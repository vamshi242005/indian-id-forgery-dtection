import requests
import os
import sys

print("=== STARTING END-TO-END VERIFICATION ===")

# Test 1: Frontend Server
try:
    fe_res = requests.get("http://localhost:5500")
    print(f"[PASS] Frontend HTTP Server reachable on port 5500 (Status: {fe_res.status_code})")
except Exception as e:
    print("[FAIL] Frontend HTTP Server error:", e)
    sys.exit(1)

# Test 2: Backend Health Check
try:
    be_res = requests.get("http://localhost:8005/health", headers={"ngrok-skip-browser-warning": "true"})
    print("[PASS] Backend /health check passed:", be_res.json())
except Exception as e:
    print("[FAIL] Backend /health check failed:", e)
    sys.exit(1)

# Test 3: Document Predictions
test_dir = r"C:\Users\kv035\.gemini\antigravity-ide\scratch\document-forgery-detection\test_images"
tests = [
    ("aadhaar_original.jpg", "aadhaar", "ORIGINAL"),
    ("aadhaar_fake.jpg", "aadhaar", "FAKE"),
    ("pan_original.jpg", "pan", "ORIGINAL"),
    ("pan_fake.jpg", "pan", "FAKE"),
    ("passport_original.jpg", "passport", "ORIGINAL"),
    ("voterid_original.jpg", "voterid", "ORIGINAL")
]

for fname, doc_type, expected_label in tests:
    fpath = os.path.join(test_dir, fname)
    with open(fpath, "rb") as f:
        res = requests.post(
            "http://localhost:8005/predict",
            data={"document_type": doc_type},
            files={"file": (fname, f, "image/jpeg")},
            headers={"ngrok-skip-browser-warning": "true"}
        )
        data = res.json()
        print(f"[PREDICT] {fname} ({doc_type}) -> Status: {res.status_code}, Label: {data.get('label')}, Confidence: {data.get('confidence')}%, Explanation Provided: {data.get('explanation') is not None}")
        if res.status_code != 200 or data.get('label') != expected_label:
            print(f"Error on {fname}: expected {expected_label}, got {data}")
            sys.exit(1)

print("\n=== ALL END-TO-END VERIFICATION TESTS PASSED SUCCESSFULLY! ===")
