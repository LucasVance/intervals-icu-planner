# filename: main.py

import requests
import json
import os
from datetime import date, timedelta, datetime, time, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

# --- ADDED: Version constant for the script ---
SCRIPT_VERSION = "1.2.0"

# ==============================================================================
# --- API CLIENT, CALCULATION ENGINE, WORKOUT BUILDER (All Unchanged) ---
# ==============================================================================
class IntervalsAPI:
    """A client to interact with the Intervals.icu API."""
    BASE_URL = "https://intervals.icu"
    def __init__(self, athlete_id, api_key):
        if not athlete_id or not api_key:
            raise ValueError("API credentials (ATHLETE_ID, API_KEY) not found in environment variables.")
        self.auth = ("API_KEY", api_key)
        self.athlete_url = f"{self.BASE_URL}/api/v1/athlete/{athlete_id}"
    def get_current_state(self, for_date: date):
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
        except requests.exceptions.RequestException as e: print(f"ERROR: Could not connect to Intervals.icu API: {e}"); return None
        except json.JSONDecodeError: print(f"ERROR: Could not decode JSON response from API."); return None
    def create_workout(self, workout_data: dict):
        url = f"{self.athlete_url}/events"
        try:
            response = requests.post(url, auth=self.auth, json=workout_data, timeout=10)
            response.raise_for_status()
            print("SUCCESS: Workout successfully created on Intervals.icu calendar.")
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"ERROR: Failed to create workout: {e}")
            if e.response is not None: print(f"Server Response: {e.response.text}")
            return None

def calculate_next_day_tss(current_ctl, current_atl, goals_config):
    # This uses the older, hardcoded 42/7 constants from the uploaded main.py
    # To make this configurable, we would read ctl_days and atl_days from config
    tss_for_tsb_goal = (41 * current_ctl - 36 * current_atl - 42 * goals_config['target_tsb']) / 5
    tss_cap_from_alb = current_atl - (goals_config['alb_lower_bound'] * (7/6))
    reason = "TSB Driven"
    final_tss = tss_for_tsb_goal
    if final_tss > tss_cap_from_alb:
        final_tss = tss_cap_from_alb
        reason = "Capped by ALB Limit"
    final_tss = max(0, final_tss)
    return {
        "final_tss": final_tss,
        "tss_for_tsb_goal": tss_for_tsb_goal,
        "tss_cap_from_alb": tss_cap_from_alb,
        "reason": reason
    }

def build_z2_workout_for_tss(tss_details, current_ctl, current_atl, goals_config, workout_config, workout_date: date):
    target_tss = tss_details['final_tss']
    workout_datetime = datetime.combine(workout_date, time(7, 0))
    name_prefix = workout_config.get("name_prefix", "Auto-Plan:")
    if target_tss <= 0:
        return {"category": "WORKOUT", "type": "Rest", "name": f"{name_prefix} Rest Day", "start_date_local": workout_datetime.isoformat(), "description": "Rest Day"}
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
    workout_steps = f"{ramp_string}\n{main_set_string}" if main_set_duration_min > 0 else ramp_string
    rationale_string = f"""
<h3>Auto-Plan Rationale</h3>
<table>
    <style>
        td:first-child {{
            padding-right: 5px; text-align: right;
        }}
    </style>
    <tr>
        <td>TSB Limit: </td>
        <td>{goals_config['target_tsb']:.1f}</td>
    </tr>
    <tr>
        <td>ALB Limit: </td>
        <td>{goals_config['alb_lower_bound']:.1f}</td>
    </tr>
    <tr>
        <td>CTL: </td>
        <td>{current_ctl:.1f}</td>
    </tr>
    <tr>
        <td>ATL: </td>
        <td>{current_atl:.1f}</td>
    </tr>
    <tr>
        <td>TSS limit from TSB: </td>
        <td>{tss_details['tss_for_tsb_goal']:.1f}</td>
    </tr>
    <tr>
        <td>TSS limit from ALB: </td>
        <td>{tss_details['tss_cap_from_alb']:.1f}</td>
    </tr>
    <tr>
        <td>Final TSS target: </td>
        <td>{tss_details['final_tss']:.1f} ({tss_details['reason']})</td>
    </tr>
</table>"""
    final_description = f"{workout_steps}\n{rationale_string}"
    workout_object = {"category": "WORKOUT", "type": "Ride", "name": f"{name_prefix} {round(target_tss)} TSS", "start_date_local": workout_datetime.isoformat(), "description": final_description, "load": round(target_tss)}
    return workout_object

