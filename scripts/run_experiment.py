#!/usr/bin/env python3
import argparse
import hashlib
import json
import pathlib
import socket
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone


ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULTS_PATH = ROOT / "experiments" / "defaults.json"
SCENARIOS_DIR = ROOT / "experiments" / "scenarios"
RESULTS_DIR = ROOT / "results" / "runs"

PROMETHEUS_QUERIES = {
    "api_gateway_latency_p95_ms": 'twinpix_transaction_duration_seconds{quantile="0.95"} * 1000',
    "processing_latency_p95_ms": 'twinpix_processing_duration_seconds{quantile="0.95"} * 1000',
    "directory_latency_p95_ms": 'twinpix_key_lookup_duration_seconds{quantile="0.95"} * 1000',
    "api_gateway_success_total": 'twinpix_transactions_total{status="success"}',
    "api_gateway_error_total": 'twinpix_transactions_total{status="error"}',
    "processing_success_total": 'twinpix_processing_total{status="success"}',
    "processing_error_total": 'twinpix_processing_total{status="error"}',
    "directory_success_total": 'twinpix_key_lookups_total{status="success"}',
    "directory_error_total": 'twinpix_key_lookups_total{status="error"}',
    "processing_queue_depth": "twinpix_processing_queue_depth",
    "processing_backlog_max": "twinpix_processing_backlog_max",
    "processing_active_workers": "twinpix_processing_active_workers",
    "processing_worker_capacity": "twinpix_processing_worker_capacity",
    "processing_timeout_total": "twinpix_processing_timeouts_total",
    "processing_queue_rejections_total": "twinpix_processing_queue_rejections_total",
    "twin_alerts_total": "sum(twin_alerts_total)",
    "twin_recommendations_total": "sum(twin_recommendations_total)",
}


def parse_args():
    parser = argparse.ArgumentParser(description="Executa cenarios experimentais reproduziveis do MVP.")
    parser.add_argument("--scenario", required=True, help="Arquivo JSON do cenario ou id do cenario")
    parser.add_argument("--mode", choices=["with-twin", "without-twin"], required=True)
    parser.add_argument("--keep-up", action="store_true", help="Mantem os containers em execucao ao final")
    parser.add_argument("--skip-build", action="store_true", help="Nao usa --build no docker compose up")
    return parser.parse_args()


def run(command, *, env=None, cwd=ROOT, capture=False):
    kwargs = {
        "cwd": str(cwd),
        "env": env,
        "text": True,
        "check": True,
    }
    if capture:
        kwargs["stdout"] = subprocess.PIPE
        kwargs["stderr"] = subprocess.PIPE
    else:
        print("+", " ".join(command))
    return subprocess.run(command, **kwargs)


def load_json(path):
    return json.loads(path.read_text())


def resolve_scenario_path(scenario_arg):
    candidate = pathlib.Path(scenario_arg)
    if candidate.is_file():
        return candidate.resolve()
    scenario_file = SCENARIOS_DIR / f"{scenario_arg}.json"
    if scenario_file.is_file():
        return scenario_file
    matches = list(SCENARIOS_DIR.glob(f"{scenario_arg}*.json"))
    if len(matches) == 1:
        return matches[0]
    raise FileNotFoundError(f"Cenario nao encontrado: {scenario_arg}")


def deep_merge(base, override):
    result = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def json_hash(data):
    payload = json.dumps(data, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def fetch_json(url, timeout=5):
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return json.loads(response.read().decode())


def wait_for_json(url, expected_key="status", expected_value="UP", timeout_seconds=180):
    deadline = time.time() + timeout_seconds
    last_error = None
    while time.time() < deadline:
        try:
            payload = fetch_json(url)
            if expected_key is None:
                return payload
            value = payload.get(expected_key)
            if value == expected_value or str(value).lower() == str(expected_value).lower():
                return payload
        except Exception as exc:  # noqa: BLE001
            last_error = exc
        time.sleep(2)
    raise RuntimeError(f"Timeout aguardando {url}: {last_error}")


def wait_for_http_ok(url, timeout_seconds=180):
    deadline = time.time() + timeout_seconds
    last_error = None
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=5) as response:
                if 200 <= response.status < 300:
                    return True
        except Exception as exc:  # noqa: BLE001
            last_error = exc
        time.sleep(2)
    raise RuntimeError(f"Timeout aguardando {url}: {last_error}")


