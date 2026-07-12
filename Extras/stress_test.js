import http from "k6/http";
import { check } from "k6";

export const options = {
  vus: 200,
  duration: "30s",
};

const BASE = "http://localhost:8000";
const EXAM_DAY = "dca66be8-440f-43ab-9a4f-aa9254ed73db";

export default function () {

  const userIndex = (__VU % 200) + 1;
  const email = `load${userIndex}@eri.local`;

  let login = http.post(
    `${BASE}/auth/dev-login`,
    JSON.stringify({ email: email }),
    {
      headers: {
        "Content-Type": "application/json",
        "x-dev-key": "ERI_DEV_LOGIN"
      }
    }
  );

  if (login.status !== 200) {
    return;
  }

  const token = JSON.parse(login.body).access_token;

  let start = http.post(
    `${BASE}/attempts/start`,
    JSON.stringify({ exam_day_id: EXAM_DAY }),
    {
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`
      }
    }
  );

  check(start, {
    "attempt start ok": (r) => r.status === 200 || r.status === 403 || r.status === 400
  });

}