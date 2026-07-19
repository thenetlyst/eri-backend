import { check, fail } from "k6";

import { validateConfig } from "../config/config.js";
import { buildSimulationOptions } from "../workloads/simulation_options.js";

import { getUserNumber } from "../lib/auth.js";
import { startAttempt } from "../lib/attempt.js";

export const options = buildSimulationOptions();

export function setup() {
    validateConfig();
}

export default function () {

    const userNumber = getUserNumber();

    //
    // Start Attempt
    //
    const attempt = startAttempt(userNumber);

    if (!check(attempt, {
        "attempt created": (r) => !!r?.attempt_id,
    })) {

        console.error("========================================");
        console.error("START ATTEMPT FAILED");
        console.error("========================================");
        console.error(JSON.stringify(attempt, null, 2));
        console.error("========================================");

        fail("Unable to start attempt.");
    }
}