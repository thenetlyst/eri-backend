/**
 * ============================================================
 * ERI Production Qualification Framework
 * Authentication
 * ============================================================
 */

import { CONFIG } from "../config/config.js";
import { buildHeaders } from "./helpers.js";
import exec from "k6/execution";

/**
 * Returns the authentication token for a user.
 *
 * Current:
 *   Dev bypass (dev-user-X)
 *
 * Future:
 *   Firebase ID Token
 */
export function getToken(userNumber) {
    return `dev-user-${userNumber}`;
}

/**
 * Returns standard headers for a user.
 */
export function getHeaders(userNumber) {
    const token = getToken(userNumber);

    console.log("========================================");
    console.log("AUTH DEBUG");
    console.log("User Number :", userNumber);
    console.log("Token       :", token);
    console.log("========================================");

    return buildHeaders(token);
}

export function getUserNumber() {

    const userNumber =
        CONFIG.USER_START +
        (exec.scenario.iterationInTest % CONFIG.USER_COUNT);

    console.log("========================================");
    console.log("USER CALCULATION");
    console.log("CONFIG.USER_START :", CONFIG.USER_START);
    console.log("USER_COUNT        :", CONFIG.USER_COUNT);
    console.log("Iteration         :", exec.scenario.iterationInTest);
    console.log("Computed User     :", userNumber);
    console.log("========================================");

    return userNumber;
}