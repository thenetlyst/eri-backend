import { check } from "k6";

import { validateConfig } from "../config/config.js";

import { buildOptions } from "../workloads/options.js";

import { getUserNumber } from "../lib/auth.js";

import { startAttempt } from "../lib/attempt.js";

import { listQuestions } from "../lib/questions.js";

/**
 * ============================================================
 * ERI Production Qualification
 *
 * Scenario:
 * List Questions
 * ============================================================
 */

export const options = buildOptions();

export function setup() {
    validateConfig();
}

export default function () {

    const userNumber = getUserNumber();

    const attempt = startAttempt(userNumber);

    const questions = listQuestions(
        userNumber,
        attempt.attempt_id
    );

    check(questions, {

        "question list returned":
            (q) => q !== null,

        "question list not empty":
            (q) => Array.isArray(q),

        "questions exist":
            (q) => q.length > 0,

    });

}