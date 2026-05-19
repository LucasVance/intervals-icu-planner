# filename: main.py

import requests
import json
import os
import re
import math
from datetime import date, timedelta, datetime, time
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from typing import Dict, List, Any, Optional, Tuple, Union

# Global config variable loaded at runtime
config: Dict[str, Any] = {}

# ==============================================================================
# --- API CLIENT ---
# ==============================================================================
class IntervalsAPI:
    """A client to interact with the Intervals.icu API."""
    BASE_URL: str = "https://intervals.icu"

    def __init__(self, athlete_id: str, api_key: str) -> None:
        """Initializes the IntervalsAPI client with authentication details.

        Args:
            athlete_id: The unique ID of the athlete.
            api_key: The developer API key from Intervals.icu.

        Raises:
            ValueError: If credentials are missing.
        """
        if not athlete_id or not api_key:
            raise ValueError("API credentials (ATHLETE_ID, API_KEY) not found in environment variables.")
        self.auth: Tuple[str, str] = ("API_KEY", api_key)
        self.athlete_url: str = f"{self.BASE_URL}/api/v1/athlete/{athlete_id}"

    def get_current_state(self, for_date: date) -> Optional[Dict[str, float]]:
        """Queries the native Intervals.icu wellness API for CTL and ATL on a date.

        Args:
            for_date: The date to fetch CTL/ATL state for.

        Returns:
            A dictionary containing 'ctl' and 'atl' values, or None if the request failed.
        """
        date_str: str = for_date.isoformat()
        url: str = f"{self.athlete_url}/wellness/{date_str}"
        try:
            response = requests.get(url, auth=self.auth, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data.get('ctl') is None or data.get('atl') is None:
                return None
            return {"ctl": float(data.get('ctl')), "atl": float(data.get('atl'))}
        except requests.exceptions.RequestException as e:
            print(f"ERROR: Could not connect to Intervals.icu API: {e}")
            return None
        except json.JSONDecodeError:
            print("ERROR: Could not decode JSON response from API.")
            return None

    def get_historical_kj_state(self, for_date: date) -> Optional[Dict[str, float]]:
        """Calculates CTL and ATL locally in mechanical kJ using 365 days of activity history.

        Args:
            for_date: The start-of-day date to compute historical values for.

        Returns:
            A dictionary containing calculated 'ctl' and 'atl' values, or None if the request failed.
        """
        start_str: str = (for_date - timedelta(days=365)).isoformat()
        url: str = f"{self.athlete_url}/activities?oldest={start_str}"
        try:
            response = requests.get(url, auth=self.auth, timeout=10)
            response.raise_for_status()
            activities: List[Dict[str, Any]] = response.json()
            
            # Deduplicate activities starting within the same minute (e.g., duplicate Garmin/Strava syncs)
            deduped: Dict[str, Dict[str, Any]] = {}
            for act in activities:
                if 'start_date_local' in act:
                    minute_key: str = act['start_date_local'][:16]  # YYYY-MM-DDTHH:MM
                    existing = deduped.get(minute_key)
                    if not existing:
                        deduped[minute_key] = act
                    else:
                        # Prefer the activity with actual work/load data
                        existing_score: float = float(existing.get('icu_joules') or 0) + float(existing.get('icu_training_load') or 0)
                        new_score: float = float(act.get('icu_joules') or 0) + float(act.get('icu_training_load') or 0)
                        if new_score > existing_score:
                            deduped[minute_key] = act

            daily_kj: Dict[str, float] = {}
            for act in deduped.values():
                if 'start_date_local' in act:
                    d_str: str = act['start_date_local'][:10]
                    joules: float = float(act.get('icu_joules') or 0)
                    daily_kj[d_str] = daily_kj.get(d_str, 0.0) + (joules / 1000.0)
            
            ctl: float = 0.0
            atl: float = 0.0
            c: float = float(config['training_goals']['ctl_days'])
            a: float = float(config['training_goals']['atl_days'])
            
            # Constants for continuous exponential decay matching Intervals.icu
            kc: float = math.exp(-1.0 / c)
            ka: float = math.exp(-1.0 / a)
            
            strava_warning: bool = False
            for i in range(365, -1, -1):
                d: date = for_date - timedelta(days=i)
                d_str = d.isoformat()
                kj: float = daily_kj.get(d_str, 0.0)
                
                # Check for hidden Strava load
                if kj == 0 and any(act.get('start_date_local', '').startswith(d_str) and act.get('source') == 'STRAVA' for act in activities):
                    strava_warning = True

                ctl = ctl * kc + kj * (1.0 - kc)
                atl = atl * ka + kj * (1.0 - ka)
            
            if strava_warning:
                print("\nWARNING: Some historical activities were synced via Strava. Strava's API terms often hide kJ data from 3rd-party scripts, which may cause your calculated Fitness/Fatigue to be lower than the Intervals.icu charts.\n")
            
            return {"ctl": ctl, "atl": atl}
        except Exception as e:
            print(f"ERROR: Could not fetch historical activities for kJ calculation: {e}")
            return None

    def create_workout(self, workout_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Creates a planned workout event on the athlete's Intervals.icu calendar.

        Args:
            workout_data: The workout structure details.

        Returns:
            The server's response JSON, or None if the request failed.
        """
        url: str = f"{self.athlete_url}/events"
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

    def get_events(self, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """Fetches calendar events/workouts planned in a specified range.

        Args:
            start_date: Start date of range (inclusive).
            end_date: End date of range (inclusive).

        Returns:
            A list of dictionary structures representing planned events.
        """
        start_str: str = start_date.isoformat()
        end_str: str = end_date.isoformat()
        url: str = f"{self.athlete_url}/events?oldest={start_str}&newest={end_str}"
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
# --- CALCULATION ENGINE ---
# ==============================================================================
def calculate_next_day_tss(current_ctl: float, current_atl: float, goals_config: Dict[str, Any]) -> Dict[str, Any]:
    """Calculates target TSS/load using mathematical parity between TSB and Ramp Rate bounds.

    Args:
        current_ctl: The athlete's current Chronic Training Load.
        current_atl: The athlete's current Acute Training Load.
        goals_config: Configuration dictionary for training goals.

    Returns:
        A dictionary containing the final calculated load target and boundary constraints.
    """
    # Get the configured time constants.
    c: float = float(goals_config.get('ctl_days', 42))
    a: float = float(goals_config.get('atl_days', 7))

    # Decay constants
    kc: float = math.exp(-1.0 / c)
    ka: float = math.exp(-1.0 / a)

    # Determine targets with auto-calibration
    if 'target_ramp_rate' in goals_config:
        target_ramp_rate: float = float(goals_config['target_ramp_rate'])
        # Convert Ramp Rate to equivalent TSB target using continuous formula
        target_tsb: float = target_ramp_rate * (ka - kc) / (7.0 * (1.0 - ka) * (1.0 - kc))
    elif 'target_tsb' in goals_config:
        target_tsb = float(goals_config['target_tsb'])
        # Convert TSB to equivalent Ramp Rate target using continuous formula
        target_ramp_rate = target_tsb * 7.0 * (1.0 - ka) * (1.0 - kc) / (ka - kc)
    else:
        # Default fallback (e.g. Ramp Rate of 40.0 / wk)
        target_ramp_rate = 40.0
        target_tsb = target_ramp_rate * (ka - kc) / (7.0 * (1.0 - ka) * (1.0 - kc))

    # 1. Ramp Rate Bound (Prevents CTL Spikes)
    daily_ramp: float = target_ramp_rate / 7.0
    tss_for_ramp_goal: float = current_ctl + (daily_ramp / (1.0 - kc))

    # 2. TSB Bound (Gauges Freshness)
    numerator: float = target_tsb - (current_ctl * kc) + (current_atl * ka)
    denominator: float = ka - kc
    tss_for_tsb_goal: float = numerator / denominator if denominator != 0 else 0.0

    # 3. Apply Dual Bounds
    final_tss: float = min(tss_for_ramp_goal, tss_for_tsb_goal)
    final_tss = max(0.0, final_tss)

    # Determine active driver
    reason: str = "Ramp Rate Driven" if tss_for_ramp_goal <= tss_for_tsb_goal else "TSB Driven"

    return {
        "final_tss": final_tss,
        "tss_for_ramp_goal": tss_for_ramp_goal,
        "tss_for_tsb_goal": tss_for_tsb_goal,
        "reason": reason,
        "target_ramp_rate": target_ramp_rate,
        "target_tsb": target_tsb
    }


def estimate_days_to_target(start_ctl: float, start_atl: float, goals_config: Dict[str, Any]) -> int:
    """Performs a quick daily simulation to estimate days to reach target CTL.

    Args:
        start_ctl: Start Chronic Training Load.
        start_atl: Start Acute Training Load.
        goals_config: Configuration dictionary for training goals.

    Returns:
        Number of days needed to reach target CTL, or -1 if unreachable within max window.
    """
    ctl_current: float = start_ctl
    atl_current: float = start_atl
    target_ctl: float = float(goals_config.get('target_ctl', 999))

    # Use the same constants as the main calculation
    c: float = float(goals_config.get('ctl_days', 42))
    a: float = float(goals_config.get('atl_days', 7))
    
    # Continuous exponential decay constants
    kc: float = math.exp(-1.0 / c)
    ka: float = math.exp(-1.0 / a)

    if ctl_current >= target_ctl:
        return 0

    for days_out in range(1, 365 * 3):  # Max 3 year projection
        tss_details: Dict[str, Any] = calculate_next_day_tss(ctl_current, atl_current, goals_config)
        tss_needed: float = tss_details['final_tss']
        
        atl_current = (atl_current * ka) + (tss_needed * (1.0 - ka))
        ctl_current = (ctl_current * kc) + (tss_needed * (1.0 - kc))

        if ctl_current >= target_ctl:
            return days_out
    
    return -1


# ==============================================================================
# --- WORKOUT BUILDER ---
# ==============================================================================
def _calculate_load_for_step(step_string: str, mode: str = 'TSS') -> float:
    """Calculates the absolute load (TSS/kJ) for a single workout step.

    Args:
        step_string: The single step string line from template description.
        mode: The calculation mode ('TSS' or 'kJ').

    Returns:
        The calculated numerical load for the single workout step.
    """
    try:
        duration_match = re.search(r'(\d+)\s*m', step_string)
        if not duration_match:
            return 0.0
        duration_min: int = int(duration_match.group(1))
        
        if mode == 'kJ':
            duration_sec: int = duration_min * 60
            intensity_parts: List[int] = [int(p) for p in re.findall(r'(\d+)w', step_string.lower())]
            if not intensity_parts:
                return 0.0
            start_w: int = intensity_parts[0]
            end_w: int = intensity_parts[1] if len(intensity_parts) > 1 else start_w
            
            if 'ramp' in step_string.lower():
                avg_w: float = (start_w + end_w) / 2.0
            else:
                avg_w = float(start_w)
            return avg_w * duration_sec / 1000.0
        else:  # mode == 'TSS'
            duration_hr: float = duration_min / 60.0
            intensity_parts = [int(p) for p in re.findall(r'(\d+)%', step_string)]
            if not intensity_parts:
                return 0.0
            start_pct: float = intensity_parts[0] / 100.0
            end_pct: float = intensity_parts[1] / 100.0 if len(intensity_parts) > 1 else start_pct
            if 'ramp' in step_string.lower():
                if_squared: float = ((start_pct**2) + (end_pct**2)) / 2.0
            else:
                if_squared = start_pct**2
            return if_squared * duration_hr * 100.0
    except (ValueError, IndexError):
        return 0.0


def build_workout_from_template(
    target_load: float,
    template: Dict[str, Any],
    workout_date: date,
    tss_details: Dict[str, Any],
    goals_config: Dict[str, Any],
    current_ctl: float,
    current_atl: float,
    days_to_target: int,
    part_num: Optional[int] = None,
    total_parts: Optional[int] = None,
    mode: str = 'TSS'
) -> Dict[str, Any]:
    """Assembles a planned workout event structure with consolidated rationale HTML.

    Args:
        target_load: Net training load to program for the workout.
        template: Dictionary describing the target workout template.
        workout_date: The local date to schedule the workout.
        tss_details: Training target engine output details.
        goals_config: Active training goals config block.
        current_ctl: Current Chronic Training Load.
        current_atl: Current Acute Training Load.
        days_to_target: Estimated days remaining to reach CTL goal.
        part_num: Specific segment number for double-day workouts.
        total_parts: Total planned workouts for double-day workouts.
        mode: Calculation mode ('TSS' or 'kJ').

    Returns:
        Structured event dictionary prepared for upload to calendar.
    """
    workout_datetime: datetime = datetime.combine(workout_date, time(9, 0))
    if part_num and part_num > 1:
        workout_datetime += timedelta(hours=10)

    name_prefix: Optional[str] = config['operational_settings'].get("workout_name_prefix")
    workout_name: str = template['name']
    if name_prefix and name_prefix.strip():
        workout_name = f"{name_prefix.strip()} {workout_name}"

    workout_name = f"{round(target_load)} {workout_name}"

    if total_parts and total_parts > 1:
        workout_name += f" ({part_num}/{total_parts})"
    
    # Workout Step Generation
    fixed_load: float = 0.0
    variable_step_line: str = ""
    for line in template['description'].split('\n'):
        if '{{ DURATION }}' in line:
            variable_step_line = line
        else:
            fixed_load += _calculate_load_for_step(line, mode)
    
    load_for_variable_part: float = target_load - fixed_load
    final_description: str = ""

    if variable_step_line:
        main_set_duration_min: int = 0
        if mode == 'kJ':
            intensity_match = re.search(r'(\d{1,4})w', variable_step_line.lower())
            main_set_watts: int = int(intensity_match.group(1)) if intensity_match else 0
            if load_for_variable_part > 0 and main_set_watts > 0:
                duration_sec: float = load_for_variable_part * 1000.0 / main_set_watts
                main_set_duration_min = round(duration_sec / 60.0)
        else:
            intensity_match = re.search(r'(\d{1,3})%', variable_step_line)
            main_set_pct: float = int(intensity_match.group(1)) / 100.0 if intensity_match else 0.0
            if load_for_variable_part > 0 and main_set_pct > 0:
                main_set_if_squared: float = main_set_pct**2
                main_set_duration_hr: float = load_for_variable_part / (main_set_if_squared * 100.0)
                main_set_duration_min = round(main_set_duration_hr * 60.0)
                
        variable_line_final: str = variable_step_line.replace('{{ DURATION }}', f'{main_set_duration_min}m')
        final_description = template['description'].replace(variable_step_line, variable_line_final)
    else:
        final_description = template['description']

    # --- Rationale Generation ---
    split_info_html: str = ""
    if total_parts and total_parts > 1:
        split_info_html = f"""
    <tr>
        <td>Split:</td>
        <td>Part {part_num} of {total_parts}</td>
    </tr>"""

    days_to_target_html: str = ""
    if days_to_target != -1:
        days_to_target_html = f"""
    <tr>
        <td>Target CTL:</td>
        <td>{days_to_target} days away</td>
    </tr>"""

    limits_html: str = f"""
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

    rationale_string: str = f"""
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
# --- MODULAR HANDLER HELPERS ---
# ==============================================================================
def load_config(config_path: str = "config.json") -> Dict[str, Any]:
    """Loads and parses the global training planning configuration file.

    Args:
        config_path: The file system path to config.json.

    Returns:
        The loaded and parsed configuration dictionary.

    Raises:
        FileNotFoundError: If the configuration file is missing.
    """
    with open(config_path) as f:
        return json.load(f)


def get_local_today(config_data: Dict[str, Any]) -> Tuple[date, ZoneInfo]:
    """Determines today's date adjusted to the athlete's configured timezone.

    Args:
        config_data: The configuration dictionary.

    Returns:
        A tuple of (today's date in local timezone, ZoneInfo object).
    """
    try:
        user_timezone_str: str = config_data['operational_settings']['timezone']
        user_timezone: ZoneInfo = ZoneInfo(user_timezone_str)
        today: date = datetime.now(user_timezone).date()
        return today, user_timezone
    except (KeyError, ZoneInfoNotFoundError):
        print("ERROR: Invalid or missing timezone. Using UTC timezone fallback.")
        return date.today(), ZoneInfo("UTC")


def get_api_credentials() -> Tuple[str, str]:
    """Safely extracts athlete credentials from environment variables.

    Returns:
        A tuple of (athlete_id, api_key).

    Raises:
        KeyError: If one of the secret credentials variables is missing.
    """
    athlete_id: str = os.environ['ATHLETE_ID']
    api_key: str = os.environ['API_KEY']
    return athlete_id, api_key


def calculate_existing_load(api: IntervalsAPI, tomorrow: date, mode: str) -> float:
    """Queries calendar events for tomorrow and sums the load of already planned workouts.

    Args:
        api: The authenticated IntervalsAPI client.
        tomorrow: Tomorrow's local date.
        mode: Training calculation mode ('TSS' or 'kJ').

    Returns:
        The accumulated training load already scheduled for tomorrow.
    """
    existing_workouts: List[Dict[str, Any]] = api.get_events(tomorrow, tomorrow)
    existing_load: float = 0.0
    for workout in existing_workouts:
        if not workout.get("start_date_local", "").startswith(tomorrow.isoformat()):
            continue
        
        # Check explicit load depending on calculation mode
        if mode == 'kJ':
            w_load: Optional[float] = workout.get('joules')
            if w_load is not None:
                existing_load += w_load / 1000.0
            else:
                # Fallback to estimate from workout document or description text
                workout_doc = workout.get('workout_doc')
                if workout_doc and workout_doc.get('average_watts') and workout_doc.get('duration'):
                    existing_load += (workout_doc['average_watts'] * workout_doc['duration']) / 1000.0
                elif workout.get('description'):
                    desc_load: float = sum(_calculate_load_for_step(line, mode) for line in workout['description'].split('\n'))
                    existing_load += desc_load
        else:  # TSS
            w_load_tss: Optional[float] = workout.get('icu_training_load')
            if w_load_tss is not None:
                existing_load += w_load_tss
            elif workout.get('description'):
                desc_load_tss: float = sum(_calculate_load_for_step(line, mode) for line in workout['description'].split('\n'))
                existing_load += desc_load_tss
    return existing_load


def schedule_workouts(
    config_data: Dict[str, Any],
    tomorrow: date,
    mode: str,
    total_target_load: float,
    total_target_load_details: Dict[str, Any],
    current_ctl: float,
    current_atl: float,
    days_to_target: int,
    existing_load: float
) -> List[Dict[str, Any]]:
    """Builds and schedules workouts based on weekly schedules and remaining load.

    Args:
        config_data: The configuration dictionary.
        tomorrow: The scheduling date (tomorrow).
        mode: Training calculation mode ('TSS' or 'kJ').
        total_target_load: Net load needed to reach target after subtracting existing workouts.
        total_target_load_details: Output calculation parameters dictionary.
        current_ctl: Current Chronic Training Load.
        current_atl: Current Acute Training Load.
        days_to_target: Projection of days to reach target CTL.
        existing_load: Training load already planned.

    Returns:
        List of workouts structured for upload.
    """
    day_name: str = tomorrow.strftime('%A').lower()
    day_plan: Union[str, List[str]] = config_data['weekly_schedule'].get(day_name, config_data['weekly_schedule']['default'])
    workouts_to_create: List[Dict[str, Any]] = []

    # Multi-workout multiplication pattern (e.g., "endurance * 2")
    if isinstance(day_plan, str) and '*' in day_plan:
        template_name, _, count = day_plan.partition('*')
        template_name = template_name.strip()
        num_workouts: int = int(count.strip())
        if num_workouts > 0 and template_name in config_data['workout_templates']:
            load_per_workout: float = total_target_load / num_workouts
            print(f"Planning {num_workouts} workouts with evenly split {mode} of {load_per_workout:.1f} each.")
            for i in range(num_workouts):
                workouts_to_create.append(build_workout_from_template(
                    load_per_workout, config_data['workout_templates'][template_name], tomorrow, 
                    total_target_load_details, config_data['training_goals'], current_ctl, current_atl, days_to_target, i + 1, num_workouts, mode
                ))
    elif isinstance(day_plan, list):
        if len(day_plan) == 1:
            template_name = day_plan[0]
            if template_name in config_data['workout_templates']:
                print(f"Planning 1 workout with total {mode} of {total_target_load:.1f}.")
                workouts_to_create.append(build_workout_from_template(
                    total_target_load, config_data['workout_templates'][template_name], tomorrow,
                    total_target_load_details, config_data['training_goals'], current_ctl, current_atl, days_to_target, None, None, mode
                ))
        elif len(day_plan) > 1:
            # Double-day workout dispatch
            if existing_load > 0:
                variable_template_name: str = day_plan[1]
                if variable_template_name in config_data['workout_templates']:
                    print(f"Adjustment -> Assuming existing workout is part 1 of 2. Planning part 2 ('{variable_template_name}') with remaining {total_target_load:.1f} {mode}.")
                    workouts_to_create.append(build_workout_from_template(
                        total_target_load,
                        config_data['workout_templates'][variable_template_name],
                        tomorrow,
                        total_target_load_details,
                        config_data['training_goals'],
                        current_ctl,
                        current_atl,
                        days_to_target,
                        part_num=2,
                        total_parts=2,
                        mode=mode
                    ))
            else:
                fixed_template_name: str = day_plan[0]
                if fixed_template_name in config_data['workout_templates']:
                    fixed_template = config_data['workout_templates'][fixed_template_name]
                    fixed_load_val: float = sum(_calculate_load_for_step(line, mode) for line in fixed_template['description'].split('\n'))
                    print(f"Planning a double day. Fixed workout '{fixed_template_name}' contributes {fixed_load_val:.1f} {mode}.")
                    workouts_to_create.append(build_workout_from_template(
                        fixed_load_val, fixed_template, tomorrow, 
                        total_target_load_details, config_data['training_goals'], current_ctl, current_atl, days_to_target, 1, len(day_plan), mode
                    ))
                    remaining_load: float = total_target_load - fixed_load_val
                    variable_template_name = day_plan[1]
                    if variable_template_name in config_data['workout_templates']:
                        print(f"Variable workout '{variable_template_name}' will target remaining {remaining_load:.1f} {mode}.")
                        workouts_to_create.append(build_workout_from_template(
                            remaining_load, config_data['workout_templates'][variable_template_name], tomorrow,
                            total_target_load_details, config_data['training_goals'], current_ctl, current_atl, days_to_target, 2, len(day_plan), mode
                        ))
    return workouts_to_create


def upload_or_log_workouts(api: IntervalsAPI, config_data: Dict[str, Any], workouts: List[Dict[str, Any]]) -> None:
    """Isolates the network upload requests or CLI logging for dry runs.

    Args:
        api: The authenticated IntervalsAPI client.
        config_data: Global configuration dictionary.
        workouts: Structured list of planned workouts to create.
    """
    print("-" * 20)
    if config_data['operational_settings'].get('live_mode', False):
        if workouts:
            print(f"LIVE MODE IS ON. Uploading {len(workouts)} workout(s) to Intervals.icu...")
            for workout in workouts:
                if workout and workout.get("load", 0) > 0:
                    api.create_workout(workout)
        else:
            print("LIVE MODE IS ON, but no workouts were generated for the plan.")
    else:
        print(f"DRY RUN MODE IS ON. Would have created {len(workouts)} workout(s).")
        for w in workouts:
            print(json.dumps(w, indent=2))


# ==============================================================================
# --- MAIN ORCHESTRATOR HANDLER ---
# ==============================================================================
def main_handler(event: Any, context: Any) -> str:
    """Main orchestrator function acting as entry point for GitHub Action.

    Args:
        event: GitHub / AWS event details context structure.
        context: Execution environment context details.

    Returns:
        Status code indicator ('OK' or halts early on errors).
    """
    print("--- Daily Training Plan Script v1.4.0 Initialized ---")
    
    global config
    try:
        config = load_config()
    except Exception as e:
        print(f"ERROR: Could not load config.json: {e}")
        return "ERROR"

    today, user_timezone = get_local_today(config)

    try:
        athlete_id, api_key = get_api_credentials()
    except KeyError as e:
        print(f"ERROR: Missing secret environment variable: {e}")
        return "ERROR"

    api = IntervalsAPI(athlete_id, api_key)
    mode: str = config['operational_settings'].get('calculation_mode', 'TSS')

    print(f"Fetching current state for user's local date: {today.isoformat()} ({user_timezone}) in {mode} mode")
    if mode == 'kJ':
        state = api.get_historical_kj_state(for_date=today)
    else:
        state = api.get_current_state(for_date=today)
        
    if not state:
        print("Halting script due to API error.")
        return "ERROR"
    
    current_ctl: float = state['ctl']
    current_atl: float = state['atl']
    print(f"Current State -> CTL: {current_ctl:.2f}, ATL: {current_atl:.2f}")

    days_to_target: int = estimate_days_to_target(current_ctl, current_atl, config['training_goals'])
    print(f"Estimation -> Days to reach target CTL: {days_to_target if days_to_target != -1 else 'N/A'}")

    total_target_load_details: Dict[str, Any] = calculate_next_day_tss(current_ctl, current_atl, config['training_goals'])
    total_target_load: float = total_target_load_details['final_tss']
    print(f"Calculation -> Gross Target {mode} for tomorrow: {total_target_load:.2f} ({total_target_load_details['reason']})")

    tomorrow: date = today + timedelta(days=1)
    existing_load: float = calculate_existing_load(api, tomorrow, mode)

    net_target_load: float = total_target_load
    if existing_load > 0:
        print(f"Adjustment -> Found {existing_load:.0f} {mode} already planned for {tomorrow.isoformat()}.")
        net_target_load = max(0.0, total_target_load - existing_load)
        print(f"Adjustment -> Net Target {mode} for generated workout(s): {net_target_load:.2f}")

    workouts: List[Dict[str, Any]] = schedule_workouts(
        config_data=config,
        tomorrow=tomorrow,
        mode=mode,
        total_target_load=net_target_load,
        total_target_load_details=total_target_load_details,
        current_ctl=current_ctl,
        current_atl=current_atl,
        days_to_target=days_to_target,
        existing_load=existing_load
    )

    upload_or_log_workouts(api, config, workouts)
    
    print("--- Script Finished ---")
    return "OK"


if __name__ == "__main__":
    main_handler(None, None)