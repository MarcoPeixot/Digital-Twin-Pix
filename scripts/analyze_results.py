#!/usr/bin/env python3
import argparse
import csv
import json
import math
import pathlib
from datetime import datetime, timezone


ROOT = pathlib.Path(__file__).resolve().parents[1]
RUNS_DIR = ROOT / "results" / "runs"
ANALYSIS_DIR = ROOT / "results" / "analysis"
SCENARIOS_DIR = ROOT / "experiments" / "scenarios"

COMPARISON_METRICS = [
    {
        "key": "throughput_req_s",
        "label": "Throughput",
        "unit": "req/s",
        "better": "higher",
        "source": "derived",
    },
    {
        "key": "load_http_req_avg_ms",
        "label": "Latencia media HTTP",
        "unit": "ms",
        "better": "lower",
        "source": "derived",
    },
    {
        "key": "load_http_req_p95_ms",
        "label": "Latencia p95 HTTP",
        "unit": "ms",
        "better": "lower",
        "source": "derived",
    },
    {
        "key": "api_gateway_latency_p95_ms",
        "label": "Latencia p95 API Gateway",
        "unit": "ms",
        "better": "lower",
        "source": "summary",
    },
    {
        "key": "processing_latency_p95_ms",
        "label": "Latencia p95 Processing Core",
        "unit": "ms",
        "better": "lower",
        "source": "summary",
    },
    {
        "key": "directory_latency_p95_ms",
        "label": "Latencia p95 Directory",
        "unit": "ms",
        "better": "lower",
        "source": "summary",
    },
    {
        "key": "success_rate_pct",
        "label": "Taxa de sucesso",
        "unit": "%",
        "better": "higher",
        "source": "derived",
    },
    {
        "key": "error_rate_pct",
        "label": "Taxa de erro",
        "unit": "%",
        "better": "lower",
        "source": "derived",
    },
    {
        "key": "processing_backlog_max",
        "label": "Backlog maximo",
        "unit": "itens",
        "better": "lower",
        "source": "summary",
    },
    {
        "key": "processing_timeout_total",
        "label": "Timeouts de processamento",
        "unit": "eventos",
        "better": "lower",
        "source": "summary",
    },
    {
        "key": "processing_queue_rejections_total",
        "label": "Rejeicoes por fila",
        "unit": "eventos",
        "better": "lower",
        "source": "summary",
    },
]

SUMMARY_HEADERS = [
    "scenario_id",
    "scenario_name",
    "without_twin_run_id",
    "with_twin_run_id",
    "config_sha256",
    "git_commit_without_twin",
    "git_commit_with_twin",
    "git_dirty_without_twin",
    "git_dirty_with_twin",
    "effect_label",
    "effect_basis",
    "effect_score",
    "throughput_req_s_without_twin",
    "throughput_req_s_with_twin",
    "load_http_req_avg_ms_without_twin",
    "load_http_req_avg_ms_with_twin",
    "load_http_req_p95_ms_without_twin",
    "load_http_req_p95_ms_with_twin",
    "error_rate_pct_without_twin",
    "error_rate_pct_with_twin",
    "processing_backlog_max_without_twin",
    "processing_backlog_max_with_twin",
    "processing_timeout_total_without_twin",
    "processing_timeout_total_with_twin",
]


def parse_args():
    parser = argparse.ArgumentParser(
        description="Gera a analise final comparativa dos resultados experimentais ja produzidos."
    )
    parser.add_argument(
        "--output-dir",
        help="Diretorio de saida. Padrao: results/analysis/<timestamp>",
    )
    return parser.parse_args()


def load_json(path):
    return json.loads(path.read_text())


def read_optional_json(path):
    if path.is_file():
        return load_json(path)
    return None


def ensure_dir(path):
    path.mkdir(parents=True, exist_ok=True)
    return path


def iso_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def slugify(text):
    return "".join(ch if ch.isalnum() or ch in {"-", "_"} else "-" for ch in text.lower()).strip("-")


def format_number(value, unit=None):
    if value is None:
        return "n/a"
    if isinstance(value, (int, float)):
        if math.isfinite(value):
            if unit == "%":
                return f"{value:.2f}%"
            if abs(value) >= 1000:
                return f"{value:,.2f}".replace(",", "_")
            if abs(value) >= 1:
                return f"{value:.2f}"
            return f"{value:.4f}"
    return str(value)


