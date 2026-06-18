# Template Drift Guard - 2 Hour PoC

Small PoC to detect config drift between a known-good baseline template and the current template state, then classify risk.

Related docs:
- `ARCHITECTURE.md` - architecture and component design
- `DEMO_READY.md` - demo readiness and run checklist

## What this demonstrates

- Detects **added / removed / modified** config values
- Assigns risk levels: `high`, `medium`, `low`
- Produces:
  - `output/drift-report.json`
  - `output/drift-report.md`
- Gives a simple rollback plan

## Run

From this directory:

```bash
python3 drift_guard.py \
  --baseline snapshots/baseline.json \
  --current snapshots/current.json \
  --output output
```

## Live Org Run (no manual JSON editing)

Prereq:
- Install Salesforce CLI (`sf`)
- Authenticate both orgs first (`sf org login web --alias <alias>`)

One command:

```bash
./run_live_demo.sh <baseline_org_alias> <candidate_org_alias> [permission_set_label] [sharing_object] [queue_name] [label_name]
```

Example:

```bash
./run_live_demo.sh baseline candidate DriftDemo_Perms Contact "Support Queue" DRIFT_DEMO_LABEL
```

This command:
- Exports baseline snapshot from org alias 1 (`export_snapshot.py`)
- Exports candidate snapshot from org alias 2 (`export_snapshot.py`)
- Runs drift comparison (`drift_guard.py`)
- Produces `output/drift-report.md` and `output/drift-report.json`

### What `export_snapshot.py` currently reads

- `features`: org-level Einstein analytics + sandbox flag
- `permissions`: object permissions from one permission set label (Account/Contact/Case)
- `sharing`: sharing model for one object (default `Contact`)
- `routing`: presence/dev name for one queue (default `Support Queue`)
- `labels`: one custom label value (default `DRIFT_DEMO_LABEL`)

If any query does not match your org setup, the script keeps running and writes empty/default values for that section.

## Demo script (3 minutes)

1. Open `snapshots/baseline.json` and `snapshots/current.json`
2. Point out intentional drift:
   - Gen AI toggles changed
   - Permission changed (`sales_rep_delete_contact`)
   - Routing changed
   - Sharing changed
3. Run the command
4. Open `output/drift-report.md`
5. Explain:
   - High-risk drift blocks promotion
   - Report provides concrete rollback plan

## MCP angle for next iteration

This PoC uses mock JSON snapshots. For a stronger version:

- Replace JSON reads with an MCP collector:
  - `get_template_snapshot(template_id, env)`
  - `get_baseline_snapshot(template_id, release_tag)`
- Optionally store policy rules in Google Sheets and read them through MCP.

Current design keeps this easy: only the collector needs to change.
