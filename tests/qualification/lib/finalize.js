import http from "k6/http";

import { CONFIG } from "../config.js";
import { getHeaders } from "./auth.js";

export function finalizeAttempt(userNumber, attemptId) {

    const res = http.post(
        `${CONFIG.BASE_URL}/attempts/${attemptId}/finalize`,
        null,
        getHeaders(userNumber)
    );

    let body = {};

    try {
        body = JSON.parse(res.body);
    } catch (_) {
        body = {};
    }

    if (res.status === 200) {
        return {
            ok: true,
            status: res.status,
            body,
            raw: res,
        };
    }

    const detail = body.detail || {};

    return {
        ok: false,
        status: res.status,
        reason: detail.code ?? "UNKNOWN",
        message: detail.message ?? "",
        body,
        raw: res,
    };
}