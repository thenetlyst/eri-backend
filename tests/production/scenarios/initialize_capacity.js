import { check } from "k6";

import { validateConfig } from "../config/config.js";
import { buildCapacityOptions } from "../workloads/capacity_options.js";

import { getUserNumber } from "../lib/auth.js";
import { initializeAttempt } from "../lib/attempt.js";

export const options = buildCapacityOptions();

export function setup() {
    validateConfig();
}

export default function () {

    const result = initializeAttempt(getUserNumber());

    check(result, {
        "attempt created": (r) => r != null,
        "attempt id exists": (r) => r != null && !!r.attempt_id,
        "duration exists": (r) =>
            r != null && r.allowed_duration_seconds > 0,
    });

}