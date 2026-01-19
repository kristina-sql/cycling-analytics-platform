import os
import requests
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime
import time

load_dotenv()

# Load credentials from .env
CLIENT_ID = os.getenv("STRAVA_CLIENT_ID")
CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")
ACCESS_TOKEN = os.getenv("STRAVA_API_KEY")  # your chosen variable
REFRESH_TOKEN = os.getenv("STRAVA_REFRESH_TOKEN")
EXPIRES_AT = int(os.getenv("STRAVA_TOKEN_EXPIRES_AT", 0))  # default 0 if missing

def refresh_token_if_needed():
    global ACCESS_TOKEN, REFRESH_TOKEN, EXPIRES_AT
    if time.time() >= EXPIRES_AT:
        print("Access token expired, refreshing...")
        response = requests.post(
            "https://www.strava.com/oauth/token",
            data={
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "grant_type": "refresh_token",
                "refresh_token": REFRESH_TOKEN
            }
        )
        data = response.json()
        ACCESS_TOKEN = data["access_token"]
        REFRESH_TOKEN = data["refresh_token"]
        EXPIRES_AT = data["expires_at"]

        # Update .env file with new tokens
        env_path = ".env"
        lines = []
        if os.path.exists(env_path):
            with open(env_path, "r") as f:
                lines = f.readlines()
        with open(env_path, "w") as f:
            updated_keys = ["STRAVA_API_KEY", "STRAVA_REFRESH_TOKEN", "STRAVA_TOKEN_EXPIRES_AT"]
            for key in updated_keys:
                # Remove old lines if they exist
                lines = [line for line in lines if not line.startswith(key + "=")]
            # Append updated values
            lines.append(f"STRAVA_API_KEY={ACCESS_TOKEN}\n")
            lines.append(f"STRAVA_REFRESH_TOKEN={REFRESH_TOKEN}\n")
            lines.append(f"STRAVA_TOKEN_EXPIRES_AT={EXPIRES_AT}\n")
            f.writelines(lines)
        print("Tokens refreshed and .env updated!")

# Refresh token if needed before API calls
refresh_token_if_needed()

# Prepare headers for API requests
headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}

# Fetch your last 200 activities (page 1 initially)
url = "https://www.strava.com/api/v3/athlete/activities"
params = {"per_page": 200, "page": 1}

all_activities = []
while True:
    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        raise Exception(f"Error: {response.status_code}, {response.text}")
    
    data = response.json()
    if not data:
        break
    
    all_activities.extend(data)
    params["page"] += 1

# Filter only virtual rides from 2025
rides_summary = []
for ride in all_activities:
    ride_date = datetime.strptime(ride["start_date"], "%Y-%m-%dT%H:%M:%SZ")
    if ride.get("sport_type") == "VirtualRide" and ride_date.year in [2025, 2026]:
        rides_summary.append({
            "ride_id": ride["id"],
            "name": ride["name"],
            "start_date": ride["start_date"],
            "distance_km": ride["distance"] / 1000,
            "moving_time_min": ride["moving_time"] / 60,
            "average_speed_kmh": ride["average_speed"] * 3.6,
            "elevation_m": ride["total_elevation_gain"],
            "average_power": ride.get("average_watts"),
            "max_power": ride.get("max_watts"),
            "average_hr": ride.get("average_heartrate"),
            "max_hr": ride.get("max_heartrate"),
            "kilojoules": ride.get("kilojoules"),
            "sport_type": ride.get("sport_type")
        })

df_summary = pd.DataFrame(rides_summary)
df_summary.to_csv("strava_virtual_2025_summary.csv", index=False)
print("Virtual 2025 rides CSV created!")