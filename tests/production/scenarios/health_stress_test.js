import http from "k6/http";
import { check } from "k6";
import { Counter, Rate } from "k6/metrics";

// ====================
// Metrics
// =====================

const status200 = new Counter("status_200");
const status429 = new Counter("status_429");
const status500 = new Counter("status_500");
const status502 = new Counter("status_502");
const status503 = new Counter("status_503");
const status504 = new Counter("status_504");
const statusOther = new Counter("status_other");

const successRate = new Rate("success_rate");

let loggedErrors = 0;

// =====================
// Test Configuration
// =====================

export const options = {
    scenarios: {
        health: {
            executor: "constant-arrival-rate",

            // Requests per second
            rate: Number(__ENV.RATE || 200),

            timeUnit: "1s",

            duration: __ENV.DURATION || "10m",

            // Initial VU pool
            preAllocatedVUs: Number(__ENV.PRE_VUS || 500),

            // k6 can increase VUs if responses slow down
            maxVUs: Number(__ENV.MAX_VUS || 25000),
        },
    },

    thresholds: {
        http_req_failed: ["rate<0.01"],
        success_rate: ["rate>0.99"],
    },

    noConnectionReuse: false,
    userAgent: "ERI-Health-Stress-Test",
};

// =====================
// Environment Variables
// =====================

const BASE_URL = __ENV.BASE_URL || "http://localhost";
const ENDPOINT = __ENV.ENDPOINT || "/health";

// =====================
// Test
// =====================

export default function () {

    const res = http.get(`${BASE_URL}${ENDPOINT}`);

    successRate.add(res.status === 200);

    switch (res.status) {

        case 200:
            status200.add(1);
            break;

        case 429:
            status429.add(1);
            break;

        case 500:
            status500.add(1);

            if (loggedErrors < 20) {
                console.log("500 Internal Server Error");
                loggedErrors++;
            }

            break;

        case 502:
            status502.add(1);

            if (loggedErrors < 20) {
                console.log("502 Bad Gateway");
                loggedErrors++;
            }

            break;

        case 503:
            status503.add(1);

            if (loggedErrors < 20) {
                console.log(
                    `503 upstream=${res.headers["X-Upstream"] || "NONE"}`
                );
                loggedErrors++;
            }

            break;

        case 504:
            status504.add(1);

            if (loggedErrors < 20) {
                console.log("504 Gateway Timeout");
                loggedErrors++;
            }

            break;

        default:
            statusOther.add(1);

            if (loggedErrors < 20) {
                console.log(`Unexpected status: ${res.status}`);
                loggedErrors++;
            }
    }

    check(res, {
        "status == 200": (r) => r.status === 200,
    });
}