"""
Seed demo integrations for an account via the running local API.

Usage (from backend/ directory):
    python3 scripts/seed_via_api.py <email> <password>

Example:
    python3 scripts/seed_via_api.py Jeremenkovic23@gmail.com yourpassword
"""

import sys
import requests

BASE = "http://localhost:8000/api/v1"


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 scripts/seed_via_api.py <email> <password>")
        sys.exit(1)

    email, password = sys.argv[1], sys.argv[2]

    # 1. Login
    resp = requests.post(f"{BASE}/auth/login", json={"email": email, "password": password})
    if not resp.ok:
        print(f"✗ Login failed: {resp.status_code} {resp.text[:200]}")
        sys.exit(1)
    token = resp.json()["access_token"]
    print(f"✓ Logged in as {email}")

    headers = {"Authorization": f"Bearer {token}"}

    # 2. Get company_id for this user's account
    me = requests.get(f"{BASE}/auth/me", headers=headers)
    if not me.ok:
        print(f"✗ Could not get user info: {me.text}")
        sys.exit(1)
    company_id = me.json()["company_id"]
    print(f"✓ Company ID: {company_id}")

    # 3. Call seed-demo endpoint
    resp = requests.post(
        f"{BASE}/super-admin/companies/{company_id}/seed-demo",
        headers=headers,
    )
    if not resp.ok:
        print(f"✗ Seed failed: {resp.status_code} {resp.text[:300]}")
        sys.exit(1)

    result = resp.json()
    print(f"✓ Done!")
    print(f"  Integrations added:   {result['integrations_added']}")
    print(f"  Integrations skipped: {result['integrations_skipped']}")
    print(f"  Evidence upserted:    {result['evidence_upserted']}")
    if result["added"]:
        print(f"  Added: {', '.join(result['added'])}")


if __name__ == "__main__":
    main()
