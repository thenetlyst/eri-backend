import { getHeaders } from "../lib/auth.js";

export default function () {
    console.log(
        JSON.stringify(getHeaders(__VU), null, 2)
    );
}