def http_get_json(url):
    try:
        return fetch_json(url)
    except Exception as exc:  # noqa: BLE001
        return {"available": False, "error": str(exc)}


def prometheus_query(base_url, query):
    query_url = f"{base_url}/api/v1/query?{urllib.parse.urlencode({'query': query})}"
    try:
        response = fetch_json(query_url)
        result = response.get("data", {}).get("result", [])
        if not result:
            return None
        if len(result) == 1:
            return float(result[0]["value"][1])
        return sum(float(series["value"][1]) for series in result)
    except Exception:  # noqa: BLE001
        return None


def git_metadata():
    commit = run(["git", "rev-parse", "HEAD"], capture=True).stdout.strip()
    status = run(["git", "status", "--short"], capture=True).stdout.strip()
    branch = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture=True).stdout.strip()
    return {
        "commit": commit,
        "branch": branch,
        "dirty": bool(status),
        "status": status.splitlines() if status else [],
    }


def k6_env(experiment):
    return {
        "TARGET_BASE_URL": "http://api-gateway:8080",
        "LOAD_PROFILE_JSON": json.dumps(experiment["load_profile"]),
        "TRANSACTION_AMOUNT": str(experiment["transaction"]["amount"]),
        "SOURCE_KEY": experiment["transaction"]["source_key"],
        "DESTINATION_KEYS_JSON": json.dumps(experiment["transaction"]["destination_keys"]),
    }


def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return sock.getsockname()[1]


def allocate_host_ports(mode):
    ports = {
        "POSTGRES_PORT": find_free_port(),
        "KAFKA_PORT": find_free_port(),
        "API_GATEWAY_PORT": find_free_port(),
        "DIRECTORY_PORT": find_free_port(),
        "PROCESSING_CORE_PORT": find_free_port(),
        "PROMETHEUS_PORT": find_free_port(),
        "GRAFANA_PORT": find_free_port(),
    }
    if mode == "with-twin":
        ports["DIGITAL_TWIN_PORT"] = find_free_port()
    return ports


def service_urls(host_ports, mode):
    urls = {
        "api_gateway": f"http://localhost:{host_ports['API_GATEWAY_PORT']}",
        "directory": f"http://localhost:{host_ports['DIRECTORY_PORT']}",
        "processing_core": f"http://localhost:{host_ports['PROCESSING_CORE_PORT']}",
        "prometheus": f"http://localhost:{host_ports['PROMETHEUS_PORT']}",
        "grafana": f"http://localhost:{host_ports['GRAFANA_PORT']}",
    }
    if mode == "with-twin":
        urls["digital_twin"] = f"http://localhost:{host_ports['DIGITAL_TWIN_PORT']}"
    return urls


