import { check, fail } from "k6";
import { startAttempt } from "../lib/attempt.js";
import { resumeAttempt } from "../lib/resume.js";
import { submitAnswer } from "../lib/answer.js";

export const options = {
    scenarios: {
        answer_race: {
            executor: "per-vu-iterations",
            vus: 50,
            iterations: 1,
            maxDuration: "2m",
        },
    },

    thresholds: {
        http_req_failed: ["rate==0"],
        http_req_duration: ["p(95)<1000"],
    },
};

const USER = Number(__ENV.USER);

export default function () {

    // VU 1 creates the attempt.
    if (__VU === 1) {

        const attempt = startAttempt(USER);

        check(attempt, {
            "Attempt created": (a) => a.ok,
        });

        if (!attempt.ok) {
            fail("Unable to create attempt");
        }

        globalThis.attemptId = attempt.attemptId;

        const resume = resumeAttempt(
            USER,
            attempt.attemptId
        );

        globalThis.questionId =
            resume.body.question_order[0];
    }

    // Wait until attempt exists.
    while (!globalThis.attemptId) {
        sleep(0.1);
    }

    const options = ["A", "B", "C", "D"];

    const result = submitAnswer(
        USER,
        globalThis.attemptId,
        globalThis.questionId,
        options[(__VU - 1) % 4],
        false
    );

    check(result, {
        "Answer accepted": (r) => r.ok,
    });
}