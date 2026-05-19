# filename: main.py

import requests
import json
import os
import re
import math
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

    def get_historical_kj_state(self, for_date: date):
        start_str = (for_date - timedelta(days=365)).isoformat()
        url = f"{self.athlete_url}/activities?oldest={start_str}"
        try:
            response = requests.get(url, auth=self.auth, timeout=10)
            response.raise_for_status()
            activities = response.json()
            
            # Deduplicate activities starting within the same minute (e.g., duplicate Garmin/Strava syncs)
            deduped = {}
            for act in activities:
                if 'start_date_local' in act:
                    minute_key = act['start_date_local'][:16] # YYYY-MM-DDTHH:MM
                    existing = deduped.get(minute_key)
                    if not existing:
                        deduped[minute_key] = act
                    else:
                        # Prefer the activity with actual work/load data
                        existing_score = (existing.get('icu_joules') or 0) + (existing.get('icu_training_load') or 0)
                        new_score = (act.get('icu_joules') or 0) + (act.get('icu_training_load') or 0)
                        if new_score > existing_score:
                            deduped[minute_key] = act

            daily_kj = {}
            for act in deduped.values():
                if 'start_date_local' in act:
                    d_str = act['start_date_local'][:10]
                    joules = act.get('icu_joules') or 0
                    daily_kj[d_str] = daily_kj.get(d_str, 0.0) + (joules / 1000.0)
            
            ctl = 0.0
            atl = 0.0
            c = float(config['training_goals']['ctl_days'])
            a = float(config['training_goals']['atl_days'])
            
            # Constants for continuous exponential decay matching Intervals.icu
            kc = math.exp(-1.0 / c)
            ka = math.exp(-1.0 / a)
            
            strava_warning = False
            for i in range(365, -1, -1):
                d = for_date - timedelta(days=i)
                d_str = d.isoformat()
                kj = daily_kj.get(d_str, 0.0)
                
                # Check for hidden Strava load
                if kj == 0 and any(act.get('start_date_local', '').startswith(d_str) and act.get('source') == 'STRAVA' for act in activities):
                    strava_warning = True

                ctl = ctl * kc + kj * (1 - kc)
                atl = atl * ka + kj * (1 - ka)
            
            if strava_warning:
                print("\nWARNING: Some historical activities were synced via Strava. Strava's API terms often hide kJ data from 3rd-party scripts, which may cause your calculated Fitness/Fatigue to be lower than the Intervals.icu charts.\n")
            
            return {"ctl": ctl, "atl": atl}
        except Exception as e:
            print(f"ERROR: Could not fetch historical activities for kJ calculation: {e}")
            return None
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
    def get_events(self, start_date: date, end_date: date):
        start_str = start_date.isoformat()
        end_str = end_date.isoformat()
        url = f"{self.athlete_url}/events?oldest={start_str}&newest={end_str}"
        try:
            response = requests.get(url, auth=self.auth, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"ERROR: Could not fetch events from Intervals.icu: {e}")
            return []
        except json.JSONDecodeError:
            print("ERROR: Could not decode JSON response for events.")
            return []

# ==============================================================================
# --- CALCULATION ENGINE (Corrected) ---
# ==============================================================================
def calculate_next_day_tss(current_ctl, current_atl, goals_config):
    """Calculates the target TSS and returns a dictionary with calculation details."""
    
    # Get the configured time constants.
    c = goals_config.get('ctl_days', 42)
    a = goals_config.get('atl_days', 7)

    # Decay constants
    kc = math.exp(-1.0 / c)
    ka = math.exp(-1.0 / a)

    # Determine targets with auto-calibration
    if 'target_ramp_rate' in goals_config:
        target_ramp_rate = float(goals_config['target_ramp_rate'])
        # Convert Ramp Rate to equivalent TSB target using continuous formula
        # target_tsb = target_ramp_rate * (ka - kc) / (7.0 * (1 - ka) * (1 - kc))
        target_tsb = target_ramp_rate * (ka - kc) / (7.0 * (1.0 - ka) * (1.0 - kc))
    elif 'target_tsb' in goals_config:
        target_tsb = float(goals_config['target_tsb'])
        # Convert TSB to equivalent Ramp Rate target using continuous formula
        # target_ramp_rate = target_tsb * 7.0 * (1 - ka) * (1 - kc) / (ka - kc)
        target_ramp_rate = target_tsb * 7.0 * (1.0 - ka) * (1.0 - kc) / (ka - kc)
    else:
        # Default fallback (e.g. Ramp Rate of 40.0 / wk)
        target_ramp_rate = 40.0
        target_tsb = target_ramp_rate * (ka - kc) / (7.0 * (1.0 - ka) * (1.0 - kc))

    # 1. Ramp Rate Bound (Prevents CTL Spikes)
    daily_ramp = target_ramp_rate / 7.0
    tss_for_ramp_goal = current_ctl + (daily_ramp / (1.0 - kc))

    # 2. TSB Bound (Gauges Freshness)
    numerator = target_tsb - (current_ctl * kc) + (current_atl * ka)
    denominator = ka - kc
    tss_for_tsb_goal = numerator / denominator if denominator != 0 else 0

    # 3. Apply Dual Bounds
    final_tss = min(tss_for_ramp_goal, tss_for_tsb_goal)
    final_tss = max(0.0, final_tss)

    # Determine active driver
    reason = "Ramp Rate Driven" if tss_for_ramp_goal <= tss_for_tsb_goal else "TSB Driven"

    return {
        "final_tss": final_tss,
        "tss_for_ramp_goal": tss_for_ramp_goal,
        "tss_for_tsb_goal": tss_for_tsb_goal,
        "reason": reason,
        "target_ramp_rate": target_ramp_rate,
        "target_tsb": target_tsb
    }

