import { CONFIG } from "../config/config.js";

import { get } from "./http.js";
import { getHeaders } from "./auth.js";

/**
 * Reconstruct an assessment attempt.
 */
export function reconstructAttempt(
    userNumber,
    attemptId
) {

    return get(

        `${CONFIG.BASE_URL}/attempts/${attemptId}/reconstruct`,

        getHeaders(userNumber),

        200,

        {
            endpoint: "reconstruct",
        }

    ).data;

}