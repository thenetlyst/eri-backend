import { check } from "k6";

/**
 * Build standard request headers.
 */
export function buildHeaders(token = null) {
    const headers = {
        "Content-Type": "application/json",
    };

    if (token) {
        headers.Authorization = `Bearer ${token}`;
    }

    return headers;
}

/**
 * Development authentication token.
 */
export function buildDevToken(userNumber) {
    return `dev-user-${userNumber}`;
}

/**
 * Standard response validation.
 */
export function expectStatus(response, expectedStatus) {

    const ok = check(response, {
        [`status is ${expectedStatus}`]: (r) =>
            r.status === expectedStatus,
    });

    if (!ok) {
        console.error("========================================");
        console.error("UNEXPECTED HTTP RESPONSE");
        console.error("URL            :", response.request.url);
        console.error("Method         :", response.request.method);
        console.error("Expected Status:", expectedStatus);
        console.error("Actual Status  :", response.status);
        console.error("Response Body  :");
        console.error(response.body);
        console.error("========================================");
    }

    return ok;
}

/**
 * Parse JSON safely.
 */
export function parseJson(response) {
    try {
        return response.json();
    } catch {
        return null;
    }
}

/**
 * Random integer.
 */
export function randomInt(min, max) {
    return Math.floor(
        Math.random() * (max - min + 1)
    ) + min;
}

/**
 * Random answer option.
 *
 * Used by production qualification scenarios
 * to simulate realistic participant behaviour.
 */
export function randomOption() {

    const options = [
        "A",
        "B",
        "C",
        "D",
    ];

    return options[
        randomInt(0, options.length - 1)
    ];

}