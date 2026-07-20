import {
    Counter,
    Trend,
    Rate,
} from "k6/metrics";

//
// -----------------------------------------------------------------------------
// Assessment Counters
// -----------------------------------------------------------------------------

export const assessmentsStarted =
    new Counter("assessment_started");
    
export const assessmentsCompleted =
    new Counter("assessment_completed");

export const assessmentsFailed =
    new Counter("assessment_failed");

export const questionsAnswered =
    new Counter("questions_answered");

export const reconstructsPerformed =
    new Counter("reconstructs_performed");

//
// -----------------------------------------------------------------------------
// Assessment Timing
// -----------------------------------------------------------------------------

export const assessmentWallClockDuration =
    new Trend("assessment_wall_clock_duration");

export const assessmentPlatformDuration =
    new Trend("assessment_platform_duration");

//
// -----------------------------------------------------------------------------
// Success Rate
// -----------------------------------------------------------------------------

export const assessmentSuccess =
    new Rate("assessment_success");