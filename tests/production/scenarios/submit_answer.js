import { check } from "k6";

import { validateConfig } from "../config/config.js";
import { buildOptions } from "../workloads/options.js";

import { getUserNumber } from "../lib/auth.js";
import { startAttempt } from "../lib/attempt.js";
import { getQuestion } from "../lib/questions.js";
import { submitAnswer } from "../lib/answer.js";

export const options = buildOptions();

export function setup() {
    validateConfig();
}

export default function () {

    const userNumber = getUserNumber();

    const attempt = startAttempt(userNumber);

    const question = getQuestion(
        userNumber,
        attempt.attempt_id,
        1
    );

    const result = submitAnswer(
        userNumber,
        attempt.attempt_id,
        question.question_id,
        "A",
        false
    );

    check(result, {

        "answer submitted":
            (r) => r !== null,

        "submission successful":
            (r) => r.success === true || r.detail === undefined,

    });

}