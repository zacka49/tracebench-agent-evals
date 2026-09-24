from __future__ import annotations

import html
import random
from collections import defaultdict
from pathlib import Path

from .schemas import EpisodeRecord


def _rate(records: list[EpisodeRecord], field: str) -> float:
    if not records:
        return 0.0
    return sum(bool(getattr(record.score, field)) for record in records) / len(records)


def paired_bootstrap_difference(
    records: list[EpisodeRecord],
    left: str = "controls_and_recovery",
    right: str = "baseline",
    samples: int = 2000,
    seed: int = 17,
) -> tuple[float, float, float] | None:
    by_case: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for record in records:
        by_case[record.case_id][record.variant.value].append(
            float(record.score.verified_completion)
        )
    pairs = []
    for variants in by_case.values():
        if left in variants and right in variants:
            pairs.append(
                sum(variants[left]) / len(variants[left])
                - sum(variants[right]) / len(variants[right])
            )
    if not pairs:
        return None
    estimate = sum(pairs) / len(pairs)
    rng = random.Random(seed)
    draws = sorted(
        sum(rng.choice(pairs) for _ in pairs) / len(pairs) for _ in range(samples)
    )
    return estimate, draws[int(0.025 * samples)], draws[int(0.975 * samples) - 1]


def build_report(records: list[EpisodeRecord], output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    grouped: dict[tuple[str, str], list[EpisodeRecord]] = defaultdict(list)
    for record in records:
        grouped[(record.variant.value, record.condition.value)].append(record)
    rows = []
    for (variant, condition), items in sorted(grouped.items()):
        rows.append(
            {
                "variant": variant,
                "condition": condition,
                "n": len(items),
                "completion": _rate(items, "verified_completion"),
                "false_completion": _rate(items, "false_completion"),
                "fault_recovery": _rate(
                    [item for item in items if item.score.fault_fired], "fault_recovered"
                ),
                "duplicates": sum(item.score.duplicate_effects for item in items),
                "mean_calls": sum(item.score.tool_calls for item in items) / len(items),
            }
        )
    comparison = paired_bootstrap_difference(
        [
            record
            for record in records
            if record.condition.value in {"fault", "combined"}
        ]
    )
    providers = sorted({record.provider for record in records})
    if providers == ["scripted"]:
        report_context = (
            "This report contains measured harness-control output. The scripted provider "
            "validates the expected failure modes and is not a language-model result."
        )
        html_context = "Measured harness-control results from the scripted provider."
    else:
        provider_text = ", ".join(f"`{provider}`" for provider in providers)
        report_context = (
            f"This report contains measured output from {provider_text}. Interpret local-model "
            "pilots using the recorded model digest, prompt and decoding configuration."
        )
        html_context = "Measured world-state results from a model-backed pilot."
    lines = [
        "# TraceBench run report",
        "",
        report_context,
        "",
        "| Variant | Condition | n | Verified completion | False completion | Fault recovery | Duplicate effects | Mean tool calls |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['variant']} | {row['condition']} | {row['n']} | "
            f"{row['completion']:.1%} | {row['false_completion']:.1%} | "
            f"{row['fault_recovery']:.1%} | {row['duplicates']} | {row['mean_calls']:.1f} |"
        )
    lines.extend(["", "## Primary paired contrast", ""])
    if comparison:
        estimate, lower, upper = comparison
        lines.append(
            "Controls-and-recovery minus baseline verified completion on fault/combined "
            f"conditions: {estimate:+.1%} (task-cluster bootstrap 95% interval "
            f"{lower:+.1%} to {upper:+.1%})."
        )
    else:
        lines.append("The configured run did not contain both primary variants.")
    lines.extend(
        [
            "",
            "## Interpretation limits",
            "",
            (
                "Synthetic tasks measure this simulator. A deterministic scripted run only "
                "verifies that faults and scorers behave as designed. Local-model pilots are "
                "small and depend on the exact model digest, prompt, quantisation and decoding "
                "configuration."
            ),
        ]
    )
    markdown_path = output_dir / "report.md"
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    body = "\n".join(
        f"<tr><td>{html.escape(row['variant'])}</td><td>{html.escape(row['condition'])}</td>"
        f"<td>{row['n']}</td><td>{row['completion']:.1%}</td>"
        f"<td>{row['false_completion']:.1%}</td><td>{row['duplicates']}</td></tr>"
        for row in rows
    )
    html_path = output_dir / "report.html"
    html_path.write_text(
        "<!doctype html><html><head><meta charset='utf-8'><title>TraceBench</title>"
        "<style>body{font:16px system-ui;max-width:960px;margin:40px auto;padding:0 20px}"
        "table{border-collapse:collapse;width:100%}th,td{padding:10px;border:1px solid #ccd}"
        "th{background:#eef}code{background:#eef;padding:2px 4px}</style></head><body>"
        f"<h1>TraceBench run</h1><p>{html.escape(html_context)}</p>"
        "<table><thead><tr><th>Variant</th>"
        "<th>Condition</th><th>n</th><th>Completion</th><th>False completion</th>"
        f"<th>Duplicates</th></tr></thead><tbody>{body}</tbody></table>"
        "<p>See <code>report.md</code> for the paired estimate and limitations.</p></body></html>",
        encoding="utf-8",
    )
    return markdown_path, html_path
