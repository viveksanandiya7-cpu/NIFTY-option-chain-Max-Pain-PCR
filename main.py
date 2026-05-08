import sys
import time
from datetime import datetime

from auth import load_settings
from option_chain import (
    get_weekly_expiry,
    get_option_chain,
    parse_chain_data,
    print_chain,
)


def main():
    print("Loading settings...")
    try:
        settings = load_settings()
    except Exception as e:
        print(f"Failed to load settings.ini: {e}")
        sys.exit(1)

    if "your_" in settings["api_key"].lower():
        print("Please fill in your actual Upstox credentials in settings.ini")
        sys.exit(1)

    if "your_" in settings["access_token"].lower():
        print("Please fill in your ACCESS_TOKEN in settings.ini")
        sys.exit(1)

    access_token = settings["access_token"]
    cycle = 0

    try:
        while True:
            cycle += 1
            now = datetime.now()
            print(f"\n{'#' * 60}")
            print(f"  Cycle {cycle} - {now.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'#' * 60}")

            expiry = get_weekly_expiry()
            expiry_str = expiry.strftime("%Y-%m-%d")
            print(f"  Fetching NIFTY option chain for expiry {expiry_str}...")

            try:
                data = get_option_chain(access_token, expiry)
            except Exception as e:
                print(f"  Fetch failed: {e}")
                print("  Retrying in 180s...")
                time.sleep(180)
                continue

            chain = parse_chain_data(data)
            print(f"  Found {len(chain)} strikes")

            if len(chain) > 0:
                print_chain(chain, expiry)
            else:
                print("  No option chain data available")

            print("  Sleeping 180s...")
            time.sleep(180)

    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)


if __name__ == "__main__":
    main()
