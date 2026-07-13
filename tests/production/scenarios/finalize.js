import { check } from "k6";

import { validateConfig } from "../config/config.js";
import { buildOptions } from "../workloads/options.js";

import { getUserNumber } from "../lib/auth.js";

import { startAttempt } from "../lib/attempt.js";
import { finalizeAttempt } from "../lib/finalize.js";

export const options = buildOptions();

export function setup() {
    validateConfig();
}

export default function () {

    const userNumber = getUserNumber();

    const attempt = startAttempt(userNumber);

    const result = finalizeAttempt(
        userNumber,
        attempt.attempt_id
    );

    check(result, {

        "attempt finalized":
            (r) => r !== null,

    });

}