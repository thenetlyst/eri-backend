import { check, fail } from "k6";

import { validateConfig } from "../config/config.js";
import { buildOptions } from "../workloads/options.js";

import { getUserNumber } from "../lib/auth.js";

import { startAttempt } from "../lib/attempt.js";
import { listQuestions, getQuestion } from "../lib/questions.js";
import { submitAnswer } from "../lib/answer.js";
import { reconstructAttempt } from "../lib/reconstruct.js";
import { finalizeAttempt } from "../lib/finalize.js";
import { randomOption } from "../lib/helpers.js";

export const options = buildOptions();

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
        fail("Unable to start attempt.");
    }

    //
    // Question Manifest
    //
    const manifest = listQuestions(
        userNumber,
        attempt.attempt_id
    );

    if (!check(manifest, {
        "manifest returned": (r) => Array.isArray(r),
        "manifest not empty": (r) => r.length > 0,
    })) {
        fail("Question manifest invalid.");
    }

    //
    // Walk Every Available Question
    //
    for (const item of manifest) {

        // Skip locked bonus questions
        if (item.bonus_locked) {
            continue;
        }

        const question = getQuestion(
            userNumber,
            attempt.attempt_id,
            item.question_order
        );

        if (!check(question, {
            "question returned": (q) => !!q?.question_id,
            "options returned": (q) => Array.isArray(q.options),
        })) {
            fail(`Question ${item.question_order} retrieval failed.`);
        }

        const answer = submitAnswer(
            userNumber,
            attempt.attempt_id,
            question.question_id,
            randomOption(),
            false
        );

        check(answer, {
            "answer stored": (a) => a !== null,
        });
    }

    //
    // Reconstruct
    //
    const snapshot = reconstructAttempt(
        userNumber,
        attempt.attempt_id
    );

    if (!check(snapshot, {
        "snapshot returned": (r) => r !== null,
        "attempt exists": (r) => !!r.snapshot?.attempt,
        "questions restored": (r) => Array.isArray(r.snapshot?.questions),
    })) {
        fail("Reconstruct failed.");
    }

    //
    // Finalize
    //
    const finalized = finalizeAttempt(
        userNumber,
        attempt.attempt_id
    );

    check(finalized, {
        "attempt finalized": (r) => r !== null,
    });

}