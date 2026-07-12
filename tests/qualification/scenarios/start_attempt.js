import { startAttempt } from "../lib/attempt.js";
import { check } from "k6";

export const options = {
    vus: Number(__ENV.VUS || 50),
    iterations: Number(__ENV.ITERATIONS || 50),
};

export default function () {
    const result = startAttempt(__VU);

    check(result, {
        "Attempt created": (r) =>
            r.ok || r.reason === "ATTEMPT_ALREADY_EXISTS",
    });
}