def percent_change(old_value, new_value):
    if old_value is None or new_value is None:
        return None
    if not isinstance(old_value, (int, float)) or not isinstance(new_value, (int, float)):
        return None
    if old_value == 0:
        if new_value == 0:
            return 0.0
        return None
    return ((new_value - old_value) / old_value) * 100.0


def safe_ratio(numerator, denominator):
    if denominator in (None, 0):
        return None
    return numerator / denominator


def parse_timestamp(value):
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def resolve_output_dir(output_dir_arg, timestamp):
    if not output_dir_arg:
        return ANALYSIS_DIR / timestamp
    candidate = pathlib.Path(output_dir_arg)
    if not candidate.is_absolute():
        candidate = ROOT / candidate
    return candidate


def display_path(path):
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def load_run(run_dir):
    summary_path = run_dir / "summary.json"
    manifest_path = run_dir / "manifest.json"
    if not summary_path.is_file() or not manifest_path.is_file():
        return None

    summary = load_json(summary_path)
    manifest = load_json(manifest_path)
    scenario = read_optional_json(run_dir / "scenario.json")
    effective_config = read_optional_json(run_dir / "effective-config.json")
    load_summary = read_optional_json(run_dir / "load-summary.json")
    twin_state = read_optional_json(run_dir / "twin-state.json")
    events = read_optional_json(run_dir / "events.json")

    summary_metrics = summary.get("metrics", {})
    derived_metrics = derive_metrics(summary_metrics, load_summary)

    return {
        "run_dir": run_dir,
        "run_id": summary["run_id"],
        "scenario_id": summary["scenario_id"],
        "scenario_name": manifest.get("scenario", {}).get("name") or (scenario or {}).get("name"),
        "scenario_description": (scenario or {}).get("description"),
        "scenario_group": (scenario or {}).get("scenario_group"),
        "mode": summary["mode"],
        "started_at": summary.get("started_at"),
        "finished_at": summary.get("finished_at"),
        "started_dt": parse_timestamp(summary.get("started_at")) or parse_timestamp(manifest.get("created_at")),
        "summary": summary,
        "manifest": manifest,
        "scenario": scenario,
        "effective_config": effective_config,
        "load_summary": load_summary,
        "twin_state": twin_state,
        "events": events,
        "metrics": {**summary_metrics, **derived_metrics},
        "config_sha256": manifest.get("effective_config_sha256"),
        "git_commit": manifest.get("git", {}).get("commit"),
        "git_branch": manifest.get("git", {}).get("branch"),
        "git_dirty": manifest.get("git", {}).get("dirty"),
        "service_base_urls": manifest.get("service_base_urls", {}),
    }


def derive_metrics(summary_metrics, load_summary):
    result = {}
    load_metrics = (load_summary or {}).get("metrics", {})
    http_req_duration = load_metrics.get("http_req_duration", {})
    http_reqs = load_metrics.get("http_reqs", {})

    result["load_http_req_avg_ms"] = http_req_duration.get("avg")
    result["load_http_req_p95_ms"] = http_req_duration.get("p(95)")
    result["throughput_req_s"] = http_reqs.get("rate")

    success_total = summary_metrics.get("api_gateway_success_total")
    error_total = summary_metrics.get("api_gateway_error_total")
    total = None
    if isinstance(success_total, (int, float)) and isinstance(error_total, (int, float)):
        total = success_total + error_total
    result["success_rate_pct"] = safe_ratio(success_total * 100.0 if success_total is not None else None, total)
    result["error_rate_pct"] = safe_ratio(error_total * 100.0 if error_total is not None else None, total)
    return result


def collect_runs():
    runs = []
    for run_dir in sorted(RUNS_DIR.iterdir()):
        if not run_dir.is_dir():
            continue
        run_data = load_run(run_dir)
        if run_data:
            runs.append(run_data)
    return runs


