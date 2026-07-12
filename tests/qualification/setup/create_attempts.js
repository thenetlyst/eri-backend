import { startAttempt } from "../lib/attempt.js";

export const options = {
    scenarios: {
        setup: {
            executor: "per-vu-iterations",
            vus: Number(__ENV.VUS || 100),
            iterations: 1,
        },
    },
};

export default function () {

    // First seeded user ID
    const USER_BASE = Number(__ENV.USER_BASE || 10000);
    const user = USER_BASE + (__VU - 1);

    const result = startAttempt(user);

    if (!result.ok) {
        console.log(JSON.stringify(result));
    } else {
        console.log(`✓ Created attempt for dev-user-${user}`);
    }
}