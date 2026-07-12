import { check, fail } from "k6";

import { startAttempt } from "../lib/attempt.js";
import { resumeAttempt } from "../lib/resume.js";

export const options = {
    vus: 1,
    iterations: 1,
};

const USER = Number(__ENV.USER);

export default function () {

    if (!USER) {
        fail("USER environment variable not provided.");
    }

    // -----------------------------
    // Start Attempt
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
    // Resume
    // -----------------------------

    const resume = resumeAttempt(
        USER,
        attempt.attemptId
    );

    check(resume, {
        "Resume succeeded": (r) => r.status === 200,
    });

    if (resume.status !== 200) {
        fail("Unable to resume attempt");
    }

    const questionId = resume.body.question_order[0];

    console.log("======================================");
    console.log("ATTEMPT_ID=" + attempt.attemptId);
    console.log("QUESTION_ID=" + questionId);
    console.log("======================================");
}