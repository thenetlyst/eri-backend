import { check } from "k6";

import { startAttempt } from "../lib/attempt.js";
import { resumeAttempt } from "../lib/resume.js";
import { submitAnswer } from "../lib/answer.js";

const USER_BASE = Number(__ENV.USER_BASE || 3000);

export const options = {
    scenarios: {
        concurrent_answers: {
            executor: "shared-iterations",
            vus: Number(__ENV.VUS || 10),
            iterations: Number(__ENV.VUS || 10),
            maxDuration: "2m",
        },
    },

    thresholds: {
        http_req_failed: ["rate==0"],
        http_req_duration: ["p(95)<500"],
    },
};

export default function () {

    const user = USER_BASE + (__VU - 1);

    //
    // Start attempt
    //

    const attempt = startAttempt(user);

    check(attempt, {
        "Attempt created": (a) => a.ok,
    });

    if (!attempt.ok) {
        console.log(JSON.stringify(attempt, null, 2));
        return;
    }

    //
    // Resume
    //

    const resume = resumeAttempt(
        user,
        attempt.attemptId
    );

    check(resume, {
        "Resume succeeded": (r) => r.ok,
    });

    if (!resume.ok) {
        console.log(JSON.stringify(resume, null, 2));
        return;
    }

    //
    // Obtain first question ID
    //

const questionOrder = resume.body.question_order || [];

check(questionOrder, {
    "Question list returned": (q) =>
        Array.isArray(q) && q.length > 0,
});

if (questionOrder.length === 0) {
    console.log(JSON.stringify(resume.body, null, 2));
    return;
}

const questionId = questionOrder[0];

    //
    // Submit answer
    //

    const answer = submitAnswer(
        user,
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
    }
}