def materialize_env_file(experiment, host_ports):
    env_lines = [
        f"POSTGRES_PORT={host_ports['POSTGRES_PORT']}",
        f"KAFKA_PORT={host_ports['KAFKA_PORT']}",
        f"API_GATEWAY_PORT={host_ports['API_GATEWAY_PORT']}",
        f"DIRECTORY_PORT={host_ports['DIRECTORY_PORT']}",
        f"PROCESSING_CORE_PORT={host_ports['PROCESSING_CORE_PORT']}",
        f"PROMETHEUS_PORT={host_ports['PROMETHEUS_PORT']}",
        f"GRAFANA_PORT={host_ports['GRAFANA_PORT']}",
        f"DIRECTORY_EXPERIMENT_LATENCY_MS={experiment['services']['directory']['latency_ms']}",
        f"DIRECTORY_EXPERIMENT_LATENCY_JITTER_MS={experiment['services']['directory']['latency_jitter_ms']}",
        f"DIRECTORY_EXPERIMENT_ERROR_RATE={experiment['services']['directory']['error_rate']}",
        f"PROCESSING_EXPERIMENT_DELAY_MS={experiment['services']['processing_core']['delay_ms']}",
        f"PROCESSING_EXPERIMENT_DELAY_JITTER_MS={experiment['services']['processing_core']['delay_jitter_ms']}",
        f"PROCESSING_EXPERIMENT_ERROR_RATE={experiment['services']['processing_core']['error_rate']}",
        f"PROCESSING_EXPERIMENT_WORKER_COUNT={experiment['services']['processing_core']['worker_count']}",
        f"PROCESSING_EXPERIMENT_QUEUE_CAPACITY={experiment['services']['processing_core']['queue_capacity']}",
        f"PROCESSING_EXPERIMENT_QUEUE_WAIT_TIMEOUT_MS={experiment['services']['processing_core']['queue_wait_timeout_ms']}",
        f"TWIN_POLL_INTERVAL_SECONDS={experiment['services']['digital_twin']['poll_interval_seconds']}",
    ]
    if "DIGITAL_TWIN_PORT" in host_ports:
        env_lines.append(f"DIGITAL_TWIN_PORT={host_ports['DIGITAL_TWIN_PORT']}")
    temp_file = tempfile.NamedTemporaryFile("w", delete=False, prefix="twinpix-exp-", suffix=".env")
    temp_file.write("\n".join(env_lines) + "\n")
    temp_file.close()
    return pathlib.Path(temp_file.name)


def service_list(mode):
    base = ["postgres", "kafka", "prometheus", "grafana", "directory", "processing-core", "api-gateway"]
    if mode == "with-twin":
        base.append("digital-twin")
    return base


def docker_compose(project_name, env_file, args):
    return [
        "docker", "compose",
        "--project-name", project_name,
        "--env-file", str(env_file),
        *args,
    ]


def collect_results(experiment, run_dir, mode, service_base_urls, started_at, finished_at):
    prometheus_url = service_base_urls["prometheus"]
    metrics = {name: prometheus_query(prometheus_url, query) for name, query in PROMETHEUS_QUERIES.items()}

    twin_state = {}
    twin_events = {}
    if mode == "with-twin":
        twin_url = service_base_urls["digital_twin"]
        twin_state = http_get_json(f"{twin_url}/state")
        twin_events = {
            "alerts": http_get_json(f"{twin_url}/alerts"),
            "recommendations": http_get_json(f"{twin_url}/recommendations"),
            "mitigation_status": http_get_json(f"{twin_url}/mitigation/status"),
        }

    prometheus_snapshot = {
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "queries": PROMETHEUS_QUERIES,
        "values": metrics,
    }

    run_dir.joinpath("prometheus-snapshot.json").write_text(json.dumps(prometheus_snapshot, indent=2))
    run_dir.joinpath("twin-state.json").write_text(json.dumps(twin_state, indent=2))
    run_dir.joinpath("events.json").write_text(json.dumps(twin_events, indent=2))

    summary = {
        "run_id": run_dir.name,
        "scenario_id": experiment["id"],
        "mode": mode,
        "started_at": started_at,
        "finished_at": finished_at,
        "metrics": metrics,
        "observed_result": {
            "degraded": bool((metrics.get("api_gateway_error_total") or 0) > 0 or (metrics.get("processing_backlog_max") or 0) > 0),
            "twin_alerts_emitted": metrics.get("twin_alerts_total"),
            "twin_recommendations_emitted": metrics.get("twin_recommendations_total"),
        },
        "interpretation": "Resumo automatico inicial. A analise final detalhada permanece fora do escopo desta tarefa."
    }
    run_dir.joinpath("summary.json").write_text(json.dumps(summary, indent=2))


