import { EVENT } from "../config/event_config.js";

export function calculateArrivalRates() {

    const earlyParticipants =
        EVENT.PARTICIPANTS *
        EVENT.ARRIVAL.EARLY_PERCENT;

    const middleParticipants =
        EVENT.PARTICIPANTS *
        EVENT.ARRIVAL.MIDDLE_PERCENT;

    const lateParticipants =
        EVENT.PARTICIPANTS *
        EVENT.ARRIVAL.LATE_PERCENT;

    return {

        earlyRate:
            earlyParticipants /
            EVENT.ARRIVAL.EARLY_WINDOW_SECONDS,

        middleRate:
            middleParticipants /
            EVENT.ARRIVAL.MIDDLE_WINDOW_SECONDS,

        lateRate:
            lateParticipants /
            EVENT.ARRIVAL.LATE_WINDOW_SECONDS,

    };

}