# ==============================================================================
# --- Lightweight Projection Function (Unchanged) ---
# ==============================================================================
def estimate_days_to_target(start_ctl, start_atl, goals_config):
    """
    Performs a quick simulation to estimate the number of days to reach the target CTL.
    """
    ctl_current = start_ctl
    atl_current = start_atl
    target_ctl = goals_config.get('target_ctl', 999)

    # Use the same constants as the main calculation
    c = goals_config.get('ctl_days', 42)
    a = goals_config.get('atl_days', 7)
    # Continuous exponential decay constants
    kc = math.exp(-1.0 / c)
    ka = math.exp(-1.0 / a)

    if ctl_current >= target_ctl:
        return 0

    for days_out in range(1, 365 * 3): # Max 3 year projection
        # This now correctly calls the updated, dynamic calculation function.
        tss_details = calculate_next_day_tss(ctl_current, atl_current, goals_config)
        tss_needed = tss_details['final_tss']
        
        atl_current = (atl_current * ka) + (tss_needed * (1 - ka))
        ctl_current = (ctl_current * kc) + (tss_needed * (1 - kc))

        if ctl_current >= target_ctl:
            return days_out
    
    return -1 # Return -1 if target is not reached within the projection window

# ==============================================================================
# --- WORKOUT BUILDER (Unchanged) ---
# ==============================================================================
def _calculate_load_for_step(step_string, mode='TSS'):
    """Calculates the TSS or kJ for a single line from a workout description."""
    try:
        duration_match = re.search(r'(\d+)\s*m', step_string)
        if not duration_match: return 0.0
        duration_min = int(duration_match.group(1))
        
        if mode == 'kJ':
            duration_sec = duration_min * 60
            intensity_parts = [int(p) for p in re.findall(r'(\d+)w', step_string.lower())]
            if not intensity_parts: return 0.0
            start_w = intensity_parts[0]
            end_w = intensity_parts[1] if len(intensity_parts) > 1 else start_w
            
            if 'ramp' in step_string.lower():
                avg_w = (start_w + end_w) / 2.0
            else:
                avg_w = start_w
            return avg_w * duration_sec / 1000.0
        else: # mode == 'TSS'
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

