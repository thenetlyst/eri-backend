import { check, fail } from "k6";

import { startAttempt } from "../lib/attempt.js";
import { resumeAttempt } from "../lib/resume.js";
import { submitAnswer } from "../lib/answer.js";
import { finalizeAttempt } from "../lib/finalize.js";
import { reconstructAttempt } from "../lib/reconstruct.js";

export const options = {
    scenarios: {
        qualification: {
            executor: "shared-iterations",

            // Number of concurrent virtual users
            vus: Number(__ENV.VUS || 1),

            // Total completed exam flows
            iterations: Number(__ENV.ITERATIONS || 1),

            // Safety timeout
            maxDuration: __ENV.MAX_DURATION || "30m",
        },
    },

    thresholds: {
        http_req_failed: ["rate==0"],
        http_req_duration: ["p(95)<2000"],
    },
};

export default function () {

    // ==========================================================
    // USER SELECTION
    // ==========================================================

    let USER;

    if (__ENV.BASE_USER !== undefined) {
        USER = Number(__ENV.BASE_USER) + (__VU - 1);
    } else if (__ENV.USER !== undefined) {
        USER = Number(__ENV.USER);
    } else {
        fail("Either USER or BASE_USER must be provided.");
    }

    // ==========================================================
    // DEBUG
    // ==========================================================

    console.log("======================================");
    console.log("NEW BUILD");
    console.log(`ENV.USER=${__ENV.USER}`);
    console.log(`ENV.BASE_USER=${__ENV.BASE_USER}`);
    console.log(`__VU=${__VU}`);
    console.log(`USER=${USER}`);
    console.log("======================================");

    // ==========================================================
    // START ATTEMPT
    // ==========================================================

    const attempt = startAttempt(USER);

    check(attempt, {
        "Attempt created": (a) => a.ok,
    });

    if (!attempt.ok) {
        console.log(JSON.stringify(attempt, null, 2));
        fail("Failed to create attempt");
    }

    // ==========================================================
    // RESUME
    // ==========================================================

    const resume = resumeAttempt(
        USER,
        attempt.attemptId
    );

    check(resume, {
        "Resume succeeded": (r) => r.status === 200,
    });

    const questionIds = resume.body.question_order;

    check(questionIds, {
        "Question list returned": (q) =>
            Array.isArray(q) &&
            q.length > 0,
    });

    // ==========================================================
    // SUBMIT ANSWERS
    // ==========================================================

    for (const questionId of questionIds) {

        const answer = submitAnswer(
            USER,
            attempt.attemptId,
            questionId,
            "A",
            false
        );

        check(answer, {
            "Answer accepted": (a) => a.ok,
        });

        if (!answer.ok) {
            console.log(JSON.stringify(answer, null, 2));
            fail(`Answer submission failed for ${questionId}`);
        }
    }

    // ==========================================================
    // FINALIZE
    // ==========================================================

    const finalize = finalizeAttempt(
        USER,
        attempt.attemptId
    );

    check(finalize, {
        "Finalize succeeded": (r) => r.status === 200,
    });

    // ==========================================================
    // RECONSTRUCT
    // ==========================================================

    const snapshot = reconstructAttempt(
        USER,
        attempt.attemptId
    );

    check(snapshot, {
        "Reconstruct succeeded": (s) => s.ok,
        "Snapshot returned": (s) =>
            s.body.snapshot !== undefined,
    });

    if (!snapshot.ok) {
        console.log(JSON.stringify(snapshot, null, 2));
        fail("Reconstruct failed");
    }

    // ==========================================================
    // SUCCESS
    // ==========================================================

    console.log("======================================");
    console.log("FULL EXAM FLOW PASSED");
    console.log(`VU=${__VU}`);
    console.log(`USER=${USER}`);
    console.log(`Attempt=${attempt.attemptId}`);
    console.log(`Questions=${questionIds.length}`);
    console.log("======================================");
}