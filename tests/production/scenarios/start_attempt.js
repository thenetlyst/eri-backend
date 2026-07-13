import { check } from "k6";

import { validateConfig } from "../config/config.js";

import { buildOptions } from "../workloads/options.js";

import {
    getUserNumber,
} from "../lib/auth.js";

import {
    startAttempt,
} from "../lib/attempt.js";

export const options = buildOptions();

export function setup() {
    validateConfig();
}

export default function () {

    const result = startAttempt(
        getUserNumber()
    );

    check(result, {

        "attempt created":
            (r) => r !== null,

        "attempt id exists":
            (r) => !!r.attempt_id,

        "duration exists":
            (r) =>
                r.allowed_duration_seconds > 0,

    });

}