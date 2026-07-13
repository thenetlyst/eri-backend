import http from "k6/http";

import { CONFIG } from "../config/config.js";
import { expectStatus, parseJson } from "./helpers.js";
import { Trend } from "k6/metrics";

const endpointTrends = {
    start_attempt: new Trend("start_attempt_latency"),
    list_questions: new Trend("list_questions_latency"),
    get_question: new Trend("get_question_latency"),
    submit_answer: new Trend("submit_answer_latency"),
    reconstruct: new Trend("reconstruct_latency"),
    finalize: new Trend("finalize_latency"),
};
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



    expectStatus(response, expectedStatus);

    const trend = endpointTrends[tags.endpoint];

    if (trend) {
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



    expectStatus(response, expectedStatus);

    const trend = endpointTrends[tags.endpoint];

    if (trend) {
        trend.add(response.timings.duration);
    }

    return {
        response,
        data: parseJson(response),
    };
}