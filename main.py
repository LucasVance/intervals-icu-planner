# filename: main.py

import requests
import json
import os
import re
from datetime import date, timedelta, datetime, time
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

# ==============================================================================
# --- API CLIENT (Unchanged) ---
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
            if data.get('ctl') is None or data.get('atl') is None: return None
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

# ==============================================================================
# --- CALCULATION ENGINE (Updated to return rationale details) ---
# ==============================================================================
def calculate_next_day_tss(current_ctl, current_atl, goals_config):
    """Calculates the target TSS and returns a dictionary with calculation details."""
    c = goals_config.get('ctl_days', 42)
    a = goals_config.get('atl_days', 7)
    kc = (c - 1) / c
    ka = (a - 1) / a
    tsb_tss_multiplier = (1/c) - (1/a)
    
    if abs(tsb_tss_multiplier) > 1e-9:
        numerator = goals_config['target_tsb'] - (current_ctl * kc) + (current_atl * ka)
        tss_for_tsb_goal = numerator / tsb_tss_multiplier
    else:
        tss_for_tsb_goal = current_atl
        
    tss_cap_from_alb = current_atl - goals_config['alb_lower_bound']

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

# ==============================================================================
# --- WORKOUT BUILDER (Updated with HTML Rationale) ---
# ==============================================================================
def _calculate_tss_for_step(step_string):
    """Calculates the TSS for a single line from a workout description."""
    try:
        duration_match = re.search(r'(\d+)\s*m', step_string)
        if not duration_match: return 0.0
        duration_min = int(duration_match.group(1))
        duration_hr = duration_min / 60.0
        intensity_parts = [int(p) for p in re.findall(r'(\d+)%', step_string)]
        if not intensity_parts: return 0.0
        start_pct = intensity_parts[0] / 100.0
        end_pct = intensity_parts[1] / 100.0 if len(intensity_parts) > 1 else start_pct
        if 'ramp' in step_string.lower():
            if_squared = ((start_pct**2) + (end_pct**2)) / 2.0
        else:
            if_squared = start_pct**2
        return if_squared * duration_hr * 100
    except (ValueError, IndexError):
        return 0.0

