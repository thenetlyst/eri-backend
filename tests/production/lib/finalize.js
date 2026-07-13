import { CONFIG } from "../config/config.js";

import { post } from "./http.js";
import { getHeaders } from "./auth.js";

/**
 * Finalize an assessment attempt.
 */
export function finalizeAttempt(
    userNumber,
    attemptId
) {

    return post(

        `${CONFIG.BASE_URL}/attempts/${attemptId}/finalize`,

        {},

        getHeaders(userNumber),

        200,

        {
            endpoint: "finalize",
        }

    ).data;

}