# ==============================================================================
# --- MAIN HANDLER (Updated with more logging) ---
# ==============================================================================
def main_handler(event, context):
    """This is the main entry point for the GitHub Action."""
    
    # --- ADDED: More detailed initial logging ---
    run_timestamp_utc = datetime.now(timezone.utc)
    print(f"--- Daily Training Plan Script v{SCRIPT_VERSION} Initialized ---")
    print(f"Run Timestamp (UTC): {run_timestamp_utc.isoformat()}")
    
    try:
        with open("config.json") as f:
            config = json.load(f)
    except FileNotFoundError:
        print("ERROR: config.json not found.")
        return
    except json.JSONDecodeError:
        print("ERROR: Could not parse config.json.")
        return

    try:
        user_timezone_str = config['operational_settings']['timezone']
        user_timezone = ZoneInfo(user_timezone_str)
        today = datetime.now(user_timezone).date()
    except (KeyError, ZoneInfoNotFoundError):
        print(f"ERROR: Invalid or missing timezone in config.json. Using UTC as default.")
        today = date.today()

    # --- ADDED: Log the configuration being used for the run ---
    print("\n--- Using configuration ---")
    print(f"Timezone: {user_timezone_str}")
    print("Training Goals:", json.dumps(config.get('training_goals'), indent=2))
    print("Workout Settings:", json.dumps(config.get('workout_settings'), indent=2))
    print("---------------------------\n")

    try:
        api_key = os.environ['API_KEY']
        athlete_id = os.environ['ATHLETE_ID']
    except KeyError as e:
        print(f"ERROR: Missing secret environment variable: {e}")
        return

    api = IntervalsAPI(athlete_id, api_key)

    print(f"Fetching current state for user's local date: {today.isoformat()}")
    state = api.get_current_state(for_date=today)
    if not state:
        print("Halting script due to API error.")
        return
    
    current_ctl = state['ctl']
    current_atl = state['atl']
    print(f"Current State -> CTL: {current_ctl:.2f}, ATL: {current_atl:.2f}")

    tss_details_tomorrow = calculate_next_day_tss(current_ctl, current_atl, config['training_goals'])
    print(f"Calculation -> Target TSS for tomorrow: {tss_details_tomorrow['final_tss']:.2f} ({tss_details_tomorrow['reason']})")
    
    tomorrow = today + timedelta(days=1)
    workout_to_upload = build_z2_workout_for_tss(
        tss_details_tomorrow, 
        current_ctl, 
        current_atl, 
        config['training_goals'], 
        config['workout_settings'], 
        workout_date=tomorrow
    )
    print("Workout Builder -> Generated workout object:")
    if workout_to_upload and isinstance(workout_to_upload, dict):
        desc = workout_to_upload.pop('description', '')
        print(json.dumps(workout_to_upload, indent=2))
        workout_to_upload['description'] = desc
    else:
        print(workout_to_upload)

    print("-" * 20)
    if config['operational_settings'].get('live_mode', False):
        if workout_to_upload:
            print("LIVE MODE IS ON. Uploading workout to Intervals.icu...")
            api.create_workout(workout_to_upload)
        else:
            print("LIVE MODE IS ON, but workout object could not be generated.")
    else:
        print("DRY RUN MODE IS ON. No workout was uploaded.")
    
    print("--- Script Finished ---")
    return "OK"

if __name__ == "__main__":
    main_handler(None, None)