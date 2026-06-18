# Demo Readiness Checklist

This file helps you run a clean 3-5 minute demo without surprises.

## Current status

Ready to demo now.

Implemented:
- Snapshot comparison (baseline vs candidate)
- Drift detection (`added`, `removed`, `modified`)
- Risk scoring (`high`, `medium`, `low`)
- Release gate signal (`safe_to_promote`)
- Rollback suggestions
- JSON + markdown report generation
- One-command live flow (`run_live_demo.sh`)

## Demo mode options

### Mode A: Stable demo (recommended)

Use local snapshots:

```bash
python3 drift_guard.py --baseline snapshots/baseline.json --current snapshots/current.json --output output
```

Why use this:
- no auth dependency,
- predictable output,
- best for recorded video.

### Mode B: Live org demo

Run:

```bash
./run_live_demo.sh <baseline_alias> <candidate_alias> DriftDemo_Perms Contact "Support Queue" DRIFT_DEMO_LABEL
```

Why use this:
- stronger "real workflow" credibility.

Risk:
- depends on org authentication and environment stability.

## Script for your narration

1. "Here is the known-good baseline snapshot."
2. "Here is the candidate snapshot for release."
3. "Now I run Drift Report."
4. "The report shows high-risk drifts in permissions/sharing/routing."
5. "Since high-risk drift exists, promotion is blocked."
6. "Rollback actions are auto-generated at the end."

## Pre-demo sanity check (30 seconds)

- Confirm command runs successfully.
- Confirm `output/drift-report.md` exists.
- Open the markdown file once before recording.

## Transparent caveats (say these if asked)

- Current collector is intentionally focused on a small subset for speed.
- This is on-demand runtime, not continuous monitoring.
- Alerts/integrations (Slack/Jira) are planned next.
