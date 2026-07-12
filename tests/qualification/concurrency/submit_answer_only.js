import { check } from "k6";
import { SharedArray } from "k6/data";

import { submitAnswer } from "../lib/answer.js";

const attemptData = new SharedArray("attempts", function () {
    return JSON.parse(open("../data/attempts.json"));
});

export const options = {
    scenarios: {
        submit_answers: {
            executor: "shared-iterations",
            vus: Number(__ENV.VUS || 100),
            iterations: Number(__ENV.VUS || 100),
            maxDuration: "2m",
        },
    },

    thresholds: {
        http_req_failed: ["rate==0"],
        http_req_duration: ["p(95)<500"],
    },
};

export default function () {

    const idx = (__VU - 1) % attemptData.length;

    const attempt = attemptData[idx];

    const response = submitAnswer(
        attempt.user,
        attempt.attempt_id,
        attempt.question_id,
        "A",
        false
    );

    check(response, {
        "Answer accepted": (r) => r.ok,
    });

    if (!response.ok) {
        console.log(JSON.stringify(response, null, 2));
    }
}