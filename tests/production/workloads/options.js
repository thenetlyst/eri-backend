import { CONFIG } from "../config/config.js";

export function buildOptions(
    vus = Number(__ENV.VUS || CONFIG.DEFAULT_VUS),
    iterations = Number(__ENV.ITERATIONS || CONFIG.DEFAULT_ITERATIONS)
) {
    return {
        vus,
        iterations,

        thresholds: {
            http_req_failed: ["rate<0.01"],
            http_req_duration: ["p(95)<500"],
        },
    };
}