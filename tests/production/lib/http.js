import http from "k6/http";

import { CONFIG } from "../config/config.js";
import { expectStatus, parseJson } from "./helpers.js";
import { Trend } from "k6/metrics";

const endpointLatency = new Trend("endpoint_latency");
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

    endpointLatency.add(response.timings.duration, tags);

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

    endpointLatency.add(response.timings.duration, tags);

    return {
        response,
        data: parseJson(response),
    };
}