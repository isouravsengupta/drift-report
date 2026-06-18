#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "Usage: ./run_live_demo.sh <baseline_org_alias> <candidate_org_alias> [permission_set_label] [sharing_object] [queue_name] [label_name]"
  exit 1
fi

BASELINE_ORG="$1"
CANDIDATE_ORG="$2"
PERMISSION_SET="${3:-DriftDemo_Perms}"
SHARING_OBJECT="${4:-Contact}"
QUEUE_NAME="${5:-Support Queue}"
LABEL_NAME="${6:-DRIFT_DEMO_LABEL}"

echo "Exporting baseline snapshot from: ${BASELINE_ORG}"
python3 export_snapshot.py \
  --target-org "${BASELINE_ORG}" \
  --output snapshots/baseline.json \
  --permission-set "${PERMISSION_SET}" \
  --sharing-object "${SHARING_OBJECT}" \
  --queue-name "${QUEUE_NAME}" \
  --label-name "${LABEL_NAME}"

echo "Exporting candidate snapshot from: ${CANDIDATE_ORG}"
python3 export_snapshot.py \
  --target-org "${CANDIDATE_ORG}" \
  --output snapshots/current.json \
  --permission-set "${PERMISSION_SET}" \
  --sharing-object "${SHARING_OBJECT}" \
  --queue-name "${QUEUE_NAME}" \
  --label-name "${LABEL_NAME}"

echo "Running drift report..."
python3 drift_guard.py \
  --baseline snapshots/baseline.json \
  --current snapshots/current.json \
  --output output

echo "Done. Open output/drift-report.md"
