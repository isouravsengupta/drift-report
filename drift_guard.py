#!/usr/bin/env python3
"""Template Drift Guard - quick PoC.

Compares two template snapshots, computes drift, assigns risk levels,
and writes both JSON + Markdown reports.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple


@dataclass(frozen=True)
class RiskRule:
    startswith: str
    level: str
    reason: str


RISK_RULES: List[RiskRule] = [
    RiskRule(
        startswith="permissions.",
        level="high",
        reason="Permission changes can grant/restrict critical access.",
    ),
    RiskRule(
        startswith="routing.",
        level="high",
        reason="Routing changes can impact customer experience and SLAs.",
    ),
    RiskRule(
        startswith="sharing.",
        level="high",
        reason="Sharing model drift can cause security and visibility issues.",
    ),
    RiskRule(
        startswith="features.gen_ai",
        level="medium",
        reason="Gen AI feature toggles can alter runtime behavior.",
    ),
    RiskRule(
        startswith="features.",
        level="medium",
        reason="Feature toggle changes can affect activation flows.",
    ),
    RiskRule(
        startswith="labels.",
        level="low",
        reason="Label-only changes are usually cosmetic.",
    ),
    RiskRule(
        startswith="descriptions.",
        level="low",
        reason="Description-only changes are usually non-functional.",
    ),
]


def flatten(data: Dict, parent_key: str = "") -> Dict[str, object]:
    """Flatten nested JSON into dot-separated key/value paths."""
    items: Dict[str, object] = {}
    for key, value in data.items():
        new_key = f"{parent_key}.{key}" if parent_key else key
        if isinstance(value, dict):
            items.update(flatten(value, new_key))
        else:
            items[new_key] = value
    return items


def infer_risk(path: str) -> Tuple[str, str]:
    for rule in RISK_RULES:
        if path.startswith(rule.startswith):
            return rule.level, rule.reason
    return "low", "Default low risk (no high/medium rule matched)."


def compare_snapshots(
    baseline: Dict[str, object], current: Dict[str, object]
) -> List[Dict[str, object]]:
    drift_items: List[Dict[str, object]] = []
    all_keys = sorted(set(baseline.keys()) | set(current.keys()))

    for key in all_keys:
        in_base = key in baseline
        in_curr = key in current

        if in_base and not in_curr:
            change_type = "removed"
            old_val = baseline[key]
            new_val = None
        elif not in_base and in_curr:
            change_type = "added"
            old_val = None
            new_val = current[key]
        elif baseline[key] != current[key]:
            change_type = "modified"
            old_val = baseline[key]
            new_val = current[key]
        else:
            continue

        level, reason = infer_risk(key)
        drift_items.append(
            {
                "path": key,
                "change_type": change_type,
                "baseline_value": old_val,
                "current_value": new_val,
                "risk_level": level,
                "risk_reason": reason,
            }
        )

    return drift_items


def risk_counts(drift_items: List[Dict[str, object]]) -> Dict[str, int]:
    out = {"high": 0, "medium": 0, "low": 0}
    for item in drift_items:
        out[item["risk_level"]] += 1
    return out


def safe_to_promote(counts: Dict[str, int]) -> bool:
    return counts["high"] == 0


def rollback_plan(drift_items: List[Dict[str, object]]) -> List[str]:
    steps: List[str] = []
    for item in drift_items:
        if item["change_type"] == "added":
            steps.append(f"Remove `{item['path']}` from current snapshot.")
        elif item["change_type"] == "removed":
            steps.append(
                f"Restore `{item['path']}` to `{json.dumps(item['baseline_value'])}`."
            )
        else:
            steps.append(
                "Reset "
                f"`{item['path']}` to baseline value "
                f"`{json.dumps(item['baseline_value'])}`."
            )
    return steps


def write_markdown_report(
    report_path: Path,
    baseline_path: Path,
    current_path: Path,
    drift_items: List[Dict[str, object]],
    counts: Dict[str, int],
) -> None:
    generated_at = datetime.now(timezone.utc).isoformat()
    promote = "YES" if safe_to_promote(counts) else "NO"

    lines = [
        "# Template Drift Guard Report",
        "",
        f"- Generated at: `{generated_at}`",
        f"- Baseline: `{baseline_path}`",
        f"- Current: `{current_path}`",
        "",
        "## Executive View",
        "",
        f"- Total drift items: **{len(drift_items)}**",
        f"- High risk: **{counts['high']}**",
        f"- Medium risk: **{counts['medium']}**",
        f"- Low risk: **{counts['low']}**",
        f"- Safe to promote: **{promote}**",
        "",
        "## Drift Details",
        "",
    ]

    if not drift_items:
        lines.append("No drift found. Baseline and current snapshots match.")
    else:
        for idx, item in enumerate(drift_items, start=1):
            lines.extend(
                [
                    f"### {idx}. `{item['path']}`",
                    f"- Change: **{item['change_type']}**",
                    f"- Risk: **{item['risk_level']}**",
                    f"- Why: {item['risk_reason']}",
                    f"- Baseline value: `{json.dumps(item['baseline_value'])}`",
                    f"- Current value: `{json.dumps(item['current_value'])}`",
                    "",
                ]
            )

        lines.extend(["## Suggested Rollback Plan", ""])
        for i, step in enumerate(rollback_plan(drift_items), start=1):
            lines.append(f"{i}. {step}")

    report_path.write_text("\n".join(lines), encoding="utf-8")


def run(baseline_file: Path, current_file: Path, output_dir: Path) -> None:
    baseline_raw = json.loads(baseline_file.read_text(encoding="utf-8"))
    current_raw = json.loads(current_file.read_text(encoding="utf-8"))

    baseline_flat = flatten(baseline_raw)
    current_flat = flatten(current_raw)

    drift_items = compare_snapshots(baseline_flat, current_flat)
    counts = risk_counts(drift_items)

    output_dir.mkdir(parents=True, exist_ok=True)
    json_report_path = output_dir / "drift-report.json"
    md_report_path = output_dir / "drift-report.md"

    json_report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "safe_to_promote": safe_to_promote(counts),
        "risk_counts": counts,
        "drift_items": drift_items,
    }
    json_report_path.write_text(json.dumps(json_report, indent=2), encoding="utf-8")

    write_markdown_report(
        report_path=md_report_path,
        baseline_path=baseline_file,
        current_path=current_file,
        drift_items=drift_items,
        counts=counts,
    )

    print(f"Done. JSON report: {json_report_path}")
    print(f"Done. Markdown report: {md_report_path}")
    print(
        "Summary -> "
        f"High: {counts['high']}, Medium: {counts['medium']}, Low: {counts['low']}, "
        f"Safe to promote: {safe_to_promote(counts)}"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Template Drift Guard PoC")
    parser.add_argument(
        "--baseline",
        type=Path,
        required=True,
        help="Path to baseline snapshot JSON",
    )
    parser.add_argument(
        "--current",
        type=Path,
        required=True,
        help="Path to current snapshot JSON",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("./output"),
        help="Output directory for generated reports",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run(args.baseline, args.current, args.output)
