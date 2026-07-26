export function buildCapacityOptions() {
    return {
        scenarios: {
            capacity: {
                executor: "constant-arrival-rate",

                rate: Number(__ENV.RATE || 25),
                timeUnit: "1s",

                duration: __ENV.DURATION || "2m",

                preAllocatedVUs: Number(__ENV.PRE_ALLOCATED_VUS || 100),
                maxVUs: Number(__ENV.MAX_VUS || 500),

            },
        },

        thresholds: {
            http_req_failed: ["rate<0.001"],
            http_req_duration: ["p(95)<1000"],
        },
    };
}