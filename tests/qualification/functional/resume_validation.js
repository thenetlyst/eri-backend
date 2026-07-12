import { check, fail } from "k6";

import { startAttempt } from "../lib/attempt.js";
import { resumeAttempt } from "../lib/resume.js";
import { submitAnswer } from "../lib/answer.js";

export const options = {
    vus: 1,
    iterations: 1,
};

const USER = Number(__ENV.USER);

export default function () {

    // -----------------------------
    // Start
    // -----------------------------

    const attempt = startAttempt(USER);

    check(attempt, {
        "Attempt created": (a) => a.ok,
    });

    if (!attempt.ok) {
        console.log(JSON.stringify(attempt, null, 2));
        fail("Unable to create attempt");
    }

    // -----------------------------
    // First Resume
    // -----------------------------

    const resume1 = resumeAttempt(
        USER,
        attempt.attemptId
    );

    check(resume1, {
        "Resume #1 succeeded": (r) => r.status === 200,
    });

    const remaining1 = resume1.body.remaining_time_seconds;
    const questionOrder1 = resume1.body.question_order;

    if (!questionOrder1.length) {
        fail("No questions returned");
    }

    // -----------------------------
    // Answer first question
    // -----------------------------

    const answer = submitAnswer(
        USER,
        attempt.attemptId,
        questionOrder1[0],
        "A",
        false
    );

    check(answer, {
        "Answer accepted": (a) => a.ok,
    });

    // -----------------------------
    // Second Resume
    // -----------------------------

    const resume2 = resumeAttempt(
        USER,
        attempt.attemptId
    );

    check(resume2, {
        "Resume #2 succeeded": (r) => r.status === 200,
    });

    const remaining2 = resume2.body.remaining_time_seconds;
    const questionOrder2 = resume2.body.question_order;
    const progress = resume2.body.progress;

    // -----------------------------
    // Validation
    // -----------------------------

    check(resume2, {

        "Same attempt": () =>
            resume2.body.attempt_id === attempt.attemptId,

        "Timer decreases": () =>
            remaining2 <= remaining1,

        "One answer saved": () =>
            progress.length === 1,

        "Question order unchanged": () =>
            JSON.stringify(questionOrder1) === JSON.stringify(questionOrder2),

    });

    console.log("======================================");
    console.log("RESUME VALIDATION PASSED");
    console.log("Attempt:", attempt.attemptId);
    console.log("======================================");
}