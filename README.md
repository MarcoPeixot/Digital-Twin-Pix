# Projeto

MVP academico de gêmeo digital para monitoramento e mitigacao de degradacao operacional em sistema transacional inspirado no ecossistema do Pix.

## Objetivo

Demonstrar, em ambiente experimental reproduzivel, como um gêmeo digital pode observar o estado operacional de um sistema sob pico de carga, detectar risco e recomendar ou aplicar mitigacao.

## Fonte de verdade

Toda definicao do projeto esta na pasta `/docs`.

## Como trabalhar com IA

* use os arquivos em `/prompts`;
* siga as regras de `AGENTS.md` e `CLAUDE.md`;
* trate `/tasks` como backlog operacional do MVP.

## Estrutura do repositorio

```
services/
  api-gateway/          # Spring Boot - entrada transacional (porta 8080)
  directory/            # Spring Boot - diretorio de chaves (porta 8081)
  processing-core/      # Spring Boot - processamento central (porta 8082)
  digital-twin/         # FastAPI - nucleo do gemeo digital (porta 8090)
infra/
  prometheus/           # Configuracao do Prometheus
  grafana/              # Provisioning do Grafana
tools/
  load-generator/       # Scripts k6 para teste de carga
docs/                   # Documentacao do projeto
prompts/                # Prompts para agentes de IA
tasks/                  # Backlog de tarefas
```

## Como executar localmente

### Pre-requisitos

- Docker e Docker Compose instalados

### Passos

```bash
# 1. Copiar variaveis de ambiente
cp .env.example .env

# 2. Subir todos os servicos
docker compose up --build

# 3. Verificar saude dos servicos
curl http://localhost:8080/health   # api-gateway
curl http://localhost:8081/health   # directory
curl http://localhost:8082/health   # processing-core
curl http://localhost:8090/health   # digital-twin

# 4. Acessar dashboards
# Prometheus: http://localhost:9090
# Grafana:    http://localhost:3000 (admin/admin)
```

### Parar os servicos

```bash
docker compose down
docker compose down -v   # remove volumes (dados do postgres)
```

## Como executar cenarios experimentais

Os cenarios versionados ficam em `experiments/scenarios/`.

Exemplos:

```bash
# Cenario 1 sem Twin
python3 scripts/run_experiment.py --scenario cenario-01-operacao-normal --mode without-twin

# Cenario 1 com Twin
python3 scripts/run_experiment.py --scenario cenario-01-operacao-normal --mode with-twin

# Cenario 4 com Twin, reaproveitando imagens locais ja construidas
python3 scripts/run_experiment.py --scenario cenario-04-saturacao-fila --mode with-twin --skip-build
```

Resultados:

* execucoes: `results/runs/<run_id>/`
* comparacoes: `results/comparisons/`

Comparar duas execucoes:

```bash
python3 scripts/compare_runs.py \
  --run-a 20260405T120000Z__cenario-01-operacao-normal__without-twin \
  --run-b 20260405T121000Z__cenario-01-operacao-normal__with-twin
```

## Ordem sugerida de desenvolvimento

1. bootstrap do repositorio;
2. fluxo transacional minimo;
3. observabilidade;
4. twin core;
5. mitigacao;
6. cenarios experimentais;
7. analise de resultados.
