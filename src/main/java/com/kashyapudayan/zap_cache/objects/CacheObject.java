package com.kashyapudayan.zap_cache.objects;

public class CacheObject {
    private String value;
    private long expiryTimestamp;
    private int accessFrequency;

    public CacheObject(String value) {
        this.value = value;
        this.expiryTimestamp = System.currentTimeMillis() + 1000;
        this.accessFrequency = 0;
    }

    public CacheObject(String value, long expiryTimestamp) {
        this.value = value;
        this.expiryTimestamp = expiryTimestamp;
        this.accessFrequency = 0;
    }

    public CacheObject(String value, long expiryTimestamp, int accessFrequency) {
        this.value = value;
        this.expiryTimestamp = expiryTimestamp;
        this.accessFrequency = accessFrequency;
    }

    public String getValue() {
        return value;
    }

    public void setValue(String value) {
        this.value = value;
    }

    public long getExpiryTimestamp() {
        return expiryTimestamp;
    }

    public void setExpiryTimestamp(long expiryTimestamp) {
        this.expiryTimestamp = expiryTimestamp;
    }

    public int getAccessFrequency() {
        return accessFrequency;
    }

    public void setAccessFrequency(int accessFrequency) {
        this.accessFrequency = accessFrequency;
    }

    public void incrementFreq() {
        accessFrequency++;
    }

    public boolean isExpired() {
        long currentTimestamp = System.currentTimeMillis();
        if (currentTimestamp > expiryTimestamp) {
            return true;
        }
        return false;
    }

}
