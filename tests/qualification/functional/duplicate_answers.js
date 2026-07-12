import { check } from "k6";

import { submitAnswer } from "../lib/answer.js";

export const options = {
    vus: 1,
    iterations: 1,
};

const USER = Number(__ENV.USER);
const ATTEMPT = __ENV.ATTEMPT;
const QUESTION = __ENV.QUESTION;

export default function () {

    const r1 = submitAnswer(
        USER,
        ATTEMPT,
        QUESTION,
        "A",
        false
    );

    const r2 = submitAnswer(
        USER,
        ATTEMPT,
        QUESTION,
        "C",
        false
    );

    const r3 = submitAnswer(
        USER,
        ATTEMPT,
        QUESTION,
        "B",
        false
    );

    check(r1, {
        "First accepted": (r) => r.ok,
    });

    check(r2, {
        "Second accepted": (r) => r.ok,
    });

    check(r3, {
        "Third accepted": (r) => r.ok,
    });

    console.log("======================================");
    console.log("DUPLICATE ANSWERS PASSED");
    console.log("======================================");
}