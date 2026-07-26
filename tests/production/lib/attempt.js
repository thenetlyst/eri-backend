import { CONFIG } from "../config/config.js";

import { getHeaders } from "./auth.js";

import { post } from "./http.js";

/**
 * Start assessment attempt.
 */
export function startAttempt(userNumber) {

/*    console.log("EXAM_DAY_ID =", CONFIG.EXAM_DAY_ID);*/

    const result = post(
        `${CONFIG.BASE_URL}/attempts/start`,
        {
            exam_day_id: CONFIG.EXAM_DAY_ID,
        },
        getHeaders(userNumber),
        200,
        {
            endpoint: "start_attempt",
        }
    );

    if (result.response.status !== 200) {
        console.error("========================================");
        console.error("START ATTEMPT FAILED");
        console.error("STATUS :", result.response.status);
        console.error("HEADERS:", JSON.stringify(result.response.headers));
        console.error("BODY   :", result.response.body);
        console.error("========================================");
    }

    return result.data;
}


/**
 * Initialize assessment attempt.
 */
export function initializeAttempt(userNumber) {

    const result = post(
        `${CONFIG.BASE_URL}/attempts/initialize`,
        {
            exam_day_id: CONFIG.EXAM_DAY_ID,
        },
        getHeaders(userNumber),
        200,
        {
            endpoint: "initialize_attempt",
        }
    );

    if (result.response.status !== 200) {
        console.error("========================================");
        console.error("INITIALIZE ATTEMPT FAILED");
        console.error("STATUS :", result.response.status);
        console.error("HEADERS:", JSON.stringify(result.response.headers));
        console.error("BODY   :", result.response.body);
        console.error("========================================");
    }

    return result.data;
}


/**
 * Activate assessment attempt.
 */
export function activateAttempt(userNumber) {

    const result = post(
        `${CONFIG.BASE_URL}/attempts/activate`,
        {
            exam_day_id: CONFIG.EXAM_DAY_ID,
        },
        getHeaders(userNumber),
        200,
        {
            endpoint: "activate_attempt",
        }
    );

    if (result.response.status !== 200) {
        console.error("========================================");
        console.error("ACTIVATE ATTEMPT FAILED");
        console.error("STATUS :", result.response.status);
        console.error("HEADERS:", JSON.stringify(result.response.headers));
        console.error("BODY   :", result.response.body);
        console.error("========================================");
    }

    return result.data;
}