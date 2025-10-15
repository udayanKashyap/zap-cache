import random
import statistics
import subprocess
import time

JAVA_CMD = ["java", "-cp", "target/classes", "com.kashyapudayan.zap_cache.App"]
# Update classpath and main class accordingly!

OPS = {"GET": "1", "PUT": "2", "DELETE": "3"}


def send_cmd(proc, cmd):
    proc.stdin.write(cmd + "\n")
    proc.stdin.flush()


def measure_latency(proc, command, payload):
    start = time.time()
    send_cmd(proc, command)
    send_cmd(proc, payload)
    output = proc.stdout.readline().strip()
    end = time.time()
    return (end - start), output


def run_workload(proc, op_type, iterations=100):
    latencies = []

    for i in range(iterations):
        key = f"key{i}"
        val = f"val{i}"

        if op_type == "PUT":
            latency, _ = measure_latency(proc, OPS["PUT"], f"{key} {val}")
        elif op_type == "GET":
            latency, _ = measure_latency(proc, OPS["GET"], key)
        elif op_type == "DELETE":
            latency, _ = measure_latency(proc, OPS["DELETE"], key)

        latencies.append(latency)

    return latencies


def print_stats(name, latencies):
    print(f"\n--- {name} STATS ---")
    print(f"Total Ops: {len(latencies)}")
    print(f"Avg Latency: {statistics.mean(latencies) * 1000:.2f} ms")
    print(f"Min Latency: {min(latencies) * 1000:.2f} ms")
    print(f"Max Latency: {max(latencies) * 1000:.2f} ms")


def main():
    proc = subprocess.Popen(
        JAVA_CMD,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    workloads = {
        "WRITE_HEAVY_PUT": "PUT",
        "READ_HEAVY_GET": "GET",
        "DELETE_HEAVY": "DELETE",
    }

    for name, op in workloads.items():
        latencies = run_workload(proc, op, iterations=100)
        print_stats(name, latencies)

    # Exit
    send_cmd(proc, "0")
    proc.terminate()


if __name__ == "__main__":
    main()