def collect_declared_scenarios():
    scenarios = {}
    for path in sorted(SCENARIOS_DIR.glob("*.json")):
        payload = load_json(path)
        scenarios[payload["id"]] = {
            "id": payload["id"],
            "name": payload.get("name"),
            "description": payload.get("description"),
            "scenario_group": payload.get("scenario_group"),
            "path": path.relative_to(ROOT).as_posix(),
        }
    return scenarios


def pair_runs(runs):
    grouped = {}
    for run in runs:
        scenario_group = grouped.setdefault(run["scenario_id"], {})
        config_group = scenario_group.setdefault(run["config_sha256"], {"with-twin": [], "without-twin": []})
        config_group[run["mode"]].append(run)

    pairs = []
    for scenario_id, configs in grouped.items():
        candidates = []
        for config_sha, config_group in configs.items():
            if not config_group["with-twin"] or not config_group["without-twin"]:
                continue
            with_twin = sorted(config_group["with-twin"], key=lambda item: item["started_dt"] or datetime.min)[-1]
            without_twin = sorted(config_group["without-twin"], key=lambda item: item["started_dt"] or datetime.min)[-1]
            latest_dt = max(
                with_twin["started_dt"] or datetime.min.replace(tzinfo=timezone.utc),
                without_twin["started_dt"] or datetime.min.replace(tzinfo=timezone.utc),
            )
            candidates.append((latest_dt, config_sha, without_twin, with_twin))
        if candidates:
            _, config_sha, without_twin, with_twin = sorted(candidates, key=lambda item: item[0])[-1]
            pairs.append(build_pair_record(scenario_id, config_sha, without_twin, with_twin))
    return sorted(pairs, key=lambda item: item["scenario_name"])


def compare_metric(metric_def, without_twin, with_twin):
    key = metric_def["key"]
    without_value = without_twin["metrics"].get(key)
    with_value = with_twin["metrics"].get(key)
    delta = None
    if isinstance(without_value, (int, float)) and isinstance(with_value, (int, float)):
        delta = with_value - without_value
    delta_pct = percent_change(without_value, with_value)

    improved = None
    if delta is not None:
        if delta == 0:
            improved = None
        elif metric_def["better"] == "lower":
            improved = delta < 0
        elif metric_def["better"] == "higher":
            improved = delta > 0

    return {
        "key": key,
        "label": metric_def["label"],
        "unit": metric_def["unit"],
        "better": metric_def["better"],
        "without_twin": without_value,
        "with_twin": with_value,
        "delta": delta,
        "delta_pct": delta_pct,
        "improved": improved,
        "source": metric_def["source"],
    }


def select_chart_metrics(metric_rows):
    priority = [
        "throughput_req_s",
        "load_http_req_p95_ms",
        "api_gateway_latency_p95_ms",
        "processing_backlog_max",
        "processing_timeout_total",
        "error_rate_pct",
    ]
    by_key = {row["key"]: row for row in metric_rows if row["without_twin"] is not None or row["with_twin"] is not None}
    selected = []
    for key in priority:
        if key in by_key:
            selected.append(by_key[key])
        if len(selected) == 4:
            break
    return selected


def build_pair_record(scenario_id, config_sha, without_twin, with_twin):
    metric_rows = [compare_metric(metric_def, without_twin, with_twin) for metric_def in COMPARISON_METRICS]
    effect_score = sum(1 for row in metric_rows if row["improved"] is True) - sum(
        1 for row in metric_rows if row["improved"] is False
    )
    effect_label, effect_basis = classify_effect(without_twin, with_twin, effect_score)

    interpretation = build_interpretation(without_twin, with_twin, metric_rows, effect_label, effect_basis)

    return {
        "scenario_id": scenario_id,
        "scenario_name": without_twin["scenario_name"] or with_twin["scenario_name"] or scenario_id,
        "scenario_description": without_twin["scenario_description"] or with_twin["scenario_description"],
        "scenario_group": without_twin["scenario_group"] or with_twin["scenario_group"],
        "config_sha256": config_sha,
        "without_twin": without_twin,
        "with_twin": with_twin,
        "metric_rows": metric_rows,
        "effect_score": effect_score,
        "effect_label": effect_label,
        "effect_basis": effect_basis,
        "interpretation": interpretation,
        "chart_metrics": select_chart_metrics(metric_rows),
    }


