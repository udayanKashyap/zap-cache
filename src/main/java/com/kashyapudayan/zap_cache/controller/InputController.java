package com.kashyapudayan.zap_cache.controller;

public interface InputController {
    public static final String MENU = """
            0 - Exit
            1 - Get Data
            2 - Put Data
            3 - Delete Data
            """;

    void displayMenu();

    void handeInputs();
}
