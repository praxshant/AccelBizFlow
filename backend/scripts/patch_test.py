from pathlib import Path

path = Path("backend/tests/test_phase234.py")
text = path.read_text(encoding="utf-8")

old = 'def test_reviewer_can_reach_all_kyc_outcomes():\n    applicant = f"REVIEW-KYC-{uuid4()}"'
new = 'def test_reviewer_can_reach_all_kyc_outcomes():\n    from app.auth import create_access_token, _secret\n    token = create_access_token("test-reviewer", "kyc_reviewer", _secret())\n    headers = {"Authorization": f"Bearer {token}"}\n    applicant = f"REVIEW-KYC-{uuid4()}"'

if old in text:
    text = text.replace(old, new)
    text = text.replace(
        'json={"status": status, "reason": "Reviewer decision", "reviewer_role": "kyc_reviewer"},',
        'json={"status": status, "reason": "Reviewer decision", "reviewer_role": "kyc_reviewer"},\n            headers=headers,'
    )
    path.write_text(text, encoding="utf-8")
    print("test_phase234.py patched successfully")
else:
    # Try CRLF
    old_crlf = old.replace('\n', '\r\n')
    new_crlf = new.replace('\n', '\r\n')
    if old_crlf in text:
        text = text.replace(old_crlf, new_crlf)
        text = text.replace(
            'json={"status": status, "reason": "Reviewer decision", "reviewer_role": "kyc_reviewer"},',
            'json={"status": status, "reason": "Reviewer decision", "reviewer_role": "kyc_reviewer"},\r\n            headers=headers,'
        )
        path.write_text(text, encoding="utf-8")
        print("test_phase234.py patched successfully (CRLF)")
    else:
        print("Could not find pattern in test_phase234.py")