def classify_effect(without_twin, with_twin, effect_score):
    without_observed = without_twin["summary"].get("observed_result", {})
    with_observed = with_twin["summary"].get("observed_result", {})
    without_degraded = bool(without_observed.get("degraded"))
    with_degraded = bool(with_observed.get("degraded"))
    alerts_total = with_observed.get("twin_alerts_emitted")
    recommendations_total = with_observed.get("twin_recommendations_emitted")

    twin_has_activity = (alerts_total not in (None, 0)) or (recommendations_total not in (None, 0))
    degradation_observed = without_degraded or with_degraded

    if not degradation_observed and not twin_has_activity:
        return (
            "neutro ou inconclusivo",
            "Sem degradacao observada e sem atividade registrada do twin; diferencas pequenas ficam tratadas como variacao de execucao, nao como ganho experimental.",
        )
    if effect_score > 0:
        return "favoravel ao twin", "Classificacao baseada no saldo de metricas comparadas dentro do cenario."
    if effect_score < 0:
        return "desfavoravel ao twin", "Classificacao baseada no saldo de metricas comparadas dentro do cenario."
    return "neutro ou inconclusivo", "As metricas comparadas nao mostraram vantagem consistente entre os modos."


def build_interpretation(without_twin, with_twin, metric_rows, effect_label, effect_basis):
    metrics_by_key = {row["key"]: row for row in metric_rows}
    without_degraded = bool(without_twin["summary"].get("observed_result", {}).get("degraded"))
    with_degraded = bool(with_twin["summary"].get("observed_result", {}).get("degraded"))
    alerts_total = with_twin["summary"].get("observed_result", {}).get("twin_alerts_emitted")
    recommendations_total = with_twin["summary"].get("observed_result", {}).get("twin_recommendations_emitted")

    throughput_row = metrics_by_key.get("throughput_req_s")
    p95_row = metrics_by_key.get("load_http_req_p95_ms")
    error_row = metrics_by_key.get("error_rate_pct")
    backlog_row = metrics_by_key.get("processing_backlog_max")

    degraded_text = "Nao houve degradacao observada no resumo consolidado." if not (without_degraded or with_degraded) else (
        "Houve indicio de degradacao em pelo menos uma das execucoes." if without_degraded != with_degraded else
        "Houve degradacao observada nos dois modos."
    )

    start_text = (
        "O ponto exato de inicio da degradacao nao pode ser determinado com precisao porque os artefatos atuais sao snapshots finais, nao series temporais completas."
    )

    if alerts_total in (None, 0) and recommendations_total in (None, 0):
        twin_text = "Nao houve alerta ou recomendacao registrada pelo twin neste cenario."
    else:
        twin_text = (
            f"O twin registrou {int(alerts_total or 0)} alertas e {int(recommendations_total or 0)} recomendacoes."
        )

    gain_fragments = []
    if throughput_row and throughput_row["improved"] is True:
        gain_fragments.append(
            f"throughput maior ({format_number(throughput_row['with_twin'], throughput_row['unit'])} vs {format_number(throughput_row['without_twin'], throughput_row['unit'])})"
        )
    if p95_row and p95_row["improved"] is True:
        gain_fragments.append(
            f"latencia p95 menor ({format_number(p95_row['with_twin'], p95_row['unit'])} vs {format_number(p95_row['without_twin'], p95_row['unit'])})"
        )
    if error_row and error_row["improved"] is True:
        gain_fragments.append(
            f"taxa de erro menor ({format_number(error_row['with_twin'], error_row['unit'])} vs {format_number(error_row['without_twin'], error_row['unit'])})"
        )
    if backlog_row and backlog_row["improved"] is True:
        gain_fragments.append(
            f"backlog maximo menor ({format_number(backlog_row['with_twin'], backlog_row['unit'])} vs {format_number(backlog_row['without_twin'], backlog_row['unit'])})"
        )

    if effect_label == "neutro ou inconclusivo" and "variacao de execucao" in effect_basis.lower():
        gain_text = "As diferencas numericas observadas foram preservadas nas tabelas, mas nao sao tratadas como evidencia de ganho do twin neste cenario."
    elif gain_fragments:
        gain_text = "O ganho mensuravel favoreceu o twin em " + "; ".join(gain_fragments) + "."
    else:
        gain_text = "Nao houve ganho mensuravel consistente a favor do twin nas metricas disponiveis."

    mitigation_text = (
        "Nao ha evidencia de mitigacao efetiva registrada nos artefatos atuais."
        if alerts_total in (None, 0) and recommendations_total in (None, 0)
        else "Houve atividade do twin, mas o efeito da mitigacao depende das metricas comparadas."
    )

    return {
        "degradacao_observada": degraded_text,
        "inicio_degradacao": start_text,
        "comportamento_twin": twin_text,
        "mitigacao": mitigation_text,
        "efeito": f"Conclusao automatica do cenario: {effect_label}. {effect_basis} {gain_text}",
    }