def build_workout_from_template(target_tss, template, workout_date, tss_details, goals_config, current_ctl, current_atl, part_num=None, total_parts=None):
    """Builds a workout object, including a detailed HTML rationale."""
    
    workout_datetime = datetime.combine(workout_date, time(7, 0))
    if part_num and part_num > 1:
        workout_datetime += timedelta(hours=10)

    # --- FIX: Correctly use the prefix from the configuration ---
    name_prefix = config['operational_settings'].get("workout_name_prefix", "Auto-Plan:")
    workout_name = f"{name_prefix}{template['name']}"
    if total_parts and total_parts > 1:
        workout_name += f" ({part_num}/{total_parts})"

    # --- Workout Step Generation ---
    fixed_tss = 0
    variable_step_line = ""
    for line in template['description'].split('\n'):
        if '{{ DURATION }}' in line:
            variable_step_line = line
        else:
            fixed_tss += _calculate_tss_for_step(line)
    
    tss_for_variable_part = target_tss - fixed_tss
    final_description = ""

    if variable_step_line:
        intensity_match = re.search(r'(\d{1,3})%', variable_step_line)
        main_set_pct = int(intensity_match.group(1)) / 100.0 if intensity_match else 0
        main_set_duration_min = 0
        if tss_for_variable_part > 0 and main_set_pct > 0:
            main_set_if_squared = main_set_pct**2
            main_set_duration_hr = tss_for_variable_part / (main_set_if_squared * 100)
            main_set_duration_min = round(main_set_duration_hr * 60)
        variable_line_final = variable_step_line.replace('{{ DURATION }}', f'{main_set_duration_min}m')
        final_description = template['description'].replace(variable_step_line, variable_line_final)
    else:
        final_description = template['description']

    # --- Rationale Generation ---
    split_info_html = ""
    if total_parts and total_parts > 1:
        split_info_html = f"""
    <tr>
        <td>Split:</td>
        <td>Part {part_num} of {total_parts}</td>
    </tr>"""

    rationale_string = f"""
<h3>Auto-Plan Rationale</h3>
<table>
    <style>
        td:first-child {{
            padding-right: 5px; text-align: right;
        }}
    </style>{split_info_html}
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

    final_description = f"{final_description}\n{rationale_string}"

    return {
        "category": "WORKOUT", "type": "Ride",
        "name": workout_name,
        "start_date_local": workout_datetime.isoformat(),
        "description": final_description,
        "load": round(target_tss)
    }

# ==============================================================================
# --- MAIN HANDLER (Updated to pass more info to workout builder) ---
# ==============================================================================
def main_handler(event, context):
    """Main entry point for the GitHub Action."""
    print("--- Daily Training Plan Script Initialized ---")
    
    global config # Make config globally accessible within this handler for simplicity
    try:
        with open("config.json") as f:
            config = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"ERROR loading config.json: {e}"); return

    try:
        user_timezone_str = config['operational_settings']['timezone']
        user_timezone = ZoneInfo(user_timezone_str)
        today = datetime.now(user_timezone).date()
    except (KeyError, ZoneInfoNotFoundError):
        print("ERROR: Invalid or missing timezone. Using UTC."); today = date.today()

    try:
        api_key = os.environ['API_KEY']; athlete_id = os.environ['ATHLETE_ID']
    except KeyError as e: print(f"ERROR: Missing secret environment variable: {e}"); return

    api = IntervalsAPI(athlete_id, api_key)
    print(f"Fetching current state for user's local date: {today.isoformat()} ({user_timezone_str})")
    state = api.get_current_state(for_date=today)
    if not state: print("Halting script due to API error."); return
    
    current_ctl, current_atl = state['ctl'], state['atl']
    print(f"Current State -> CTL: {current_ctl:.2f}, ATL: {current_atl:.2f}")

    total_target_tss_details = calculate_next_day_tss(current_ctl, current_atl, config['training_goals'])
    total_target_tss = total_target_tss_details['final_tss']
    print(f"Calculation -> Total Target TSS for tomorrow: {total_target_tss:.2f} ({total_target_tss_details['reason']})")

    tomorrow = today + timedelta(days=1)
    day_name = tomorrow.strftime('%A').lower()
    day_plan = config['weekly_schedule'].get(day_name, config['weekly_schedule']['default'])

    workouts_to_create = []
    
    if isinstance(day_plan, str) and '*' in day_plan:
        template_name, _, count = day_plan.partition('*')
        template_name = template_name.strip()
        num_workouts = int(count.strip())
        if num_workouts > 0 and template_name in config['workout_templates']:
            tss_per_workout = total_target_tss / num_workouts
            print(f"Planning {num_workouts} workouts with evenly split TSS of {tss_per_workout:.1f} each.")
            for i in range(num_workouts):
                workouts_to_create.append(build_workout_from_template(
                    tss_per_workout, config['workout_templates'][template_name], tomorrow, 
                    total_target_tss_details, config['training_goals'], current_ctl, current_atl, i + 1, num_workouts
                ))
    elif isinstance(day_plan, list):
        if len(day_plan) == 1:
            template_name = day_plan[0]
            if template_name in config['workout_templates']:
                print(f"Planning 1 workout with total TSS of {total_target_tss:.1f}.")
                workouts_to_create.append(build_workout_from_template(
                    total_target_tss, config['workout_templates'][template_name], tomorrow,
                    total_target_tss_details, config['training_goals'], current_ctl, current_atl
                ))
        elif len(day_plan) > 1:
            fixed_template_name = day_plan[0]
            if fixed_template_name in config['workout_templates']:
                fixed_template = config['workout_templates'][fixed_template_name]
                fixed_tss = sum(_calculate_tss_for_step(line) for line in fixed_template['description'].split('\n'))
                print(f"Planning a double day. Fixed workout '{fixed_template_name}' contributes {fixed_tss:.1f} TSS.")
                workouts_to_create.append(build_workout_from_template(
                    fixed_tss, fixed_template, tomorrow, 
                    total_target_tss_details, config['training_goals'], current_ctl, current_atl, 1, len(day_plan)
                ))
                remaining_tss = total_target_tss - fixed_tss
                variable_template_name = day_plan[1]
                if variable_template_name in config['workout_templates']:
                     print(f"Variable workout '{variable_template_name}' will target remaining {remaining_tss:.1f} TSS.")
                     workouts_to_create.append(build_workout_from_template(
                         remaining_tss, config['workout_templates'][variable_template_name], tomorrow,
                         total_target_tss_details, config['training_goals'], current_ctl, current_atl, 2, len(day_plan)
                     ))

    print("-" * 20)
    if config['operational_settings'].get('live_mode', False):
        if workouts_to_create:
            print(f"LIVE MODE IS ON. Uploading {len(workouts_to_create)} workout(s) to Intervals.icu...")
            for workout in workouts_to_create:
                if workout and workout.get("load", 0) > 0:
                    api.create_workout(workout)
        else:
            print("LIVE MODE IS ON, but no workouts were generated for the plan.")
    else:
        print(f"DRY RUN MODE IS ON. Would have created {len(workouts_to_create)} workout(s).")
    
    print("--- Script Finished ---")
    return "OK"

if __name__ == "__main__":
    main_handler(None, None)