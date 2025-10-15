package com.kashyapudayan.zap_cache;

import com.kashyapudayan.zap_cache.controller.ConsoleInputController;

public class App {
    public static void main(String[] args) {
        ConsoleInputController ic = new ConsoleInputController();
        try {
            while (true) {
                // ic.displayMenu();
                ic.handeInputs();
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