def build_workout_from_template(target_load, template, workout_date, tss_details, goals_config, current_ctl, current_atl, days_to_target, part_num=None, total_parts=None, mode='TSS'):
    """Builds a workout object, including a detailed HTML rationale."""
    
    workout_datetime = datetime.combine(workout_date, time(9, 0))
    if part_num and part_num > 1:
        workout_datetime += timedelta(hours=10)

    name_prefix = config['operational_settings'].get("workout_name_prefix")
    workout_name = template['name']
    if name_prefix and name_prefix.strip():
        workout_name = f"{name_prefix.strip()} {workout_name}"

    workout_name = f"{round(target_load)} {workout_name}"

    if total_parts and total_parts > 1:
        workout_name += f" ({part_num}/{total_parts})"
    
    # Workout Step Generation
    fixed_load = 0
    variable_step_line = ""
    for line in template['description'].split('\n'):
        if '{{ DURATION }}' in line:
            variable_step_line = line
        else:
            fixed_load += _calculate_load_for_step(line, mode)
    
    load_for_variable_part = target_load - fixed_load
    final_description = ""

    if variable_step_line:
        if mode == 'kJ':
            intensity_match = re.search(r'(\d{1,4})w', variable_step_line.lower())
            main_set_watts = int(intensity_match.group(1)) if intensity_match else 0
            main_set_duration_min = 0
            if load_for_variable_part > 0 and main_set_watts > 0:
                duration_sec = load_for_variable_part * 1000 / main_set_watts
                main_set_duration_min = round(duration_sec / 60)
        else:
            intensity_match = re.search(r'(\d{1,3})%', variable_step_line)
            main_set_pct = int(intensity_match.group(1)) / 100.0 if intensity_match else 0
            main_set_duration_min = 0
            if load_for_variable_part > 0 and main_set_pct > 0:
                main_set_if_squared = main_set_pct**2
                main_set_duration_hr = load_for_variable_part / (main_set_if_squared * 100)
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

    days_to_target_html = ""
    if days_to_target != -1:
        days_to_target_html = f"""
    <tr>
        <td>Target CTL:</td>
        <td>{days_to_target} days away</td>
    </tr>"""

    limits_html = f"""
    <tr>
        <td>Target Ramp Rate: </td>
        <td>{tss_details['target_ramp_rate']:.1f} / wk</td>
    </tr>
    <tr>
        <td>Target TSB: </td>
        <td>{tss_details['target_tsb']:.1f}</td>
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
        <td>Load limit from Ramp Rate: </td>
        <td>{tss_details['tss_for_ramp_goal']:.1f}</td>
    </tr>
    <tr>
        <td>Load limit from TSB: </td>
        <td>{tss_details['tss_for_tsb_goal']:.1f}</td>
    </tr>"""

    rationale_string = f"""
<h3>Auto-Plan Rationale ({mode})</h3>
<table>
    <style>
        td:first-child {{
            padding-right: 5px; text-align: right;
        }}
    </style>{split_info_html}{limits_html}
    <tr>
        <td>Final {mode} target: </td>
        <td>{tss_details['final_tss']:.1f} ({tss_details['reason']})</td>
    </tr>{days_to_target_html}
</table>"""

    final_description = f"{final_description}\n{rationale_string}"

    return {
        "category": "WORKOUT", "type": "Ride",
        "name": workout_name,
        "start_date_local": workout_datetime.isoformat(),
        "description": final_description,
        "load": round(target_load)
    }

