import { check, fail } from "k6";
import { submitAnswer } from "../lib/answer.js";

export const options = {
    vus: 1,
    iterations: 1,
};

const USER = Number(__ENV.USER);
const ATTEMPT = __ENV.ATTEMPT;
const QUESTION = __ENV.QUESTION;

export default function () {

    const result = submitAnswer(
        USER,
        ATTEMPT,
        QUESTION,
        "A",
        false
    );

    console.log(JSON.stringify(result, null, 2));
    
    check(result, {
        "HTTP 403": (r) => r.status === 403,
        "Attempt expired": (r) => r.reason === "ATTEMPT_EXPIRED",
        "Answer rejected": (r) => !r.ok,
    });

    if (result.ok) {
        fail("Expired attempt accepted an answer.");
    }

    console.log("======================================");
    console.log("TIMER EXPIRY PASSED");
    console.log("======================================");
}