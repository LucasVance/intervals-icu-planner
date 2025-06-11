# Automated training planner for Intervals.icu

This repository contains a Python script that automatically generates a daily training plan based on your long-term fitness goals and syncs it as a structured workout to your [Intervals.icu](https://intervals.icu) calendar.

The script runs automatically every day using GitHub Actions, creating a dynamic feedback loop: it reads your current fitness state, calculates the precise load needed for the next day, and populates your calendar so you always know what's next.

## Core concepts

This planner is built on the well-established principles of training load management, with a key custom metric for controlling daily intensity.

-   **CTL (Chronic Training Load):** A proxy for your overall fitness, based on a long-term (42-day) weighted average of your training load.
-   **ATL (Acute Training Load):** A proxy for your fatigue, based on a short-term (7-day) weighted average.
-   **TSB (Training Stress Balance):** Calculated as `CTL - ATL`, this represents your "form" or "freshness." A negative TSB is typical during a build phase. This script aims to hold your TSB at a specific target level.
-   **ALB (Acute Load Balance):** A metric defined as `ATL (from previous day) - Daily TSS`. This acts as a "guard rail" to prevent excessively large single-day jumps in training stress, ensuring a smooth and sustainable progression.

## Features

-   Fetches your current fitness (CTL) and fatigue (ATL) daily from the Intervals.icu API.
-   Calculates the precise Training Stress Score (TSS) required for the next day to progress towards your goals.
-   Calculates this TSS based on two primary inputs:
    1.  A long-term **Target TSB** you want to maintain.
    2.  A limiting **ALB (Acute Load Balance)** that controls day-to-day aggressiveness.
-   Automatically generates a structured workout (a Zone 2 ride with a warm-up ramp) designed to hit the calculated TSS target.
-   Uploads the workout to your Intervals.icu calendar for the next day.
-   Designed for full automation via the included GitHub Actions workflow.

## Setup and configuration

To get this running, you'll need to configure your goals and set up the necessary secrets for the GitHub Action. Fork this repository and complete the next steps.

### 1. The `config.json` File

This file holds all the non-sensitive parameters for your training plan. Edit the values in `config.json` to match your personal goals.

```
{
  "training_goals": {
    "target_ctl": 130.0,
    "target_tsb": -25.0,
    "alb_lower_bound": -40.0
  },
  "workout_settings": {
    "power_target_pct": 0.65,
    "ramp_duration_min": 3,
    "ramp_start_pct": 0.40
  },
  "operational_settings": {
    "live_mode": true,
    "workout_name_prefix": "Auto-Plan:"
  }
}

```

-   `target_ctl`: Your ultimate long-term fitness goal.
-   `target_tsb`: The daily TSB you want to hold during your training block.
-   `alb_lower_bound`: The "floor" for daily training aggressiveness. A value of `-40` means your daily TSS is allowed to be ~47 points higher than your ATL from the previous day. A less negative number (e.g., -20) will force a more gradual progression. In my experience, -10 is a good starting point.
-   `power_target_pct`: The intensity of the main workout set (e.g., 0.65 = 65% FTP).
-   `ramp_duration_min` / `ramp_start_pct`: Parameters for the workout's warm-up ramp.
-   `live_mode`: Should be `true` for the GitHub Action to run for real.

### 2. GitHub Actions Secrets

To allow the script to securely access your Intervals.icu account, you must add your Athlete ID and API Key as "Repository secrets". They can be found at the bottom of the [intervals.icu settings](https://intervals.icu/settings) page

1.  In your GitHub repository, go to **Settings** > **Secrets and variables** > **Actions**.
2.  Click the **"New repository secret"** button.
3.  Create two secrets:
    -   **Name:** `ATHLETE_ID`
        -   **Value:** `iXXXXXX`
    -   **Name:** `API_KEY`
        -   **Value:** `YOUR_API_KEY_HERE`

### 3. GitHub Actions workflow file

This project is set up to run using the workflow file located at `.github/workflows/daily_planner.yml`. This file tells GitHub to run your script on a schedule. By default, it's set to run every night at 10 PM PST. You can change the schedule by editing the `cron` line in the file.

Here is an example of what the `daily_planner.yml` file should look like:

```
name: Run Daily Intervals.icu Planner

on:
  workflow_dispatch: # Allows manual triggering
  schedule:
    # Runs at 22:00 UTC every day.
    # Adjust the time to suit your schedule.
    - cron: '0 22 * * *'

jobs:
  build-and-run:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run the daily planner script
        env:
          ATHLETE_ID: ${{ secrets.ATHLETE_ID }}
          API_KEY: ${{ secrets.API_KEY }}
        run: python main.py

```

## How it works

The script follows a simple, robust daily cycle:

1.  **Trigger:** The GitHub Actions scheduler triggers the script at a set time every night.
2.  **Read State:** The script makes an API call to Intervals.icu to get your latest CTL and ATL values at the end of the current day.
3.  **Calculate:** Using your configured goals (`target_tsb`, `alb_lower_bound`), it calculates the precise TSS target for tomorrow.
4.  **Build Workout:** It translates this TSS target into a structured workout with a warm-up ramp and a Zone 2 main set of the correct duration.
5.  **Write to Calendar:** It makes a final API call to create this new workout on your Intervals.icu calendar for the next day.

## Local testing

If you want to test the script on your local machine before letting the automation run:

1.  Clone the repository.
    
2.  Create a Python virtual environment: `python3 -m venv .venv` and `source .venv/bin/activate`.
    
3.  Install dependencies: `pip install -r requirements.txt`.
    
4.  Temporarily set your `live_mode` to `false` in `config.json` to prevent it from uploading workouts.
    
5.  Set your secrets as local environment variables before running the script:
    
    ```
    export ATHLETE_ID="iXXXXXX"
    export API_KEY="YOUR_API_KEY_HERE"
    python main.py
    
    ```
    

## License

This project is licensed under the MIT License. See the `LICENSE` file for details