def main():
    args = parse_args()

    defaults = load_json(DEFAULTS_PATH)["defaults"]
    scenario_path = resolve_scenario_path(args.scenario)
    scenario = load_json(scenario_path)
    experiment = deep_merge(defaults, scenario)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_id = f"{timestamp}__{experiment['id']}__{args.mode}"
    project_name = f"twinpix-{timestamp.lower()}"
    run_dir = RESULTS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=False)

    host_ports = allocate_host_ports(args.mode)
    base_urls = service_urls(host_ports, args.mode)
    env_file = materialize_env_file(experiment, host_ports)
    git_info = git_metadata()
    effective_config_hash = json_hash(experiment)

    manifest = {
      "run_id": run_id,
      "objective": "Execucao reproduzivel de cenario experimental do MVP",
      "scope": {
        "included": [
          "cenario versionado",
          "execucao controlada",
          "modo com ou sem twin",
          "coleta padronizada de resultados",
          "identificacao de versao e configuracao"
        ],
        "limitations": [
          "sem dashboard avancado",
          "sem analise final detalhada",
          "sem machine learning",
          "sem mitigacao automatica real"
        ]
      },
      "scenario": {
        "path": str(scenario_path.relative_to(ROOT)),
        "sha256": sha256(scenario_path),
        "id": experiment["id"],
        "name": experiment["name"],
      },
      "mode": args.mode,
      "effective_config_sha256": effective_config_hash,
      "git": git_info,
      "docker_project_name": project_name,
      "host_ports": host_ports,
      "service_base_urls": base_urls,
      "created_at": datetime.now(timezone.utc).isoformat(),
    }
    run_dir.joinpath("manifest.json").write_text(json.dumps(manifest, indent=2))
    run_dir.joinpath("scenario.json").write_text(json.dumps(scenario, indent=2))
    run_dir.joinpath("effective-config.json").write_text(json.dumps(experiment, indent=2))

    services = service_list(args.mode)
    compose_up = docker_compose(
        project_name,
        env_file,
        ["up", "-d", *(["--build"] if not args.skip_build else []), *services],
    )

    started_at = datetime.now(timezone.utc).isoformat()
    try:
        run(compose_up)
        wait_for_json(f"{base_urls['api_gateway']}/actuator/health")
        wait_for_json(f"{base_urls['directory']}/actuator/health")
        wait_for_json(f"{base_urls['processing_core']}/actuator/health")
        wait_for_http_ok(f"{base_urls['prometheus']}/-/healthy")
        if args.mode == "with-twin":
            wait_for_json(f"{base_urls['digital_twin']}/health", expected_value="up")

        time.sleep(experiment["collection"]["warmup_seconds"])

        summary_path = run_dir / "load-summary.json"
        k6_command = [
            "docker", "run", "--rm",
            "--network", f"{project_name}_default",
            "-v", f"{ROOT}:/workspace",
            "-w", "/workspace",
        ]
        for key, value in k6_env(experiment).items():
            k6_command.extend(["-e", f"{key}={value}"])
        k6_command.extend([
            "grafana/k6:0.49.0",
            "run",
            "--summary-export", f"/workspace/{summary_path.relative_to(ROOT)}",
            "tools/load-generator/script.js",
        ])
        run(k6_command)

        time.sleep(experiment["collection"]["cooldown_seconds"])
        finished_at = datetime.now(timezone.utc).isoformat()
        collect_results(experiment, run_dir, args.mode, base_urls, started_at, finished_at)
    finally:
        if not args.keep_up:
            try:
                run(docker_compose(project_name, env_file, ["down", "-v"]))
            except subprocess.CalledProcessError:
                pass
        env_file.unlink(missing_ok=True)

    print(f"Execucao concluida: {run_dir.relative_to(ROOT)}")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        print(exc.stdout or "", file=sys.stdout)
        print(exc.stderr or "", file=sys.stderr)
        raise
