import { CONFIG } from "../config/config.js";

import { getHeaders } from "./auth.js";

import { post } from "./http.js";

/**
 * Start assessment attempt.
 */
export function startAttempt(userNumber) {

    return post(

        `${CONFIG.BASE_URL}/attempts/start`,

        {
            exam_day_id: CONFIG.EXAM_DAY_ID,
        },

        getHeaders(userNumber),

        200,

        {
            endpoint: "start_attempt",
        }

    ).data;
}