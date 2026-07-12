import http from "k6/http";

import { CONFIG } from "../config.js";
import { getHeaders } from "./auth.js";

export function submitAnswer(
    userNumber,
    attemptId,
    questionId,
    selectedOption,
    hintUsed = false
) {
    const payload = JSON.stringify({
        question_id: questionId,
        selected_option: selectedOption,
        hint_used: hintUsed,
    });

    const res = http.post(
        `${CONFIG.BASE_URL}/attempts/${attemptId}/submit-answer`,
        payload,
        getHeaders(userNumber)
    );

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
                "ATTEMPT_NOT_ACTIVE",
                "TIME_EXPIRED",
                "FORBIDDEN",
            ].includes(body.detail.code));


    if (res.status === 200) {
        return {
            ok: true,
            status: res.status,
            isCorrect: body.is_correct,
            rawScore: body.raw_score,
            effectiveScore: body.effective_score,
            totalHintsUsed: body.total_hints_used,
            raw: res,
        };
    }

    const detail = body.detail || {};

    return {
        ok: false,
        status: res.status,
        reason: detail.code ?? "UNKNOWN",
        message: detail.message ?? "",
        raw: res,
    };
}