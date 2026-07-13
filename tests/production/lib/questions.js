import { CONFIG } from "../config/config.js";

import { get } from "./http.js";
import { getHeaders } from "./auth.js";

/**
 * Returns the question manifest for an attempt.
 */
export function listQuestions(userNumber, attemptId) {
    return get(
        `${CONFIG.BASE_URL}/questions/${attemptId}/questions`,
        getHeaders(userNumber),
        200,
        {
            endpoint: "list_questions",
        }
    ).data;
}

/**
 * Returns a single question.
 */
export function getQuestion(
    userNumber,
    attemptId,
    questionOrder
) {
    return get(
        `${CONFIG.BASE_URL}/questions/${attemptId}/questions/${questionOrder}`,
        getHeaders(userNumber),
        200,
        {
            endpoint: "get_question",
        }
    ).data;
}