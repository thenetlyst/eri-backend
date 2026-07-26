import { activateAttempt } from "../lib/attempt.js";
import { getUserNumber } from "../lib/auth.js";

export const options = {
    scenarios: {
        activate: {
            executor: "constant-arrival-rate",

            rate: Number(__ENV.RATE || 50),

            timeUnit: "1s",

            duration: __ENV.DURATION || "2m",

            preAllocatedVUs: 500,

            maxVUs: 5000,
        },
    },

    thresholds: {
        http_req_failed: [
            "rate<0.01",
        ],

        activate_attempt_latency: [
            "p(95)<1000",
        ],
    },
};

export default function () {

    const userNumber = getUserNumber();

    activateAttempt(userNumber);

}