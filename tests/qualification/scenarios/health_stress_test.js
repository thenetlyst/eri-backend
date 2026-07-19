import http from "k6/http";
import { check } from "k6";

export const options = {
    vus: __ENV.VUS ? Number(__ENV.VUS) : 500,
    iterations: __ENV.ITERATIONS ? Number(__ENV.ITERATIONS) : 500,

    thresholds: {
        http_req_failed: ["rate<0.01"],
        http_req_duration: ["p(95)<100"],
    },
};

const BASE_URL = __ENV.BASE_URL || "http://localhost";

export default function () {

    const res = http.get(`${BASE_URL}/health`);

    check(res, {
        "status 200": (r) => r.status === 200,
    });
}