## Why

The current strike flight logic still needs iterative tuning based on actual closed-loop run data: one successful run is not enough if takeoff, route following, strike, or landing remains unsafe, unstable, or inconsistent. We need a repeatable optimization workflow that preserves every `flight_log.csv`, analyzes each run, adjusts software-side behavior and parameters, and reruns the full ZJG-map mission until the aircraft behavior is consistently safe and controlled without touching FC params.

## What Changes

- Define an iterative optimization workflow that analyzes each generated flight log, identifies flight-behavior issues, and applies software-only tuning between full closed-loop test runs.
- Require all full closed-loop tests for this effort to run on the `zjg` map/configuration.
- Preserve every run artifact instead of overwriting outputs: each flight log must be archived as `log_1`, `log_2`, `log_3`, etc., and each analysis must be recorded as `flight_log_analysis_1.md`, `flight_log_analysis_2.md`, `flight_log_analysis_3.md`, etc.
- Define the safety and stability goals for iterative tuning, including safer takeoff and landing behavior, avoidance of dangerous or erratic flight, and reduction of behaviors that could crash the aircraft in simulation.
- Establish a rerun-and-review loop where every optimization round includes log review, conclusion capture, software tuning changes, and another full closed-loop validation.

## Capabilities

### New Capabilities
- `iterative-flight-log-analysis`: Structured analysis of each closed-loop `flight_log.csv` to identify mission-phase issues, unsafe behavior, and candidate software-side tuning changes.
- `closed-loop-run-artifact-retention`: Persistent per-run storage for flight logs and analysis reports using incrementing filenames instead of overwriting previous results.
- `software-only-flight-tuning-loop`: Repeatable optimize-and-rerun workflow that adjusts Striker software parameters or logic, reruns the full mission on `zjg`, and evaluates whether flight behavior improved.

### Modified Capabilities
- `strike-fullchain-validation`: Full closed-loop validation must support repeated optimization rounds on the `zjg` map and include success criteria tied to safe, stable takeoff, strike, and landing behavior across iterations.

## Impact

- Affected areas: flight-log generation/storage, SITL closed-loop test workflow, analysis/reporting artifacts, and software parameters or logic that influence takeoff, routing, strike, and landing behavior
- External/runtime impact: repeated SITL full-chain runs on the `zjg` map with preserved outputs for comparison across optimization rounds
- Developer/operator impact: every tuning cycle leaves an auditable history of run data, analysis conclusions, and whether the latest software changes improved or degraded mission safety
