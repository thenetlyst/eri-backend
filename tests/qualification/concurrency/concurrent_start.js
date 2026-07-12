import http from "k6/http";
import { check } from "k6";

const BASE_URL = __ENV.BASE_URL || "http://localhost:8000";
const EXAM_DAY_ID = __ENV.EXAM_DAY || "72970bd4-ce75-4b0f-b57b-e9478189e566";

export const options = {
    scenarios: {
        concurrent_start: {
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

    const USER_BASE = Number(__ENV.USER_BASE || 2000);
    const user = USER_BASE + (__VU - 1);

    const res = http.post(
        `${BASE_URL}/attempts/start`,
        JSON.stringify({
            exam_day_id: EXAM_DAY_ID,
        }),
        {
            headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer dev-user-${user}`,
            },
        }
    );

    let body = {};

    try {
        body = JSON.parse(res.body);
    } catch (_) {}

    check(res, {
        "201/200 returned": (r) => r.status === 200 || r.status === 201,
        "Attempt created": () => !!body.attempt_id,
    });

    if (res.status !== 200 && res.status !== 201) {
        console.log(JSON.stringify(body));
    }
}