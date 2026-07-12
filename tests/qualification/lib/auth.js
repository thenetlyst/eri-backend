import { CONFIG } from "../config.js";

export function getHeaders(userNumber) {
    return {
        headers: {
            ...CONFIG.DEFAULT_HEADERS,
            Authorization: `Bearer dev-user-${userNumber}`,
        },
    };
}