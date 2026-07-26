import http from "k6/http";
import { check } from "k6";
import { Rate } from "k6/metrics";

const BASE_URL = __ENV.BASE_URL || "http://localhost";
const TOKEN = __ENV.TOKEN;
const EXAM_DAY_ID = __ENV.EXAM_DAY_ID;

export const errorRate = new Rate("errors");

export const options = {
    scenarios: {
        initialize: {
            executor: "constant-arrival-rate",
            rate: Number(__ENV.RATE || 25),
            timeUnit: "1s",
            duration: __ENV.DURATION || "2m",
            preAllocatedVUs: 100,
            maxVUs: 500,
        },
    },

    thresholds: {
        http_req_failed: ["rate<0.001"],
        http_req_duration: ["p(95)<1000"],
    },
};

export default function () {

    const res = http.post(
        `${BASE_URL}/api/v1/attempts/initialize`,
        JSON.stringify({
            exam_day_id: EXAM_DAY_ID,
        }),
        {
            headers: {
                Authorization: `Bearer ${TOKEN}`,
                "Content-Type": "application/json",
            },
        }
    );

    const ok = check(res, {
        "status 200": (r) => r.status === 200,
    });

    errorRate.add(!ok);
}