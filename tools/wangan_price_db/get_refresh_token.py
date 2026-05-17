#!/usr/bin/env python3
"""Create a Gmail readonly OAuth refresh token for GitHub Actions secrets."""

from __future__ import annotations

import argparse
import os

from google_auth_oauthlib.flow import InstalledAppFlow

GMAIL_SCOPE = "https://www.googleapis.com/auth/gmail.readonly"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--client-id", default=os.environ.get("GOOGLE_CLIENT_ID"))
    parser.add_argument("--client-secret", default=os.environ.get("GOOGLE_CLIENT_SECRET"))
    parser.add_argument("--port", type=int, default=8080)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.client_id or not args.client_secret:
        raise SystemExit("Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET, or pass --client-id and --client-secret.")

    flow = InstalledAppFlow.from_client_config(
        {
            "installed": {
                "client_id": args.client_id,
                "client_secret": args.client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [f"http://localhost:{args.port}/"],
            }
        },
        scopes=[GMAIL_SCOPE],
    )
    credentials = flow.run_local_server(
        port=args.port,
        access_type="offline",
        prompt="consent",
    )
    print("\nAdd this value to GitHub Secrets as GOOGLE_REFRESH_TOKEN:\n")
    print(credentials.refresh_token)


if __name__ == "__main__":
    main()
