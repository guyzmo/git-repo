package com.example.util;

/**
 * Simple calculator with basic operations.
 */
public class Calculator {

    public double add(double a, double b) {
        return a + b;
    }

    public double subtract(double a, double b) {
        return a - b;
    }

    public double multiply(double a, double b) {
        return a * b;
    }

    /**
     * Division — throws IllegalArgumentException if divisor is zero.
     */
    public double divide(double a, double b) {
        if (b == 0.0) {
            throw new IllegalArgumentException("Division by zero");
        }
        return a / b;
    }
}