def build_global_conclusion(pairs, missing_scenarios):
    scenario_count = len(pairs)
    favorable = sum(1 for pair in pairs if pair["effect_label"] == "favoravel ao twin")
    unfavorable = sum(1 for pair in pairs if pair["effect_label"] == "desfavoravel ao twin")
    neutral = scenario_count - favorable - unfavorable

    if favorable > unfavorable:
        headline = "No conjunto disponivel, o efeito agregado do gemeo digital foi predominantemente favoravel."
    elif unfavorable > favorable:
        headline = "No conjunto disponivel, o efeito agregado do gemeo digital foi predominantemente desfavoravel."
    else:
        headline = "No conjunto disponivel, o efeito agregado do gemeo digital ficou neutro ou inconclusivo."

    if missing_scenarios:
        availability = (
            "Ainda faltam pares completos para os cenarios: "
            + ", ".join(sorted(missing_scenarios))
            + "."
        )
    else:
        availability = "Todos os cenarios declarados possuem pares completos para comparacao."

    return {
        "headline": headline,
        "scenario_count": scenario_count,
        "favorable_scenarios": favorable,
        "unfavorable_scenarios": unfavorable,
        "neutral_scenarios": neutral,
        "availability": availability,
    }


def markdown_metric_table(metric_rows):
    lines = [
        "| Metrica | Sem twin | Com twin | Delta | Delta % | Melhor resultado |",
        "| --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in metric_rows:
        better_text = "with-twin" if row["improved"] is True else "without-twin" if row["improved"] is False else "n/a"
        lines.append(
            "| "
            + row["label"]
            + f" ({row['unit']}) | "
            + format_number(row["without_twin"], row["unit"])
            + " | "
            + format_number(row["with_twin"], row["unit"])
            + " | "
            + format_number(row["delta"], row["unit"])
            + " | "
            + format_number(row["delta_pct"], "%")
            + " | "
            + better_text
            + " |"
        )
    return "\n".join(lines)


def write_csv(path, headers, rows):
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def svg_bar_chart(title, metric_rows):
    width = 980
    row_height = 90
    chart_width = 320
    left = 310
    top = 70
    height = top + len(metric_rows) * row_height + 30
    palette = {"without": "#b0bec5", "with": "#1565c0"}

    max_values = []
    for row in metric_rows:
        values = [value for value in [row["without_twin"], row["with_twin"]] if isinstance(value, (int, float))]
        max_values.append(max(values) if values else 1.0)

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="40" y="42" font-family="Arial, sans-serif" font-size="24" font-weight="700" fill="#102a43">{escape_xml(title)}</text>',
        '<text x="40" y="62" font-family="Arial, sans-serif" font-size="12" fill="#486581">Comparacao direta entre without-twin e with-twin.</text>',
        '<rect x="730" y="22" width="18" height="18" fill="#b0bec5"/>',
        '<text x="756" y="36" font-family="Arial, sans-serif" font-size="13" fill="#102a43">without-twin</text>',
        '<rect x="860" y="22" width="18" height="18" fill="#1565c0"/>',
        '<text x="886" y="36" font-family="Arial, sans-serif" font-size="13" fill="#102a43">with-twin</text>',
    ]

    for index, row in enumerate(metric_rows):
        y = top + index * row_height
        scale_max = max_values[index] or 1.0
        without_width = 0 if row["without_twin"] in (None, 0) else (row["without_twin"] / scale_max) * chart_width
        with_width = 0 if row["with_twin"] in (None, 0) else (row["with_twin"] / scale_max) * chart_width

        lines.extend(
            [
                f'<text x="40" y="{y + 18}" font-family="Arial, sans-serif" font-size="14" font-weight="700" fill="#102a43">{escape_xml(row["label"])} ({escape_xml(row["unit"])})</text>',
                f'<line x1="{left}" y1="{y + 8}" x2="{left + chart_width}" y2="{y + 8}" stroke="#d9e2ec" stroke-width="1"/>',
                f'<rect x="{left}" y="{y + 18}" width="{without_width:.2f}" height="20" fill="{palette["without"]}"/>',
                f'<rect x="{left}" y="{y + 46}" width="{with_width:.2f}" height="20" fill="{palette["with"]}"/>',
                f'<text x="{left - 12}" y="{y + 33}" text-anchor="end" font-family="Arial, sans-serif" font-size="12" fill="#486581">without</text>',
                f'<text x="{left - 12}" y="{y + 61}" text-anchor="end" font-family="Arial, sans-serif" font-size="12" fill="#486581">with</text>',
                f'<text x="{left + chart_width + 12}" y="{y + 33}" font-family="Arial, sans-serif" font-size="12" fill="#102a43">{escape_xml(format_number(row["without_twin"], row["unit"]))}</text>',
                f'<text x="{left + chart_width + 12}" y="{y + 61}" font-family="Arial, sans-serif" font-size="12" fill="#102a43">{escape_xml(format_number(row["with_twin"], row["unit"]))}</text>',
            ]
        )

    lines.append("</svg>")
    return "\n".join(lines)


