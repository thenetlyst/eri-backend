import { check } from "k6";

import { resumeAttempt } from "../lib/resume.js";
import { submitAnswer } from "../lib/answer.js";
import { finalizeAttempt } from "../lib/finalize.js";

export const options = {
    vus: 1,
    iterations: 1,
};

const ATTEMPT = __ENV.ATTEMPT;
const QUESTION = __ENV.QUESTION;

// User B (different from the attempt owner)
const USER = Number(__ENV.USER);

export default function () {

    const resume = resumeAttempt(
        USER,
        ATTEMPT
    );

    const answer = submitAnswer(
        USER,
        ATTEMPT,
        QUESTION,
        "A",
        false
    );

    const finalize = finalizeAttempt(
        USER,
        ATTEMPT
    );

    check(resume, {
        "Resume denied": (r) => !r.ok,
    });

    check(answer, {
        "Submit denied": (r) => !r.ok,
    });

    check(finalize, {
        "Finalize denied": (r) => !r.ok,
    });

    console.log("======================================");
    console.log("UNAUTHORIZED ACCESS PASSED");
    console.log("======================================");
}