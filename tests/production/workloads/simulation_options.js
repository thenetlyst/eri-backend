export function buildSimulationOptions() {

    return {

        scenarios: {

            national_start_burst: {

                executor: "ramping-arrival-rate",

                tags: {
                    scenario: "national_start_burst",
                },

                startRate: 25,

                timeUnit: "1s",

                preAllocatedVUs: 1000,

                maxVUs: 5000,

                stages: [

                    {
                        target: 100,
                        duration: "20s",
                    },

                    {
                        target: 125,
                        duration: "20s",
                    },

                    {
                        target: 200,
                        duration: "30s",
                    },

                    {
                        target: 200,
                        duration: "30s",
                    },

                    {
                        target: 200,
                        duration: "30s",
                    },

                    {
                        target: 150,
                        duration: "60s",
                    },

                    {
                        target: 125,
                        duration: "60s",
                    },

                    {
                        target: 75,
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