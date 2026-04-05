# Arquitetura

## 1. Estilo arquitetural

A arquitetura do MVP sera baseada em servicos modulares, observabilidade explicita e separacao entre:

* sistema transacional simulado;
* camada de observacao;
* nucleo do gêmeo digital;
* camada de mitigacao.

## 2. Arquitetura logica

### Camada 1 - Simulacao do sistema operacional

Inclui:

* entrada transacional;
* diretorio;
* processamento central;
* filas;
* persistencia.

### Camada 2 - Telemetria e observabilidade

Inclui:

* metricas;
* logs estruturados;
* eventos;
* coleta e armazenamento observacional.

### Camada 3 - Gêmeo digital

Inclui:

* modelo de estado;
* regras de inferencia;
* classificacao de risco;
* decisao.

### Camada 4 - Mitigacao

Inclui:

* execucao de acoes;
* ajuste de parametros;
* resposta ao risco.

### Camada 5 - Analise experimental

Inclui:

* dashboards;
* relatorios;
* comparacao de cenarios.

## 3. Fluxo arquitetural resumido

1. Requisicao entra no sistema.
2. Fluxo transacional percorre diretorio e processamento.
3. Componentes emitem metricas, logs e eventos.
4. Coletor alimenta o gêmeo digital.
5. Gêmeo atualiza o estado e detecta risco.
6. Gêmeo gera alerta ou aciona mitigacao.
7. Resultado e refletido nas metricas e analisado.

## 4. Tecnologia sugerida do MVP

Esta e apenas uma sugestao-base e pode ser ajustada.

* Servicos simulados: Java Spring Boot.
* Gêmeo digital: Python FastAPI ou servico separado equivalente.
* Mensageria: Kafka.
* Persistencia: PostgreSQL.
* Cache/estado transitorio: Redis, se necessario.
* Metricas: Prometheus.
* Visualizacao: Grafana.
* Orquestracao local: Docker Compose.
* Teste de carga: k6

## 5. Principios arquiteturais

* simplicidade antes de sofisticacao;
* observabilidade nativa;
* decisoes explicaveis;
* reprodutibilidade experimental;
* baixo acoplamento;
* documentacao primeiro.

## 6. Fora de escopo arquitetural

* microsservicos excessivamente fragmentados;
* Kubernetes no MVP inicial;
* alta disponibilidade real de producao;
* seguranca regulatoria completa;
* ML avancado na primeira versao.