# ==============================================================================
# --- MAIN HANDLER (Unchanged) ---
# ==============================================================================
def main_handler(event, context):
    """Main entry point for the GitHub Action."""
    print("--- Daily Training Plan Script v1.4.0 Initialized ---")
    
    global config
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
    mode = config['operational_settings'].get('calculation_mode', 'TSS')

    print(f"Fetching current state for user's local date: {today.isoformat()} ({user_timezone_str}) in {mode} mode")
    if mode == 'kJ':
        state = api.get_historical_kj_state(for_date=today)
    else:
        state = api.get_current_state(for_date=today)
        
    if not state: print("Halting script due to API error."); return
    
    current_ctl, current_atl = state['ctl'], state['atl']
    print(f"Current State -> CTL: {current_ctl:.2f}, ATL: {current_atl:.2f}")

    days_to_target = estimate_days_to_target(current_ctl, current_atl, config['training_goals'])
    print(f"Estimation -> Days to reach target CTL: {days_to_target if days_to_target != -1 else 'N/A'}")

    total_target_load_details = calculate_next_day_tss(current_ctl, current_atl, config['training_goals'])
    total_target_load = total_target_load_details['final_tss']
    print(f"Calculation -> Gross Target {mode} for tomorrow: {total_target_load:.2f} ({total_target_load_details['reason']})")

    tomorrow = today + timedelta(days=1)

    # --- Check for existing workouts and adjust load ---
    existing_workouts = api.get_events(tomorrow, tomorrow)
    existing_load = 0
    for workout in existing_workouts:
        if not workout.get("start_date_local", "").startswith(tomorrow.isoformat()): continue
        
        # Check explicit joules / load depending on mode
        if mode == 'kJ':
            w_load = workout.get('joules')
            if w_load is not None:
                existing_load += w_load / 1000.0
            else:
                # Fallback to estimate from description or workout_doc
                workout_doc = workout.get('workout_doc')
                if workout_doc and workout_doc.get('average_watts') and workout_doc.get('duration'):
                    existing_load += (workout_doc['average_watts'] * workout_doc['duration']) / 1000.0
                elif workout.get('description'):
                    desc_load = sum(_calculate_load_for_step(line, mode) for line in workout['description'].split('\n'))
                    existing_load += desc_load
        else: # TSS
            w_load = workout.get('icu_training_load')
            if w_load is not None:
                existing_load += w_load
            elif workout.get('description'):
                desc_load = sum(_calculate_load_for_step(line, mode) for line in workout['description'].split('\n'))
                existing_load += desc_load

    if existing_load > 0:
        print(f"Adjustment -> Found {existing_load:.0f} {mode} already planned for {tomorrow.isoformat()}.")
        total_target_load = max(0, total_target_load - existing_load)
        print(f"Adjustment -> Net Target {mode} for generated workout(s): {total_target_load:.2f}")
    # --- End New ---

    day_name = tomorrow.strftime('%A').lower()
    day_plan = config['weekly_schedule'].get(day_name, config['weekly_schedule']['default'])

    workouts_to_create = []
    
    if isinstance(day_plan, str) and '*' in day_plan:
        template_name, _, count = day_plan.partition('*')
        template_name = template_name.strip()
        num_workouts = int(count.strip())
        if num_workouts > 0 and template_name in config['workout_templates']:
            load_per_workout = total_target_load / num_workouts
            print(f"Planning {num_workouts} workouts with evenly split {mode} of {load_per_workout:.1f} each.")
            for i in range(num_workouts):
                workouts_to_create.append(build_workout_from_template(
                    load_per_workout, config['workout_templates'][template_name], tomorrow, 
                    total_target_load_details, config['training_goals'], current_ctl, current_atl, days_to_target, i + 1, num_workouts, mode
                ))
    elif isinstance(day_plan, list):
        if len(day_plan) == 1:
            template_name = day_plan[0]
            if template_name in config['workout_templates']:
                print(f"Planning 1 workout with total {mode} of {total_target_load:.1f}.")
                workouts_to_create.append(build_workout_from_template(
                    total_target_load, config['workout_templates'][template_name], tomorrow,
                    total_target_load_details, config['training_goals'], current_ctl, current_atl, days_to_target, None, None, mode
                ))
        elif len(day_plan) > 1:
            # For double days, check if workouts already exist.
            # If they do, assume they are the first part of the double.
            # The script will then only create the second part with the remaining load.
            if existing_load > 0:
                variable_template_name = day_plan[1]
                if variable_template_name in config['workout_templates']:
                    print(f"Adjustment -> Assuming existing workout is part 1 of 2. Planning part 2 ('{variable_template_name}') with remaining {total_target_load:.1f} {mode}.")
                    workouts_to_create.append(build_workout_from_template(
                        total_target_load, # Use the already-adjusted total load
                        config['workout_templates'][variable_template_name],
                        tomorrow,
                        total_target_load_details,
                        config['training_goals'],
                        current_ctl,
                        current_atl,
                        days_to_target,
                        part_num=2,
                        total_parts=2,
                        mode=mode
                    ))
            # If no workouts exist, create both from scratch.
            else:
                fixed_template_name = day_plan[0]
                if fixed_template_name in config['workout_templates']:
                    fixed_template = config['workout_templates'][fixed_template_name]
                    fixed_load_val = sum(_calculate_load_for_step(line, mode) for line in fixed_template['description'].split('\n'))
                    print(f"Planning a double day. Fixed workout '{fixed_template_name}' contributes {fixed_load_val:.1f} {mode}.")
                    workouts_to_create.append(build_workout_from_template(
                        fixed_load_val, fixed_template, tomorrow, 
                        total_target_load_details, config['training_goals'], current_ctl, current_atl, days_to_target, 1, len(day_plan), mode
                    ))
                    remaining_load = total_target_load - fixed_load_val
                    variable_template_name = day_plan[1]
                    if variable_template_name in config['workout_templates']:
                        print(f"Variable workout '{variable_template_name}' will target remaining {remaining_load:.1f} {mode}.")
                        workouts_to_create.append(build_workout_from_template(
                            remaining_load, config['workout_templates'][variable_template_name], tomorrow,
                            total_target_load_details, config['training_goals'], current_ctl, current_atl, days_to_target, 2, len(day_plan), mode
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
        for w in workouts_to_create:
            print(json.dumps(w, indent=2))
    
    print("--- Script Finished ---")
    return "OK"

if __name__ == "__main__":
    main_handler(None, None)