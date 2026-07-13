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

    return buildHeaders(token);
}

/**
 * Returns the current user number for this VU.
 *
 * Every Virtual User gets a unique dev account.
 */
export function getUserNumber() {
    return (
        CONFIG.USER_START +
        (exec.scenario.iterationInTest % CONFIG.USER_COUNT)
    );
}