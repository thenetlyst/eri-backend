/**
 * ============================================================
 * ERI Production Qualification Framework
 * National Event Configuration
 * ============================================================
 */

export const EVENT = {

    // -------------------------------------------------------------------------
    // Event Scale
    // -------------------------------------------------------------------------

    PARTICIPANTS: 25000,

    QUESTIONS_PER_ASSESSMENT: 10,

    // -------------------------------------------------------------------------
    // Timing
    // -------------------------------------------------------------------------

    EXAM_WINDOW_SECONDS: 60 * 60,

    TARGET_ASSESSMENT_DURATION_SECONDS: 20 * 60,

    // -------------------------------------------------------------------------
    // Arrival Distribution
    // -------------------------------------------------------------------------

    ARRIVAL: {

        EARLY_PERCENT: 0.45,

        MIDDLE_PERCENT: 0.35,

        LATE_PERCENT: 0.20,

        EARLY_WINDOW_SECONDS: 10 * 60,

        MIDDLE_WINDOW_SECONDS: 20 * 60,

        LATE_WINDOW_SECONDS: 15 * 60,

    },

};