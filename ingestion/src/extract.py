# AI wirtten code, need to refine it fully and comment what is not understandable (requests,os,json part fine, but pathlib, typing added later)
import os
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import requests
from dotenv import load_dotenv


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_env() -> Dict[str, str]:
    load_dotenv()
    required = [
        "STRAVA_CLIENT_ID",
        "STRAVA_CLIENT_SECRET",
        "STRAVA_REFRESH_TOKEN",
    ]
    missing = [k for k in required if not os.getenv(k)]
    if missing:
        raise RuntimeError(f"Missing env vars: {', '.join(missing)}")

    # Access token can be empty initially; we can refresh using refresh_token.
    return {
        "client_id": os.getenv("STRAVA_CLIENT_ID", ""),
        "client_secret": os.getenv("STRAVA_CLIENT_SECRET", ""),
        "refresh_token": os.getenv("STRAVA_REFRESH_TOKEN", ""),
        "access_token": os.getenv("STRAVA_API_KEY", ""),  # optional
        "expires_at": os.getenv("STRAVA_TOKEN_EXPIRES_AT", "0"),
    }


def refresh_access_token(
    client_id: str,
    client_secret: str,
    refresh_token: str,
) -> Dict[str, Any]:
    """Always refreshes token using refresh_token. Returns token payload."""
    resp = requests.post(
        "https://www.strava.com/oauth/token",
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def get_valid_access_token(env: Dict[str, str]) -> Dict[str, Any]:
    """
    If token is missing/expired -> refresh.
    """
    try:
        expires_at = int(env.get("expires_at") or "0")
    except ValueError:
        expires_at = 0

    access_token = env.get("access_token") or ""
    now = int(time.time())

    if (not access_token) or (now >= expires_at):
        print("Access token missing/expired -> refreshing via refresh token...")
        token_data = refresh_access_token(
            env["client_id"], env["client_secret"], env["refresh_token"]
        )
        # Print instructions (safer than editing .env automatically)
        print("\nUpdate your .env with these new values:")
        print(f"STRAVA_API_KEY={token_data.get('access_token')}")
        print(f"STRAVA_REFRESH_TOKEN={token_data.get('refresh_token')}")
        print(f"STRAVA_TOKEN_EXPIRES_AT={token_data.get('expires_at')}\n")
        return token_data

    # token still valid; return in same shape as refresh payload
    return {
        "access_token": access_token,
        "refresh_token": env["refresh_token"],
        "expires_at": expires_at,
    }


def fetch_activities(access_token: str, per_page: int = 200) -> List[Dict[str, Any]]:
    """
    Fetches ALL activities available via paging.
    Raw ingestion best practice: do not filter business logic here.
    """
    url = "https://www.strava.com/api/v3/athlete/activities"
    headers = {"Authorization": f"Bearer {access_token}"}

    all_activities: List[Dict[str, Any]] = []
    page = 1

    while True:
        params = {"per_page": per_page, "page": page}
        resp = requests.get(url, headers=headers, params=params, timeout=30)

        # Helpful error detail
        if resp.status_code != 200:
            raise RuntimeError(f"Strava API error {resp.status_code}: {resp.text}")

        data = resp.json()
        if not data:
            break

        all_activities.extend(data)
        page += 1

    return all_activities


def save_raw_json(activities: List[Dict[str, Any]], out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"strava_activities_raw_{_utc_now_iso().replace(':','')}.json"
    payload = {
        "extracted_at_utc": _utc_now_iso(),
        "record_count": len(activities),
        "activities": activities,
    }
    out_path.write_text(json.dumps(payload, ensure_ascii=False))
    return out_path


def save_raw_csv_flat(activities: List[Dict[str, Any]], out_dir: Path) -> Path:
    """
    Optional: a quick flat CSV with the raw keys Strava returns (not derived metrics).
    This is still 'raw-ish' but JSON is the better raw format.
    """
    import pandas as pd  # local import to keep top clean

    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "strava_activities_raw_flat.csv"
    df = pd.json_normalize(activities, sep="__")
    df.to_csv(out_path, index=False)
    return out_path


def main() -> None:
    env = load_env()
    token_data = get_valid_access_token(env)

    activities = fetch_activities(token_data["access_token"], per_page=200)
    print(f"Fetched {len(activities)} activities.")

    # Raw outputs (recommended)
    out_dir = Path("data") / "raw"
    json_path = save_raw_json(activities, out_dir)
    print(f"Saved raw JSON: {json_path}")

    # Optional convenience export (still raw-ish)
    csv_path = save_raw_csv_flat(activities, out_dir)
    print(f"Saved raw flat CSV: {csv_path}")


if __name__ == "__main__":
    main()
