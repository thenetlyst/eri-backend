import http from "k6/http";
import { Trend } from "k6/metrics";

import { CONFIG } from "../config.js";
import { getHeaders } from "./auth.js";

export const blockedTrend = new Trend("http_blocked");
export const connectingTrend = new Trend("http_connecting");
export const waitingTrend = new Trend("http_waiting");
export const sendingTrend = new Trend("http_sending");
export const receivingTrend = new Trend("http_receiving");

export const backendTimeTrend = new Trend("backend_request_time");
export const transportGapTrend = new Trend("transport_gap");

export function startAttempt(userNumber) {
    const payload = JSON.stringify({
        exam_day_id: CONFIG.EXAM_DAY_ID,
    });

    const res = http.post(
        `${CONFIG.BASE_URL}/attempts/start`,
        payload,
        getHeaders(userNumber)
    );

    blockedTrend.add(res.timings.blocked);
    connectingTrend.add(res.timings.connecting);
    waitingTrend.add(res.timings.waiting);
    sendingTrend.add(res.timings.sending);
    receivingTrend.add(res.timings.receiving);

    const backendTime = Number(res.headers["X-Request-Time"] || 0);

    backendTimeTrend.add(backendTime);

    const transportGap = Math.max(
        0,
        res.timings.waiting - backendTime
    );

    transportGapTrend.add(transportGap);

    let body = {};

    try {
        body = JSON.parse(res.body);
    } catch (_) {
        body = {};
    }

    const valid =
        res.status === 200 ||
        (res.status === 403 &&
            body.detail &&
            [
                "ALREADY_COMPLETED",
                "WINDOW_CLOSED",
                "ATTEMPT_ALREADY_EXISTS",
            ].includes(body.detail.code));


    if (res.status === 200) {
        return {
            ok: true,
            status: res.status,
            attemptId: body.attempt_id,
            allowedDuration: body.allowed_duration_seconds,
            specialUnlocked: body.special_unlocked,
            raw: res,
        };
    }

    const detail = body.detail || {};

    return {
        ok: false,
        status: res.status,
        reason: detail.code ?? "UNKNOWN",
        message: detail.message ?? "",
        attemptId: detail.meta?.attempt_id ?? null,
        raw: res,
    };
}