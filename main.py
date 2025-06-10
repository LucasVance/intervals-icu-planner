# filename: main.py

import requests
import json
import os
from datetime import date, timedelta, datetime, time

class IntervalsAPI:
    """A client to interact with the Intervals.icu API."""
    BASE_URL = "https://intervals.icu"

    def __init__(self, athlete_id, api_key):
        if not athlete_id or not api_key:
            raise ValueError("API credentials (ATHLETE_ID, API_KEY) not found in environment variables.")
        self.auth = ("API_KEY", api_key)
        self.athlete_url = f"{self.BASE_URL}/api/v1/athlete/{athlete_id}"

    def get_current_state(self, for_date: date):
        # ... (This function remains exactly the same)
        date_str = for_date.isoformat()
        url = f"{self.athlete_url}/wellness/{date_str}"
        try:
            response = requests.get(url, auth=self.auth, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data.get('ctl') is None or data.get('atl') is None:
                print("ERROR: API response received, but CTL/ATL data is missing.")
                return None
            return {"ctl": data.get('ctl'), "atl": data.get('atl')}
        except requests.exceptions.RequestException as e:
            print(f"ERROR: Could not connect to Intervals.icu API: {e}")
            return None
        except json.JSONDecodeError:
            print(f"ERROR: Could not decode JSON response from API.")
            return None

    def create_workout(self, workout_data: dict):
        # ... (This function remains exactly the same)
        url = f"{self.athlete_url}/events"
        try:
            response = requests.post(url, auth=self.auth, json=workout_data, timeout=10)
            response.raise_for_status()
            print("SUCCESS: Workout successfully created on Intervals.icu calendar.")
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"ERROR: Failed to create workout: {e}")
            if e.response is not None:
                print(f"Server Response: {e.response.text}")
            return None

def calculate_next_day_tss(current_ctl, current_atl, goals_config):
    # ... (This function remains exactly the same)
    tss_for_tsb_goal = (41 * current_ctl - 36 * current_atl - 42 * goals_config['target_tsb']) / 5
    tss_cap_from_alb = current_atl - (goals_config['alb_lower_bound'] * (7/6))
    final_tss = min(tss_for_tsb_goal, tss_cap_from_alb)
    final_tss = max(0, final_tss)
    return final_tss

def build_z2_workout_for_tss(target_tss, workout_config, workout_date: date):
    # ... (This function remains exactly the same)
    workout_datetime = datetime.combine(workout_date, time(7, 0))
    name_prefix = workout_config.get("name_prefix", "Auto-Plan:")
    if target_tss <= 0:
        return {
            "category": "WORKOUT", "type": "Rest",
            "name": f"{name_prefix} Rest Day",
            "start_date_local": workout_datetime.isoformat(),
            "description": "Rest Day"
        }
    ramp_duration_min = workout_config['ramp_duration_min']
    ramp_start_pct = workout_config['ramp_start_pct']
    main_set_pct = workout_config['power_target_pct']
    ramp_if_squared = ((ramp_start_pct**2) + (main_set_pct**2)) / 2.0
    ramp_duration_hr = ramp_duration_min / 60.0
    ramp_tss = ramp_if_squared * ramp_duration_hr * 100
    tss_for_main_set = target_tss - ramp_tss
    main_set_duration_min = 0
    if tss_for_main_set > 0 and main_set_pct > 0:
        main_set_if_squared = main_set_pct**2
        main_set_duration_hr = tss_for_main_set / (main_set_if_squared * 100)
        main_set_duration_min = round(main_set_duration_hr * 60)
    ramp_string = f"- {ramp_duration_min}m ramp {ramp_start_pct:.0%}-{main_set_pct:.0%} FTP"
    main_set_string = f"- {main_set_duration_min}m {main_set_pct:.0%} FTP"
    workout_description = f"{ramp_string}\n{main_set_string}" if main_set_duration_min > 0 else ramp_string
    workout_object = {
        "category": "WORKOUT", "type": "Ride",
        "name": f"{name_prefix} {round(target_tss)} TSS",
        "start_date_local": workout_datetime.isoformat(),
        "description": workout_description,
        "load": round(target_tss)
    }
    return workout_object

def main_handler(event, context):
    """
    This is the main entry point for the Google Cloud Function.
    The 'event' and 'context' arguments are required by GCP but not used in this simple scheduler setup.
    """
    print("--- Cloud Function Initialized ---")
    
    # Load configuration from the bundled config.json file
    try:
        with open("config.json") as f:
            config = json.load(f)
    except FileNotFoundError:
        print("ERROR: config.json not found.")
        return # Exit gracefully
    
    # Load secrets from secure environment variables
    try:
        api_key = os.environ['API_KEY']
        athlete_id = os.environ['ATHLETE_ID']
    except KeyError as e:
        print(f"ERROR: Missing secret environment variable: {e}")
        return

    # Initialize API Client
    api = IntervalsAPI(athlete_id, api_key)

    # Get Current State
    today = date.today()
    print(f"Fetching current state for today ({today.isoformat()})...")
    state = api.get_current_state(for_date=today)
    if not state:
        print("Halting script due to API error.")
        return
    
    current_ctl = state['ctl']
    current_atl = state['atl']
    print(f"Current State -> CTL: {current_ctl:.2f}, ATL: {current_atl:.2f}")

    # Calculate Tomorrow's Target TSS
    target_tss_tomorrow = calculate_next_day_tss(current_ctl, current_atl, config['training_goals'])
    print(f"Calculation -> Target TSS for tomorrow: {target_tss_tomorrow:.2f}")
    
    # Build the Workout
    tomorrow = today + timedelta(days=1)
    workout_to_upload = build_z2_workout_for_tss(target_tss_tomorrow, config['workout_settings'], workout_date=tomorrow)
    print("Workout Builder -> Generated workout object:")
    print(json.dumps(workout_to_upload, indent=2))

    # Send Workout to Intervals.icu
    if config['operational_settings']['live_mode']:
        if workout_to_upload:
            print("LIVE MODE IS ON. Uploading workout to Intervals.icu...")
            api.create_workout(workout_to_upload)
        else:
            print("LIVE MODE IS ON, but workout object could not be generated.")
    else:
        print("DRY RUN MODE IS ON. No workout was uploaded.")
    
    print("--- Cloud Function Finished ---")
    return "OK" # Return a success message

# Add this block to the very end of main.py

if __name__ == "__main__":
    # This block runs when the script is executed directly.
    # We call the main_handler function, passing None for the unused
    # event and context parameters.
    main_handler(None, None)
