import { check, fail } from "k6";

import { startAttempt } from "../lib/attempt.js";
import { resumeAttempt } from "../lib/resume.js";
import { submitAnswer } from "../lib/answer.js";

export const options = {
    scenarios: {
        answer_race: {
            executor: "per-vu-iterations",
            vus: 100,
            iterations: 1,
            maxDuration: "2m",
        },
    },

    thresholds: {
        http_req_failed: ["rate==0"],
        http_req_duration: ["p(95)<1000"],
    },
};

export default function () {

    const user = __VU;

    // -----------------------------------
    // Start attempt
    // -----------------------------------

    const attempt = startAttempt(user);

    if (!attempt.ok) {
        console.log(JSON.stringify(attempt));
        fail("Unable to create attempt");
    }

    // -----------------------------------
    // Resume
    // -----------------------------------

    const resume = resumeAttempt(
        user,
        attempt.attemptId
    );

    const questions = resume.body.question_order;

    if (!questions || questions.length === 0) {
        fail("No questions returned");
    }

    // -----------------------------------
    // Submit FIRST question only
    // -----------------------------------

    const result = submitAnswer(
        user,
        attempt.attemptId,
        questions[0],
        "A",
        false
    );

    check(result, {
        "Answer accepted": (r) => r.ok,
    });

    if (!result.ok) {
        console.log(JSON.stringify(result));
        fail("Answer rejected");
    }

}