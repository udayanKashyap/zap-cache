package com.kashyapudayan.zap_cache.controller;

import java.util.HashMap;
import java.util.Map;

import com.kashyapudayan.zap_cache.objects.CacheObject;

public class CacheWorker {
    private Map<String, CacheObject> dataMap;
    private int maxAccessFrequency;
    private String maxAccessKey;

    public CacheWorker() {
        dataMap = new HashMap<>();
    }

    public String get(String key) {
        if (key.equals("") || key == null) {
            return null;
        }
        CacheObject cacheObject = dataMap.get(key);
        if (cacheObject == null) {
            return null;
        }
        if (cacheObject.isExpired()) {
            dataMap.remove(key);
            return null;
        } else {
            String value = cacheObject.getValue();
            cacheObject.incrementFreq();
            if (cacheObject.getAccessFrequency() > maxAccessFrequency) {
                maxAccessFrequency = cacheObject.getAccessFrequency();
                maxAccessKey = key;
            }
            return value;
        }

    }

    public boolean put(String key, String value, int ttl) {
        if (value == null) {
            return false;
        }

        CacheObject oldObj = dataMap.get(key);
        long currentTimestamp = System.currentTimeMillis();
        long expiryTimestamp = currentTimestamp + (1000 * ttl);
        if (oldObj == null) {
            // insert fresh cacheObject
            CacheObject newObj = new CacheObject(value, expiryTimestamp, 0);
            dataMap.put(key, newObj);
            return true;
        }
        String oldValue = oldObj.getValue();
        if (oldValue == value) {
            return false;
        }
        if (oldValue != null) {
            // update old cacheObject
            oldObj.setValue(value);
            oldObj.setExpiryTimestamp(expiryTimestamp);
            oldObj.setAccessFrequency(0);
            return true;
        }
        return false;
    }

    public String delete(String key) {
        CacheObject deletedObj = dataMap.remove(key);
        if (deletedObj == null) {
            return null;
        }
        if (deletedObj.isExpired()) {
            return null;
        }
        return deletedObj.getValue();

    }

    public int delegate(String key) {
        return 0;
    }
}
