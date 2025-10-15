package com.kashyapudayan.zap_cache.controller;

import java.util.Scanner;

public class ConsoleInputController implements InputController {
    private Scanner sc;
    private CacheWorker cacheWorker;

    public ConsoleInputController() {
        this.sc = new Scanner(System.in);
        this.cacheWorker = new CacheWorker();
    }

    @Override
    public void displayMenu() {
        System.out.print(MENU);
    }

    private String takeInput() {
        return sc.nextLine();

    }

    @Override
    public void handeInputs() {
        String input = takeInput();
        switch (input) {
            case "0" -> exit();
            case "1" -> get();
            case "2" -> put();
            case "3" -> delete();
        }
        ;
    }

    public void get() {
        // System.out.print("> ");
        String key = sc.nextLine();
        String value = cacheWorker.get(key);
        System.out.println(value);
    }

    public void put() {
        // System.out.print("> ");
        String[] input = sc.nextLine().split(" ");
        String key = input[0];
        String value = input[1];
        boolean isSuccess = cacheWorker.put(key, value, 100);
        System.out.println(isSuccess);
    }

    public void delete() {
        // System.out.print("> ");
        String key = sc.nextLine();
        String value = cacheWorker.delete(key);
        System.out.println(value);
    }

    public void exit() {
        System.gc();
        System.exit(0);
    }
}