def escape_xml(value):
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def build_scenario_report(pair):
    without_twin = pair["without_twin"]
    with_twin = pair["with_twin"]
    interpretation = pair["interpretation"]

    lines = [
        f"# {pair['scenario_name']}",
        "",
        "## Objetivo",
        "",
        "Comparar explicitamente as execucoes without-twin e with-twin do cenario com base nos artefatos consolidados do experimento.",
        "",
        "## Rastreabilidade",
        "",
        f"- scenario_id: `{pair['scenario_id']}`",
        f"- scenario_group: `{pair['scenario_group'] or 'n/a'}`",
        f"- config_sha256: `{pair['config_sha256']}`",
        f"- effect_label: `{pair['effect_label']}`",
        f"- effect_basis: `{pair['effect_basis']}`",
        f"- without_twin run_id: `{without_twin['run_id']}`",
        f"- with_twin run_id: `{with_twin['run_id']}`",
        f"- without_twin commit: `{without_twin['git_commit']}`",
        f"- with_twin commit: `{with_twin['git_commit']}`",
        f"- without_twin dirty: `{without_twin['git_dirty']}`",
        f"- with_twin dirty: `{with_twin['git_dirty']}`",
        "",
        "## Tabela comparativa",
        "",
        markdown_metric_table(pair["metric_rows"]),
        "",
        "## Interpretacao objetiva",
        "",
        f"- O sistema degradou? {interpretation['degradacao_observada']}",
        f"- Em que ponto a degradacao comecou? {interpretation['inicio_degradacao']}",
        f"- O gemeo detectou antes da falha evidente? {interpretation['comportamento_twin']}",
        f"- A mitigacao melhorou o comportamento? {interpretation['mitigacao']}",
        f"- O ganho foi mensuravel? {interpretation['efeito']}",
        "",
        "## Grafico",
        "",
        f"Arquivo SVG: `chart-{slugify(pair['scenario_id'])}.svg`",
        "",
    ]
    return "\n".join(lines)


