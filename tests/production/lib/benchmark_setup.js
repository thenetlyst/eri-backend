import { validateConfig } from "../config/config.js";
import { getUserNumber } from "./auth.js";
import { startAttempt } from "./attempt.js";
import { listQuestions } from "./questions.js";

export function prepareAttempt() {

    validateConfig();

    const userNumber = getUserNumber();

    const attempt = startAttempt(userNumber);

    if (!attempt?.attempt_id) {
        throw new Error("Unable to create attempt.");
    }

    return {
        userNumber,
        attemptId: attempt.attempt_id,
    };
}

export function prepareQuestion() {

    const state = prepareAttempt();

    const manifest = listQuestions(
        state.userNumber,
        state.attemptId
    );

    if (!manifest || manifest.length === 0) {
        throw new Error("Unable to load question manifest.");
    }

    return {
        ...state,
        manifest,
    };
}