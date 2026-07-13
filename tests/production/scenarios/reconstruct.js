import { check, fail } from "k6";

import { validateConfig } from "../config/config.js";
import { buildOptions } from "../workloads/options.js";

import { getUserNumber } from "../lib/auth.js";
import { startAttempt } from "../lib/attempt.js";
import { reconstructAttempt } from "../lib/reconstruct.js";

export const options = buildOptions();

export function setup() {
    validateConfig();
}

export default function () {

    const userNumber = getUserNumber();

    const attempt = startAttempt(userNumber);

    if (!check(attempt, {
        "attempt created": (a) => !!a?.attempt_id,
    })) {
        fail("Unable to start attempt.");
    }

    const snapshot = reconstructAttempt(
        userNumber,
        attempt.attempt_id
    );

    check(snapshot, {

        "snapshot returned":
            (r) => r !== null,

        "attempt exists":
            (r) => !!r.snapshot?.attempt,

        "questions exist":
            (r) => Array.isArray(r.snapshot?.questions),

    });

}