def build_global_report(pairs, missing_scenarios, global_conclusion, analysis_manifest):
    lines = [
        "# Analise Final dos Resultados Experimentais",
        "",
        "## Objetivo",
        "",
        "Consolidar a comparacao final entre execucoes with-twin e without-twin, com foco em metricas operacionais, interpretacao por cenario e conclusao objetiva para uso na IC.",
        "",
        "## Rastreabilidade",
        "",
        f"- analysis_id: `{analysis_manifest['analysis_id']}`",
        f"- generated_at: `{analysis_manifest['generated_at']}`",
        f"- source_runs_dir: `{analysis_manifest['source_runs_dir']}`",
        f"- analyzed_pairs: `{analysis_manifest['pair_count']}`",
        "",
        "## Conclusao consolidada",
        "",
        f"- {global_conclusion['headline']}",
        f"- Cenarios favoraveis ao twin: {global_conclusion['favorable_scenarios']}",
        f"- Cenarios desfavoraveis ao twin: {global_conclusion['unfavorable_scenarios']}",
        f"- Cenarios neutros ou inconclusivos: {global_conclusion['neutral_scenarios']}",
        f"- Disponibilidade dos dados: {global_conclusion['availability']}",
        "",
        "## Cenarios analisados",
        "",
    ]

    for pair in pairs:
        lines.extend(
            [
                f"### {pair['scenario_name']}",
                "",
                f"- scenario_id: `{pair['scenario_id']}`",
                f"- efeito consolidado: `{pair['effect_label']}`",
                f"- base da classificacao: {pair['effect_basis']}",
                f"- config_sha256: `{pair['config_sha256']}`",
                f"- without_twin run_id: `{pair['without_twin']['run_id']}`",
                f"- with_twin run_id: `{pair['with_twin']['run_id']}`",
                f"- relatorio detalhado: `scenarios/{pair['scenario_id']}/report.md`",
                "",
            ]
        )

    if missing_scenarios:
        lines.extend(
            [
                "## Cenarios ainda sem par completo",
                "",
                *[f"- `{scenario_id}`" for scenario_id in sorted(missing_scenarios)],
                "",
            ]
        )

    lines.extend(
        [
            "## Limitacoes",
            "",
            "- A analise depende apenas dos artefatos ja salvos em `results/runs`.",
            "- O ponto exato de inicio da degradacao nao pode ser estimado com alta precisao sem series temporais completas por execucao.",
            "- Os graficos desta etapa sao comparativos e simples; nao substituem dashboards ou observabilidade em tempo real.",
            "",
        ]
    )
    return "\n".join(lines)


def write_pair_outputs(base_dir, pair):
    scenario_dir = ensure_dir(base_dir / "scenarios" / pair["scenario_id"])

    comparison_json = {
        "scenario_id": pair["scenario_id"],
        "scenario_name": pair["scenario_name"],
        "config_sha256": pair["config_sha256"],
        "without_twin_run_id": pair["without_twin"]["run_id"],
        "with_twin_run_id": pair["with_twin"]["run_id"],
        "git_commit_without_twin": pair["without_twin"]["git_commit"],
        "git_commit_with_twin": pair["with_twin"]["git_commit"],
        "git_dirty_without_twin": pair["without_twin"]["git_dirty"],
        "git_dirty_with_twin": pair["with_twin"]["git_dirty"],
        "effect_score": pair["effect_score"],
        "effect_label": pair["effect_label"],
        "effect_basis": pair["effect_basis"],
        "metrics": pair["metric_rows"],
        "interpretation": pair["interpretation"],
    }
    (scenario_dir / "comparison.json").write_text(json.dumps(comparison_json, indent=2))

    csv_rows = []
    for row in pair["metric_rows"]:
        csv_rows.append(
            {
                "metric_key": row["key"],
                "metric_label": row["label"],
                "unit": row["unit"],
                "better": row["better"],
                "without_twin": row["without_twin"],
                "with_twin": row["with_twin"],
                "delta": row["delta"],
                "delta_pct": row["delta_pct"],
                "improved": row["improved"],
                "source": row["source"],
            }
        )
    write_csv(
        scenario_dir / "comparison.csv",
        [
            "metric_key",
            "metric_label",
            "unit",
            "better",
            "without_twin",
            "with_twin",
            "delta",
            "delta_pct",
            "improved",
            "source",
        ],
        csv_rows,
    )

    chart_path = scenario_dir / f"chart-{slugify(pair['scenario_id'])}.svg"
    chart_path.write_text(svg_bar_chart(pair["scenario_name"], pair["chart_metrics"]))
    (scenario_dir / "report.md").write_text(build_scenario_report(pair))


