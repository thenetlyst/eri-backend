import { check, sleep } from "k6";

import { activateAttempt } from "./attempt.js";
import { listQuestions, getQuestion } from "./questions.js";
import { submitAnswer } from "./answer.js";
import { reconstructAttempt } from "./reconstruct.js";
import { finalizeAttempt } from "./finalize.js";

import { randomOption } from "./helpers.js";

import { think } from "./thinktime.js";
import { review } from "./participant.js";

import {
    assessmentsStarted,
    assessmentsCompleted,
    assessmentsFailed,
    questionsAnswered,
    reconstructsPerformed,
    assessmentWallClockDuration,
    assessmentPlatformDuration,
    assessmentSuccess,
} from "./assessment_metrics.js";


export function runAssessment({

    userNumber,

    participant,

    mode = "finalize",

}) {

    const AssessmentState = {

        ACTIVE: "ACTIVE",

        EXPIRED: "EXPIRED",

        SUBMITTED: "SUBMITTED",

    };

    let assessmentState =
        AssessmentState.ACTIVE;

    const startTime = Date.now();

    let platformTime = 0;
    
    try {

        //
        // Start Attempt
        //

        let t = Date.now();

        const attempt = activateAttempt(userNumber);
        assessmentsStarted.add(1);

        platformTime += Date.now() - t;

        if (!check(attempt, {
            "attempt created": (r) => !!r?.attempt_id,
        })) {

            throw new Error("Unable to start assessment.");

        }

        if (mode === "start") {

            assessmentSuccess.add(true);

            return attempt;

        }

        //
        // Manifest
        //

        t = Date.now();

        const manifest = listQuestions(
            userNumber,
            attempt.attempt_id
        );

        platformTime += Date.now() - t;

        if (!check(manifest, {
            "manifest returned": (r) => Array.isArray(r),
            "manifest not empty": (r) => r.length > 0,
        })) {

            throw new Error("Manifest invalid.");

        }

        if (mode === "manifest") {

            assessmentSuccess.add(true);

            return manifest;

        }

        //
        // Walk Questions
        //

        for (const item of manifest) {


            if (item.bonus_locked) {
                continue;
            }

            t = Date.now();

            const question = getQuestion(

                userNumber,

                attempt.attempt_id,

                item.question_order

            );

            platformTime += Date.now() - t;

            if (!check(question, {

                "question returned": (q) => !!q?.question_id,

                "options returned": (q) => Array.isArray(q.options),

            })) {

                throw new Error(
                     `Question ${item.question_order} failed.`
                );

            }

            if (mode === "question") {
                return question;
            }

            //
            // Human thinking
            //

            think(participant);

            t = Date.now();

            const answerResult = submitAnswer(

                userNumber,

                attempt.attempt_id,

                question.question_id,

                randomOption(),

                false

            );

            platformTime += Date.now() - t;

            const response = answerResult.response;
            const answer = answerResult.data;
            const expected = answerResult.expected;

            if (response.status === 403) {

                const code = answer?.detail?.code;

                switch (code) {

                    case "ATTEMPT_EXPIRED":

                        assessmentState =
                            AssessmentState.EXPIRED;

                        break;

                    case "ATTEMPT_ALREADY_SUBMITTED":

                        assessmentState =
                            AssessmentState.SUBMITTED;

                        break;

                    default:

                        throw new Error(
                            `Unexpected response: ${code}`
                        );

                }

                break;

            }

            if (!expected) {

                throw new Error(
                    `Unexpected response ${response.status}`
                );

            }

            if (!check(answer, {

                "answer stored": (a) => a !== null,

            })) {

                throw new Error(
                    "Answer submission failed."
                );

            }

            questionsAnswered.add(1);

            //
        // Participant reads the submission result
        // before navigating to the next question.
        //

            sleep(
                Math.random() * 1.3 + 0.2
            );

            if (mode === "submit") {

                assessmentSuccess.add(true);

                return answer;

            }

        }

        if (
            assessmentState ===
            AssessmentState.EXPIRED
        ) {

            assessmentsFailed.add(1);

            assessmentSuccess.add(false);

            return;

        }

        if (
            assessmentState ===
            AssessmentState.SUBMITTED
        ) {

            assessmentsCompleted.add(1);

            assessmentSuccess.add(true);

            return;

        }

        //
        // Review Time
        //

        if (
            assessmentState ===
            AssessmentState.ACTIVE
        ) {

            review(participant);

        }

        //
        // Reconstruct
        //

        const shouldReconstruct =
        
            assessmentState ===
            AssessmentState.ACTIVE &&
        
            Math.random() < 0.30;

        if (shouldReconstruct) {

            t = Date.now();

            const snapshot = reconstructAttempt(

                userNumber,

                attempt.attempt_id

            );

            platformTime += Date.now() - t;

            if (!check(snapshot, {

                "snapshot returned": (r) => r !== null,

                "attempt exists": (r) => !!r.snapshot?.attempt,

                "questions restored": (r) =>
                    Array.isArray(r.snapshot?.questions),

            })) {

                throw new Error("Reconstruct failed.");

            }

            reconstructsPerformed.add(1);

            if (mode === "reconstruct") {

                assessmentSuccess.add(true);

                return snapshot;

            }

        }

        //
        // Finalize
        //




        if (
            assessmentState !==
            AssessmentState.ACTIVE
        ){

            return;

        }

        t = Date.now();

        const finalized = finalizeAttempt(

            userNumber,

            attempt.attempt_id

        );

        
        platformTime += Date.now() - t;

        const finalizedOk = check(finalized, {

            "attempt finalized": (r) =>
                r?.message === "Submission accepted" ||
                r?.message === "Attempt already submitted",

        });

        if (!finalizedOk) {

            throw new Error("Finalize failed.");

        }

        assessmentsCompleted.add(1);

        assessmentSuccess.add(true);

        return finalized;

    }

    catch (err) {

        assessmentsFailed.add(1);

        assessmentSuccess.add(false);

        throw err;

    }
    finally {

        assessmentWallClockDuration.add(

            Date.now() - startTime,

            {
                profile: participant.profile,
            }

        );

        assessmentPlatformDuration.add(

            platformTime,

            {
                profile: participant.profile,
            }

        );

    }

}