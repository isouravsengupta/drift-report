#!/usr/bin/env python3
"""Export a normalized drift snapshot from a Salesforce org via sf CLI.

This script intentionally focuses on a small, stable subset of metadata that
maps to the Drift Report PoC schema.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List


def run_sf_query(target_org: str, soql: str) -> List[Dict[str, Any]]:
    cmd = [
        "sf",
        "data",
        "query",
        "--target-org",
        target_org,
        "--query",
        soql,
        "--result-format",
        "json",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        print(
            f"[WARN] Query failed for org '{target_org}': {soql}",
            file=sys.stderr,
        )
        if proc.stderr.strip():
            print(proc.stderr.strip(), file=sys.stderr)
        return []
    payload = json.loads(proc.stdout)
    result = payload.get("result", {})
    return result.get("records", [])


def collect_features(target_org: str) -> Dict[str, Any]:
    org_rows = run_sf_query(
        target_org,
        "SELECT IsEinsteinAnalyticsEnabled, IsSandbox FROM Organization LIMIT 1",
    )
    org_row = org_rows[0] if org_rows else {}
    return {
        "gen_ai_enabled": bool(org_row.get("IsEinsteinAnalyticsEnabled", False)),
        "is_sandbox": bool(org_row.get("IsSandbox", False)),
    }


def collect_permissions(target_org: str, permission_set_name: str) -> Dict[str, Any]:
    rows = run_sf_query(
        target_org,
        (
            "SELECT SObjectType, PermissionsRead, PermissionsCreate, "
            "PermissionsEdit, PermissionsDelete, PermissionsViewAllRecords, "
            "PermissionsModifyAllRecords "
            "FROM ObjectPermissions "
            f"WHERE Parent.Label = '{permission_set_name}' "
            "AND SObjectType IN ('Account','Contact','Case')"
        ),
    )
    out: Dict[str, Any] = {}
    for row in rows:
        obj = str(row.get("SObjectType", "")).lower()
        if not obj:
            continue
        out[f"{obj}_read"] = bool(row.get("PermissionsRead", False))
        out[f"{obj}_create"] = bool(row.get("PermissionsCreate", False))
        out[f"{obj}_edit"] = bool(row.get("PermissionsEdit", False))
        out[f"{obj}_delete"] = bool(row.get("PermissionsDelete", False))
        out[f"{obj}_view_all"] = bool(row.get("PermissionsViewAllRecords", False))
        out[f"{obj}_modify_all"] = bool(row.get("PermissionsModifyAllRecords", False))
    return out


def collect_sharing(target_org: str, object_api_name: str) -> Dict[str, Any]:
    rows = run_sf_query(
        target_org,
        (
            "SELECT QualifiedApiName, ExternalSharingModel, InternalSharingModel "
            "FROM EntityDefinition "
            f"WHERE QualifiedApiName = '{object_api_name}' LIMIT 1"
        ),
    )
    row = rows[0] if rows else {}
    if not row:
        return {}
    key = object_api_name.lower()
    return {
        f"{key}_internal_visibility": row.get("InternalSharingModel"),
        f"{key}_external_visibility": row.get("ExternalSharingModel"),
    }


def collect_routing(target_org: str, queue_name: str) -> Dict[str, Any]:
    rows = run_sf_query(
        target_org,
        (
            "SELECT Name, DeveloperName FROM Group "
            f"WHERE Type = 'Queue' AND Name = '{queue_name}' LIMIT 1"
        ),
    )
    if not rows:
        return {"inbound_queue_present": False, "inbound_queue_name": queue_name}
    row = rows[0]
    return {
        "inbound_queue_present": True,
        "inbound_queue_name": row.get("Name"),
        "inbound_queue_dev_name": row.get("DeveloperName"),
    }


def collect_labels(target_org: str, label_name: str) -> Dict[str, Any]:
    rows = run_sf_query(
        target_org,
        (
            "SELECT Name, Value FROM ExternalString "
            f"WHERE Name = '{label_name}' LIMIT 1"
        ),
    )
    if not rows:
        return {"demo_label_present": False, "demo_label_name": label_name}
    row = rows[0]
    return {
        "demo_label_present": True,
        "demo_label_name": row.get("Name"),
        "demo_label_value": row.get("Value"),
    }


def build_snapshot(
    target_org: str,
    permission_set_name: str,
    object_api_name: str,
    queue_name: str,
    label_name: str,
) -> Dict[str, Any]:
    return {
        "template_id": target_org,
        "features": collect_features(target_org),
        "permissions": collect_permissions(target_org, permission_set_name),
        "sharing": collect_sharing(target_org, object_api_name),
        "routing": collect_routing(target_org, queue_name),
        "labels": collect_labels(target_org, label_name),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export Drift Report snapshot")
    parser.add_argument("--target-org", required=True, help="Salesforce org alias")
    parser.add_argument("--output", type=Path, required=True, help="Output json path")
    parser.add_argument(
        "--permission-set",
        default="DriftDemo_Perms",
        help="Permission set label used in your demo",
    )
    parser.add_argument(
        "--sharing-object",
        default="Contact",
        help="Object API name to inspect sharing model",
    )
    parser.add_argument(
        "--queue-name",
        default="Support Queue",
        help="Queue name used in your demo routing change",
    )
    parser.add_argument(
        "--label-name",
        default="DRIFT_DEMO_LABEL",
        help="Custom label name used in your demo",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    snapshot = build_snapshot(
        target_org=args.target_org,
        permission_set_name=args.permission_set,
        object_api_name=args.sharing_object,
        queue_name=args.queue_name,
        label_name=args.label_name,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    print(f"Snapshot written: {args.output}")


if __name__ == "__main__":
    main()
