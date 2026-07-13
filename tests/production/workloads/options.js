import { CONFIG } from "../config/config.js";

/**
 * Default workload profile.
 */
export function buildOptions(
    vus = CONFIG.DEFAULT_VUS,
    iterations = CONFIG.DEFAULT_ITERATIONS
) {
    return {
        vus,
        iterations,

        thresholds: {
            http_req_failed: [
                "rate<0.01",
            ],

            http_req_duration: [
                "p(95)<500",
            ],
        },
    };
}