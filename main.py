import os
import httpx
import psycopg
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse

app = FastAPI()

@app.get("/strava/callback")
async def strava_callback(request: Request):
    code = request.query_params.get("code")
    if not code:
        return PlainTextResponse("Authorization failed", status_code=400)

    async with httpx.AsyncClient() as client:
        r = await client.post(
            "https://www.strava.com/oauth/token",
            json={
                "client_id": os.getenv("STRAVA_CLIENT_ID"),
                "client_secret": os.getenv("STRAVA_CLIENT_SECRET"),
                "code": code,
                "grant_type": "authorization_code",
            },
        )

    token_data = r.json()
    athlete_id = token_data["athlete"]["id"]

    with psycopg.connect(os.getenv("DATABASE_URL")) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                insert into strava_tokens
                (athlete_id, access_token, refresh_token, expires_at, scope)
                values (%s, %s, %s, %s, %s)
                on conflict (athlete_id) do update set
                  access_token = excluded.access_token,
                  refresh_token = excluded.refresh_token,
                  expires_at = excluded.expires_at,
                  scope = excluded.scope,
                  updated_at = now();
                """,
                (
                    athlete_id,
                    token_data["access_token"],
                    token_data["refresh_token"],
                    token_data["expires_at"],
                    token_data.get("scope"),
                ),
            )

    return PlainTextResponse("Authorization successful. You can close this tab.")
