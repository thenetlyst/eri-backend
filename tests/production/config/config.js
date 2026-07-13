/**
 * ERI Production Qualification Framework
 * Configuration
 */

export const CONFIG = {
    BASE_URL: __ENV.BASE_URL || "http://localhost:8000",

    EXAM_DAY_ID: __ENV.EXAM_DAY_ID,

    USER_START: Number(__ENV.USER_START || 1),

    USER_COUNT: Number(__ENV.USER_COUNT || 100),

    DEFAULT_VUS: Number(__ENV.VUS || 1),

    DEFAULT_ITERATIONS: Number(__ENV.ITERATIONS || 1),

    REQUEST_TIMEOUT: __ENV.REQUEST_TIMEOUT || "2m",

    DEFAULT_HEADERS: {
        "Content-Type": "application/json",
    },
};

export function validateConfig() {
    if (!CONFIG.EXAM_DAY_ID) {
        throw new Error(
            "Missing EXAM_DAY_ID. Pass it using -e EXAM_DAY_ID=<uuid>"
        );
    }
}