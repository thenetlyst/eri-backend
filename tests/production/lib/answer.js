import { CONFIG } from "../config/config.js";

import { post } from "./http.js";
import { getHeaders } from "./auth.js";

/**
 * Submit an answer.
 */
export function submitAnswer(
    userNumber,
    attemptId,
    questionId,
    selectedOption,
    hintUsed = false
) {

    return post(

        `${CONFIG.BASE_URL}/attempts/${attemptId}/submit-answer-v2`,

        {
            question_id: questionId,
            selected_option: selectedOption,
            hint_used: hintUsed,
        },

        getHeaders(userNumber),

        200,

        {
            endpoint: "submit_answer",
        }

    );

}