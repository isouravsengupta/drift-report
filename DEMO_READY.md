# Demo Readiness Checklist

## Ready State

This project is ready for a functional demo now.

What is complete:
- Baseline vs candidate drift detection
- Risk scoring (high/medium/low)
- Rollback guidance generation
- Markdown and JSON report outputs
- One-command live-org run path (`run_live_demo.sh`)

## Demo Modes

### Mode A: Snapshot Demo (most reliable)

Use prepared snapshot files in `snapshots/` and run:

```bash
python3 drift_guard.py --baseline snapshots/baseline.json --current snapshots/current.json --output output
```

### Mode B: Live Org Demo (best story, environment dependent)

Authenticate org aliases with Salesforce CLI, then run:

```bash
./run_live_demo.sh <baseline_alias> <candidate_alias> DriftDemo_Perms Contact "Support Queue" DRIFT_DEMO_LABEL
```

## What to Show in Video (3-5 mins)

1. Open baseline and current snapshot inputs
2. Run the command
3. Open `output/drift-report.md`
4. Explain:
   - high-risk drifts block promotion
   - medium/low drifts are visible and trackable
   - rollback plan is auto-generated

## Suggested Talking Points

- "This is a release safety gate for Salesforce template configurations."
- "It catches accidental permission/sharing/routing drift before GA."
- "Collector is pluggable: static JSON today, org/API extraction in production."

## Known Constraints to Mention Transparently

- Extraction coverage is intentionally narrow for MVP speed.
- Real-time is implemented as on-demand command execution, not a daemon.
- Notification integrations are planned but not yet implemented.
