import { startAttempt } from "../lib/attempt.js";

export const options = {
    vus: 1,
    iterations: 1,
};

export default function () {
    const result = startAttempt(2);

    console.log(JSON.stringify(result, null, 2));
}