def build_analysis_summary(pairs, missing_scenarios, global_conclusion):
    items = []
    for pair in pairs:
        metric_map = {row["key"]: row for row in pair["metric_rows"]}
        items.append(
            {
                "scenario_id": pair["scenario_id"],
                "scenario_name": pair["scenario_name"],
                "without_twin_run_id": pair["without_twin"]["run_id"],
                "with_twin_run_id": pair["with_twin"]["run_id"],
                "config_sha256": pair["config_sha256"],
                "git_commit_without_twin": pair["without_twin"]["git_commit"],
                "git_commit_with_twin": pair["with_twin"]["git_commit"],
                "git_dirty_without_twin": pair["without_twin"]["git_dirty"],
                "git_dirty_with_twin": pair["with_twin"]["git_dirty"],
                "effect_label": pair["effect_label"],
                "effect_basis": pair["effect_basis"],
                "effect_score": pair["effect_score"],
                "throughput_req_s_without_twin": metric_map.get("throughput_req_s", {}).get("without_twin"),
                "throughput_req_s_with_twin": metric_map.get("throughput_req_s", {}).get("with_twin"),
                "load_http_req_avg_ms_without_twin": metric_map.get("load_http_req_avg_ms", {}).get("without_twin"),
                "load_http_req_avg_ms_with_twin": metric_map.get("load_http_req_avg_ms", {}).get("with_twin"),
                "load_http_req_p95_ms_without_twin": metric_map.get("load_http_req_p95_ms", {}).get("without_twin"),
                "load_http_req_p95_ms_with_twin": metric_map.get("load_http_req_p95_ms", {}).get("with_twin"),
                "error_rate_pct_without_twin": metric_map.get("error_rate_pct", {}).get("without_twin"),
                "error_rate_pct_with_twin": metric_map.get("error_rate_pct", {}).get("with_twin"),
                "processing_backlog_max_without_twin": metric_map.get("processing_backlog_max", {}).get("without_twin"),
                "processing_backlog_max_with_twin": metric_map.get("processing_backlog_max", {}).get("with_twin"),
                "processing_timeout_total_without_twin": metric_map.get("processing_timeout_total", {}).get("without_twin"),
                "processing_timeout_total_with_twin": metric_map.get("processing_timeout_total", {}).get("with_twin"),
            }
        )
    return {
        "pairs": items,
        "missing_scenarios": sorted(missing_scenarios),
        "global_conclusion": global_conclusion,
    }


def main():
    args = parse_args()
    runs = collect_runs()
    declared_scenarios = collect_declared_scenarios()
    pairs = pair_runs(runs)
    paired_scenarios = {pair["scenario_id"] for pair in pairs}
    missing_scenarios = set(declared_scenarios) - paired_scenarios

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_dir = resolve_output_dir(args.output_dir, timestamp)
    ensure_dir(output_dir)
    ensure_dir(output_dir / "scenarios")

    analysis_manifest = {
        "analysis_id": output_dir.name,
        "generated_at": iso_now(),
        "source_runs_dir": display_path(RUNS_DIR),
        "output_dir": display_path(output_dir),
        "pair_count": len(pairs),
        "declared_scenarios": len(declared_scenarios),
    }

    global_conclusion = build_global_conclusion(pairs, missing_scenarios)
    analysis_summary = build_analysis_summary(pairs, missing_scenarios, global_conclusion)

    for pair in pairs:
        write_pair_outputs(output_dir, pair)

    (output_dir / "manifest.json").write_text(json.dumps(analysis_manifest, indent=2))
    (output_dir / "summary.json").write_text(json.dumps(analysis_summary, indent=2))
    write_csv(output_dir / "summary.csv", SUMMARY_HEADERS, analysis_summary["pairs"])
    (output_dir / "report.md").write_text(
        build_global_report(pairs, missing_scenarios, global_conclusion, analysis_manifest)
    )

    print(f"Analise salva em {display_path(output_dir)}")
    print(f"Pares analisados: {len(pairs)}")
    if missing_scenarios:
        print("Cenarios sem par completo: " + ", ".join(sorted(missing_scenarios)))


if __name__ == "__main__":
    main()
