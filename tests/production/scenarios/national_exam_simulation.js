import { sleep } from "k6";

import { createParticipant } from "../lib/participant.js";
import { runAssessment } from "../lib/workflow.js";

import { getUserNumber } from "../lib/auth.js";
import { validateConfig } from "../config/config.js";
//import { EVENT } from "../config/event_config.js";

export function setup() {
    validateConfig();
}

//
// -----------------------------------------------------------------------------
// Environment
// -----------------------------------------------------------------------------

const START_JITTER_SECONDS =
    Number(__ENV.START_JITTER_SECONDS || 1.5);

const MODE =
    __ENV.MODE || "finalize";

//
// Production traffic profile
//

/*const WARMUP_RATE =
    Number(__ENV.WARMUP_RATE || 8);

const RAMP_RATE =
    Number(__ENV.RAMP_RATE || 14);

const PEAK_RATE =
    Number(__ENV.PEAK_RATE || 18);

const TAPER_RATE =
    Number(__ENV.TAPER_RATE || 14);

const FINAL_RATE =
    Number(__ENV.FINAL_RATE || 8);*/

const EVENT = {
    participants: Number(__ENV.PARTICIPANTS || 25000),

    early: {
        duration: "10m",
        percentage: 0.45,
    },

    middle: {
        duration: "20m",
        percentage: 0.40,
    },

    late: {
        duration: "15m",
        percentage: 0.15,
    },
};

function rate(percent, minutes) {

    return Math.ceil(

        EVENT.participants *
        percent /
        (minutes * 60)

    );

}

const EARLY_RATE = rate(
    EVENT.early.percentage,
    parseInt(EVENT.early.duration)
);

const MIDDLE_RATE = rate(
    EVENT.middle.percentage,
    parseInt(EVENT.middle.duration)
);

const LATE_RATE = rate(
    EVENT.late.percentage,
    parseInt(EVENT.late.duration)
);

//
// Virtual User Pool
//

const PRE_ALLOCATED_VUS =
    Number(__ENV.PRE_ALLOCATED_VUS || 10000);

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
                Number(__ENV.START_RATE || 1),

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

                {
                    duration: EVENT.early.duration,
                    target: EARLY_RATE,
                },

                {
                    duration: EVENT.middle.duration,
                    target: MIDDLE_RATE,
                },

                {
                    duration: EVENT.late.duration,
                    target: LATE_RATE,
                },

                {
                    duration: "1s",
                    target: 0,
                },

            ]

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