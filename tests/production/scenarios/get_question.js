import { check } from "k6";

import { validateConfig } from "../config/config.js";

import { buildOptions } from "../workloads/options.js";

import { getUserNumber } from "../lib/auth.js";

import { startAttempt } from "../lib/attempt.js";

import {
    getQuestion
} from "../lib/questions.js";

import { fail } from "k6";

export const options = buildOptions();

export function setup() {
    validateConfig();
}

export default function () {

    const userNumber = getUserNumber();

   

    const attempt = startAttempt(userNumber);

    check(attempt, {
        "attempt created": (a) => !!a?.attempt_id,
    });

    if (!attempt?.attempt_id) {
        fail("Unable to start attempt.");
    }

    const question = getQuestion(
        userNumber,
        attempt.attempt_id,
        1
    );

    check(question, {

        "question returned":
            (q) => q !== null,

        "question id exists":
            (q) => !!q.question_id,

        "question text exists":
            (q) => !!q.question_text,

        "options exist":
            (q) => Array.isArray(q.options),

    });

}