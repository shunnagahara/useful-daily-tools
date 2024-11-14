import time
import webbrowser
import argparse
from datetime import datetime
import pytz

# Command-line arguments setup
parser = argparse.ArgumentParser(description="A program to automatically access a specified URL at a specified time")
parser.add_argument("url", type=str, help="The URL to access")
parser.add_argument("time", type=str, help="The time to access the URL (e.g., '10:00')")
parser.add_argument("timezone", type=str, help="The timezone for the specified time (e.g., 'America/Vancouver')")
args = parser.parse_args()

# python3 scheduled_url_opener.py "https://www.example.com" "21:00" "America/Vancouver"

# Convert the specified time to a timezone-aware datetime object
def get_scheduled_time_in_local(time_str, timezone):
    target_time = datetime.strptime(time_str, "%H:%M")
    tz = pytz.timezone(timezone)
    now = datetime.now(tz)
    return tz.localize(datetime(now.year, now.month, now.day, target_time.hour, target_time.minute))

# Open the specified URL at the scheduled time
def open_url_at_scheduled_time():
    scheduled_time = get_scheduled_time_in_local(args.time, args.timezone)
    print(f"Scheduled time: {scheduled_time}")
    while True:
        now = datetime.now(scheduled_time.tzinfo)
        print(f"Current time: {now}")
        
        # Check if the current time matches the scheduled time
        if now >= scheduled_time:
            print(f"Accessing {args.url} at {now}")
            webbrowser.open(args.url)
            break
        time.sleep(1)  # Check every second for precise timing

# Execute the function to open the URL at the scheduled time
open_url_at_scheduled_time()
