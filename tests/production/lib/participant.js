
import { sleep } from "k6";
import { randomInt } from "./helpers.js";

export function createParticipant() {

    const roll = Math.random();

    if (roll < 0.20) {

        return {
            profile: "fast",

            thinkMin: 40,
            thinkMax: 70,

            reviewMin: 20,
            reviewMax: 40,
            // Reserved for future behavioural modelling.
            // Currently answers are chosen randomly.
            // Future versions may use this to simulate:
            // - higher correctness rates
            // - hint usage
            // - answer changes during review
            answerAccuracy: 0.70,
        };
    }

    if (roll < 0.80) {

        return {
            profile: "average",

            thinkMin: 70,
            thinkMax: 110,

            reviewMin: 30,
            reviewMax: 60,

            // Reserved for future behavioural modelling.
            // Currently answers are chosen randomly.
            // Future versions may use this to simulate:
            // - higher correctness rates
            // - hint usage
            // - answer changes during review
            answerAccuracy: 0.60,
        };
    }

    return {

        profile: "careful",

        thinkMin: 100,
        thinkMax: 140,

        reviewMin: 40,
        reviewMax: 80,
        // Reserved for future behavioural modelling.
        // Currently answers are chosen randomly.
        // Future versions may use this to simulate:
        // - higher correctness rates
        // - hint usage
        // - answer changes during review
        answerAccuracy: 0.80,
    };

}

export function review(profile) {

    sleep(
        randomInt(
            profile.reviewMin,
            profile.reviewMax
        )
    );

}