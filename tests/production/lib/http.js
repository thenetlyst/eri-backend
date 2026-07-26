import http from "k6/http";

import { CONFIG } from "../config/config.js";
import { expectStatus, parseJson } from "./helpers.js";
import { Trend } from "k6/metrics";

const endpointTrends = {
    start_attempt: new Trend("start_attempt_latency"),
    activate_attempt: new Trend("activate_attempt_latency"),
    list_questions: new Trend("list_questions_latency"),
    get_question: new Trend("get_question_latency"),
    submit_answer: new Trend("submit_answer_latency"),
    reconstruct: new Trend("reconstruct_latency"),
    finalize: new Trend("finalize_latency"),
};

function logTimings(endpoint, response) {
    if (__ENV.DEBUG_TIMINGS !== "true") {
        return;
    }

    console.log(
        JSON.stringify(
            {
                endpoint,
                status: response.status,
                timings: {
                    blocked: response.timings.blocked,
                    connecting: response.timings.connecting,
                    tls_handshaking: response.timings.tls_handshaking,
                    sending: response.timings.sending,
                    waiting: response.timings.waiting,
                    receiving: response.timings.receiving,
                    duration: response.timings.duration,
                },
            },
            null,
            2
        )
    );
}

/**
 * Generic GET request.
 */
export function get(url, headers, expectedStatus = 200, tags = {}) {

    const response = http.get(
        url,
        {
            headers,
            timeout: CONFIG.REQUEST_TIMEOUT,
            tags,
        }
    );

    logTimings(tags.endpoint, response);

    expectStatus(response, expectedStatus);

    const trend = endpointTrends[tags.endpoint];

    // Record only successful responses.
    if (trend && response.status === expectedStatus) {
        trend.add(response.timings.duration);
    }

    return {
        response,
        data: parseJson(response),
    };
}

/**
 * Generic POST request.
 */
export function post(
    url,
    body,
    headers,
    expectedStatus = 200,
    tags = {}
) {

    const payload =
        body === undefined ? null : JSON.stringify(body);

    const response = http.post(
        url,
        payload,
        {
            headers,
            timeout: CONFIG.REQUEST_TIMEOUT,
            tags,
        }
    );

    logTimings(tags.endpoint, response);

    if (response.status === 0) {
        console.log("================================");
        console.log("NETWORK FAILURE");
        console.log("error       :", response.error);
        console.log("error_code  :", response.error_code);
        console.log("duration    :", response.timings.duration);
        console.log("================================");
    }

    if (__ENV.DEBUG_TIMINGS === "true" && response.status !== expectedStatus) {
        console.log("========================================");
        console.log("REQUEST FAILED");
        console.log("URL        :", url);
        console.log("STATUS     :", response.status);
        console.log("ERROR      :", response.error);
        console.log("ERROR CODE :", response.error_code);
        console.log("BODY       :", response.body);
        console.log("HEADERS    :", JSON.stringify(response.headers, null, 2));
        console.log("TIMINGS    :", JSON.stringify(response.timings, null, 2));
        console.log("========================================");
    }

    expectStatus(response, expectedStatus);

    const trend = endpointTrends[tags.endpoint];

    // Record only successful responses.
    if (trend && response.status === expectedStatus) {
        trend.add(response.timings.duration);
    }

    return {
        response,
        data: parseJson(response),
    };
}