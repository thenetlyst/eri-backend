import http from "k6/http";
import { check } from "k6";
import { Counter} from "k6/metrics";

const status200 = new Counter("status_200");
const status429 = new Counter("status_429");
const status500 = new Counter("status_500");
const status502 = new Counter("status_502");
const status503 = new Counter("status_503");
const status504 = new Counter("status_504");
const statusOther = new Counter("status_other");

let logged503 = 0;

export const options = {
    vus: __ENV.VUS ? Number(__ENV.VUS) : 500,
    duration: __ENV.DURATION || "60s",

    thresholds: {
        http_req_failed: ["rate<0.01"],
        http_req_duration: ["p(95)<100"],
    },
};

const BASE_URL = __ENV.BASE_URL || "http://localhost";

export default function () {

    const res = http.get(`${BASE_URL}/health`);

    switch (res.status) {
        case 200:
            status200.add(1);
            break;

        case 429:
            status429.add(1);
            break;

        case 500:
            status500.add(1);
            break;

        case 502:
            status502.add(1);
            break;

        case 503:
            status503.add(1);

            if (logged503 < 20) {
                console.log(
                    `503 upstream=${res.headers["X-Upstream"] || "NONE"}`
                );
                logged503++;
            }

            break;

        case 504:
            status504.add(1);
            break;

        default:
            statusOther.add(1);
    }

    check(res, {
        "status 200": (r) => r.status === 200,
    });
}