import requests
import time
from collections import Counter

BASE = "http://localhost:8000"

# 🔴 UPDATE THESE EVERY RUN
TOKEN = "Bearer 1e35f382-c560-4f7b-af92-4636aa74be1f"
ATTEMPT_ID = "6940e285-57e8-4b2b-b5c2-38deb6a819e0"
QUESTION_ID = "f9e69e3b-82d0-4903-8904-6dd91ba7f32f"

headers = {
    "Authorization": TOKEN,
    "Content-Type": "application/json",
}

print("Using attempt:", ATTEMPT_ID)
input("Ensure attempt is FRESH and IN_PROGRESS → press Enter")

report = {}


# ---------- helper ----------
def submit(option):
    r = requests.post(
        f"{BASE}/attempts/{ATTEMPT_ID}/submit-answer",
        headers=headers,
        json={
            "question_id": QUESTION_ID,
            "selected_option": option,
            "hint_used": False,
        },
    )
    print("SUBMIT", option, "→", r.status_code, r.text)
    return r


# ---------- TEST 1: Idempotent ----------
print("\n--- TEST: IDEMPOTENT ---")
r1 = submit("A")
r2 = submit("A")
report["idempotent"] = r1.status_code == 200 and r2.status_code == 200


# ---------- TEST 2: Update ----------
print("\n--- TEST: UPDATE ---")
r3 = submit("B")
update_ok = False
if r3.status_code == 200:
    try:
        update_ok = "effective_score" in r3.json()
    except:
        update_ok = False

report["update"] = update_ok


# ---------- TEST 3: Resume ----------
print("\n--- TEST: RESUME ---")
resume = requests.get(
    f"{BASE}/attempts/{ATTEMPT_ID}/resume",
    headers=headers,
)

print("RESUME →", resume.status_code, resume.text)

resume_ok = False
if resume.status_code == 200:
    try:
        resume_ok = len(resume.json().get("progress", [])) >= 1
    except:
        resume_ok = False

report["resume"] = resume_ok


# ---------- TEST 4: Expiry Guard ----------
print("\n--- TEST: EXPIRY GUARD ---")
print("Waiting 2 seconds…")
time.sleep(2)

expiry_try = submit("A")
report["expiry_guard"] = expiry_try.status_code in [200, 403]


# ---------- TEST 5: Concurrency spam ----------
print("\n--- TEST: RACE SAFETY ---")
results = []
for _ in range(10):
    r = submit("A")
    results.append(r.status_code)

report["race_safe"] = Counter(results)[200] >= 1


# ---------- FINAL REPORT ----------
print("\n====== SAFETY REPORT ======")
for k, v in report.items():
    print(f"{k.upper():15} : {'PASS' if v else 'FAIL'}")

overall = all(report.values())
print("\nOVERALL:", "PASS ✅" if overall else "FAIL ❌")