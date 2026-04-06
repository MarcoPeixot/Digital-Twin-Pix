#!/usr/bin/env python3
import argparse
import json
import pathlib


ROOT = pathlib.Path(__file__).resolve().parents[1]
RUNS_DIR = ROOT / "results" / "runs"

METRICS = [
    "api_gateway_latency_p95_ms",
    "processing_latency_p95_ms",
    "directory_latency_p95_ms",
    "api_gateway_error_total",
    "processing_error_total",
    "directory_error_total",
    "processing_backlog_max",
    "processing_timeout_total",
    "processing_queue_rejections_total",
    "twin_alerts_total",
    "twin_recommendations_total",
]


def resolve_run(run_arg):
    candidate = pathlib.Path(run_arg)
    if candidate.is_dir():
        return candidate
    run_dir = RUNS_DIR / run_arg
    if run_dir.is_dir():
        return run_dir
    raise FileNotFoundError(f"Execucao nao encontrada: {run_arg}")


def load_summary(run_dir):
    return json.loads((run_dir / "summary.json").read_text())


def fmt(value):
    if value is None:
        return "n/a"
    if isinstance(value, bool):
        return "true" if value else "false"
    return f"{value:.4f}" if isinstance(value, float) else str(value)


def main():
    parser = argparse.ArgumentParser(description="Compara duas execucoes experimentais.")
    parser.add_argument("--run-a", required=True)
    parser.add_argument("--run-b", required=True)
    args = parser.parse_args()

    run_a_dir = resolve_run(args.run_a)
    run_b_dir = resolve_run(args.run_b)

    summary_a = load_summary(run_a_dir)
    summary_b = load_summary(run_b_dir)

    output = {
        "run_a": summary_a["run_id"],
        "run_b": summary_b["run_id"],
        "scenario_a": summary_a["scenario_id"],
        "scenario_b": summary_b["scenario_id"],
        "mode_a": summary_a["mode"],
        "mode_b": summary_b["mode"],
        "metrics": [],
    }

    for metric in METRICS:
        a_val = summary_a["metrics"].get(metric)
        b_val = summary_b["metrics"].get(metric)
        delta = None
        if isinstance(a_val, (int, float)) and isinstance(b_val, (int, float)):
            delta = b_val - a_val
        output["metrics"].append({
            "metric": metric,
            "run_a": a_val,
            "run_b": b_val,
            "delta_b_minus_a": delta,
        })

    comparison_dir = ROOT / "results" / "comparisons"
    comparison_dir.mkdir(parents=True, exist_ok=True)
    comparison_path = comparison_dir / f"{summary_a['run_id']}__vs__{summary_b['run_id']}.json"
    comparison_path.write_text(json.dumps(output, indent=2))

    print(f"Comparacao salva em {comparison_path.relative_to(ROOT)}")
    for item in output["metrics"]:
        print(
            f"{item['metric']}: "
            f"A={fmt(item['run_a'])} | "
            f"B={fmt(item['run_b'])} | "
            f"delta={fmt(item['delta_b_minus_a'])}"
        )


if __name__ == "__main__":
    main()
