import { sleep } from "k6";

import { createParticipant } from "../lib/participant.js";
import { runAssessment } from "../lib/workflow.js";

import { getUserNumber } from "../lib/auth.js";
import { validateConfig } from "../config/config.js";

export function setup() {
    validateConfig();
}

//
// -----------------------------------------------------------------------------
// Environment
// -----------------------------------------------------------------------------

const START_JITTER_SECONDS =
    Number(__ENV.START_JITTER_SECONDS || 5);

const MODE =
    __ENV.MODE || "finalize";

//
// Production traffic profile
//

const WARMUP_RATE =
    Number(__ENV.WARMUP_RATE || 8);

const RAMP_RATE =
    Number(__ENV.RAMP_RATE || 14);

const PEAK_RATE =
    Number(__ENV.PEAK_RATE || 18);

const TAPER_RATE =
    Number(__ENV.TAPER_RATE || 14);

const FINAL_RATE =
    Number(__ENV.FINAL_RATE || 8);

//
// Virtual User Pool
//

const PRE_ALLOCATED_VUS =
    Number(__ENV.PRE_ALLOCATED_VUS || 1000);

const MAX_VUS =
    Number(__ENV.MAX_VUS || 30000);

//
// -----------------------------------------------------------------------------
// k6 Options
// -----------------------------------------------------------------------------

export const options = {

    scenarios: {

        national_exam: {

            executor: "ramping-arrival-rate",

            //
            // Initial arrival rate.
            //

            startRate:
                Number(__ENV.START_RATE || 5),

            timeUnit: "1s",

            //
            // VU pool
            //

            preAllocatedVUs:
                PRE_ALLOCATED_VUS,

            maxVUs:
                MAX_VUS,

            gracefulStop: "25m",

            //
            // National event arrival curve
            //

            stages: [

                //
                // Early arrivals
                //

                {
                    duration: "5m",
                    target: WARMUP_RATE,
                },

                //
                // Main ramp
                //

                {
                    duration: "5m",
                    target: PEAK_RATE,
                },

                //
                // National peak
                //

                {
                    duration: "5m",
                    target: PEAK_RATE,
                },

                //
                // Late arrivals
                //

//                {
//                   duration: "5m",
//                   target: TAPER_RATE,
//                },

                //
                // Final participants
                //

//                {
//                    duration: "5m",
//                    target: FINAL_RATE,
//                },

                //
                // End event
                //

                {
                    duration: "1s",
                    target: 0,
                },

            ],

        },

    },

    thresholds: {

        http_req_failed: [
            "rate<0.01",
        ],

        checks: [
            "rate>0.99",
        ],

        assessment_success: [
            "rate>0.99",
        ],

    },

};

//
// -----------------------------------------------------------------------------
// Assessment Simulation
// -----------------------------------------------------------------------------

export default function () {

    //
    // Small amount of randomness so participants
    // don't all click Start simultaneously.
    //

    sleep(
        Math.random() *
        START_JITTER_SECONDS
    );

    //
    // Behaviour profile.
    //

    const participant =
        createParticipant();

    //
    // Stable participant allocation.
    //

    const userNumber =
        getUserNumber();

    //
    // Execute one complete assessment.
    //

    runAssessment({

        userNumber,

        participant,

        mode: MODE,

    });

}

//
// -----------------------------------------------------------------------------
// Teardown
// -----------------------------------------------------------------------------

export function teardown() {

    //
    // Reserved for future reporting.
    //

}