import http from "k6/http";

import { CONFIG } from "../config/config.js";
import { expectStatus, parseJson } from "./helpers.js";

/**
 * Generic GET request.
 */
export function get(url, headers, expectedStatus = 200, tags = {}) {

    const response = http.get(
        url,
        {
            headers,
            timeout: CONFIG.REQUEST_TIMEOUT,
            tags,
        }
    );

    // ===== TEMPORARY DEBUG =====
    console.log("----------------------------------------");
    console.log("GET:", url);
    console.log("Expected Status:", expectedStatus);
    console.log("Actual Status:", response.status);
    console.log("Response Body:");
    console.log(response.body);
    console.log("----------------------------------------");
    // ===========================

    expectStatus(response, expectedStatus);

    return {
        response,
        data: parseJson(response),
    };
}

/**
 * Generic POST request.
 */
export function post(
    url,
    body,
    headers,
    expectedStatus = 200,
    tags = {}
) {

    const payload =
        body === undefined ? null : JSON.stringify(body);

    const response = http.post(
        url,
        payload,
        {
            headers,
            timeout: CONFIG.REQUEST_TIMEOUT,
            tags,
        }
    );



    expectStatus(response, expectedStatus);

    return {
        response,
        data: parseJson(response),
    };
}