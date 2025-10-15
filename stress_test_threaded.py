import threading
import queue
import subprocess
import time
import random
import statistics
import sys
from dataclasses import dataclass, field

# =========================
# Config
# =========================
JAVA_CMD = [
    "java",
    "-cp",
    "target/classes",
    "com.kashyapudayan.zap_cache.App",
]  # update if needed

TOTAL_OPS = 100000  # <-- default total operations
THREADS = 8  # number of worker threads generating ops
PUT_PCT = 30  # % of ops
GET_PCT = 60  # % of ops
DEL_PCT = 10  # % of ops
ASSERT_MIX_SUM = True  # sanity check of mix
KEY_SPACE = 2_000  # reuse keys to create realistic cache hits

# Safety: stdout read timeout (seconds)
READ_TIMEOUT = 5.0

OPS = {"GET": "1", "PUT": "2", "DELETE": "3"}

# =========================
# Internals
# =========================


@dataclass
class OpRequest:
    op: str  # "GET" | "PUT" | "DELETE"
    key: str
    value: str | None
    start_ts: float = field(default=0.0)
    end_ts: float = field(default=0.0)
    response: str | None = field(default=None)
    done: threading.Event = field(default_factory=threading.Event)

    @property
    def latency(self) -> float:
        return self.end_ts - self.start_ts if self.end_ts and self.start_ts else 0.0


class ConsoleClient:
    """
    Single-process console client with serialized I/O, safe for multiple producer threads.
    """

    def __init__(self, java_cmd):
        self.proc = subprocess.Popen(
            java_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,  # line-buffered
        )
        if not self.proc.stdin or not self.proc.stdout:
            raise RuntimeError("Failed to open stdin/stdout for Java process")
        self.io_lock = threading.Lock()

    def send_and_read_one_line(self, command: str, payload: str) -> str:
        """
        Sends (command, payload) as two lines, reads ONE line back as the 'result'.
        NOTE: Your Java console likely prints extra lines (menu, prompts).
        We deliberately read a single line after payload to measure latency consistently.
        """
        with self.io_lock:
            # Write command
            self.proc.stdin.write(command + "\n")
            self.proc.stdin.flush()

            # Write payload
            self.proc.stdin.write(payload + "\n")
            self.proc.stdin.flush()

            # Read one line as the 'result' for this op.
            # Use a timed read loop to avoid deadlock if nothing arrives.
            start_wait = time.time()
            while True:
                if (time.time() - start_wait) > READ_TIMEOUT:
                    return "<timeout>"
                line = self.proc.stdout.readline()
                if not line:
                    # Process may have exited or no output yet
                    time.sleep(0.001)
                    continue
                line = line.rstrip("\n")
                if line == "":
                    # skip empty
                    continue
                return line

    def exit(self):
        try:
            with self.io_lock:
                self.proc.stdin.write("0\n")
                self.proc.stdin.flush()
        except Exception:
            pass
        try:
            self.proc.terminate()
        except Exception:
            pass


def make_payload(op: str):
    key = f"key{random.randint(0, KEY_SPACE - 1)}"
    if op == "PUT":
        val = f"val{random.randint(0, KEY_SPACE - 1)}"
        return key, val
    return key, None


def op_sampler():
    r = random.random() * 100
    if r < PUT_PCT:
        return "PUT"
    elif r < PUT_PCT + GET_PCT:
        return "GET"
    else:
        return "DELETE"


def worker_thread(
    name: str,
    client: ConsoleClient,
    task_q: queue.Queue,
    results: dict[str, list[float]],
    in_flight: threading.Semaphore,
):
    while True:
        try:
            req: OpRequest = task_q.get(timeout=1.0)
        except queue.Empty:
            return
        try:
            req.start_ts = time.time()
            if req.op == "PUT":
                resp = client.send_and_read_one_line(
                    OPS["PUT"], f"{req.key} {req.value}"
                )
            elif req.op == "GET":
                resp = client.send_and_read_one_line(OPS["GET"], req.key)
            else:
                resp = client.send_and_read_one_line(OPS["DELETE"], req.key)
            req.end_ts = time.time()
            req.response = resp
            results[req.op].append(req.latency)
        finally:
            req.done.set()
            task_q.task_done()
            in_flight.release()


def main():
    if ASSERT_MIX_SUM:
        assert PUT_PCT + GET_PCT + DEL_PCT == 100, (
            "PUT_PCT + GET_PCT + DEL_PCT must equal 100"
        )

    print(f"Launching Java process: {' '.join(JAVA_CMD)}")
    client = ConsoleClient(JAVA_CMD)

    task_q: queue.Queue[OpRequest] = queue.Queue(maxsize=THREADS * 4)
    results = {"PUT": [], "GET": [], "DELETE": []}
    in_flight = threading.Semaphore(THREADS)  # limit concurrent 'scheduled' ops

    # Spawn worker threads
    threads = []
    for i in range(THREADS):
        t = threading.Thread(
            target=worker_thread,
            args=(f"worker-{i}", client, task_q, results, in_flight),
            daemon=True,
        )
        t.start()
        threads.append(t)

    # Enqueue TOTAL_OPS
    start_all = time.time()
    for _ in range(TOTAL_OPS):
        in_flight.acquire()  # keep pressure at THREADS
        op = op_sampler()
        key, val = make_payload(op)
        req = OpRequest(op=op, key=key, value=val)
        task_q.put(req)

    # Wait for drain
    task_q.join()
    total_time = time.time() - start_all

    # Stop workers
    for t in threads:
        t.join(timeout=0.1)

    # Ask Java to exit
    client.exit()

    # Print stats
    def stats_for(name, arr):
        if not arr:
            print(f"{name}: no ops")
            return
        print(
            f"{name}: count={len(arr)}, avg={statistics.mean(arr) * 1000:.2f} ms, "
            f"p50={statistics.median(arr) * 1000:.2f} ms, "
            f"min={min(arr) * 1000:.2f} ms, max={max(arr) * 1000:.2f} ms"
        )

    print("\n=== RESULTS ===")
    print(
        f"TOTAL_OPS: {TOTAL_OPS}, THREADS: {THREADS}, MIX: PUT {PUT_PCT}% / GET {GET_PCT}% / DELETE {DEL_PCT}%"
    )
    print(
        f"Wall time: {total_time:.3f}s, Throughput: {TOTAL_OPS / total_time:.1f} ops/s"
    )

    stats_for("PUT", results["PUT"])
    stats_for("GET", results["GET"])
    stats_for("DELETE", results["DELETE"])

    # Optional: stderr dump if needed for debugging
    try:
        err = client.proc.stderr.read()
        if err and err.strip():
            print("\n--- STDERR (Java) ---")
            print(err.strip())
    except Exception:
        pass


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        sys.exit(130)
