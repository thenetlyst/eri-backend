export function buildSimulationOptions() {

    return {

        scenarios: {

            national_start_burst: {

                executor: "ramping-arrival-rate",

                tags: {
                    scenario: "national_start_burst",
                },

                startRate: 50,

                timeUnit: "1s",

                preAllocatedVUs: 1000,

                maxVUs: 5000,

                stages: [

                    {
                        target: 50,
                        duration: "20s",
                    },

                    {
                        target: 100,
                        duration: "20s",
                    },

                    {
                        target: 150,
                        duration: "20s",
                    },

                    {
                        target: 210,
                        duration: "60s",
                    },

                    {
                        target: 100,
                        duration: "60s",
                    },

                    {
                        target: 20,
                        duration: "60s",
                    },

                    {
                        target: 0,
                        duration: "10s",
                    }

                ],

                gracefulStop: "30s",

            }

        },

        thresholds: {

            http_req_failed: [
                "rate<0.01"
            ],

            http_req_duration: [
                "p(95)<3000"
            ],

            checks: [
                "rate>0.99"
            ],

 /*           "http_req_duration{scenario:national_start_burst}": [
                "p(95)<3000"
            ]*/

        }

    };

}