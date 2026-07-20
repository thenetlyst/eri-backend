import { sleep } from "k6";
import { randomInt } from "./helpers.js";

export function think(profile) {

    sleep(
        randomInt(
            profile.thinkMin,
            profile.thinkMax
        )
    );

}