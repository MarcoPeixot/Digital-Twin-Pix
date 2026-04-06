# Resultados

## 1. Objetivo

Padronizar o registro e analise dos resultados experimentais.

## 2. Estrutura minima por experimento

* nome do cenario;
* data/hora da execucao;
* configuracao usada;
* versao do codigo;
* modo de execucao (com/sem gêmeo);
* metricas coletadas;
* eventos relevantes;
* resultado observado;
* interpretacao.

## 3. Estrutura de analise

### 3.1 Baseline

Descrever o comportamento normal.

### 3.2 Degradacao observada

Descrever como e quando o sistema comecou a degradar.

### 3.3 Comportamento do gêmeo

Descrever o que foi detectado, quando e com qual confianca/regra.

### 3.4 Mitigacao

Descrever qual acao foi recomendada ou aplicada.

### 3.5 Efeito da mitigacao

Descrever impacto quantitativo e qualitativo.

## 4. Formato esperado

Os resultados devem combinar:

* tabelas comparativas;
* graficos simples ou de series temporais, conforme os artefatos disponiveis;
* texto analitico;
* conclusao objetiva por cenario.

## 4.1 Saidas consolidadas no repositorio

A analise final pode ser materializada em `/results/analysis/<timestamp>` contendo:

* `manifest.json`;
* `summary.json`;
* `summary.csv`;
* `report.md`;
* `scenarios/<scenario_id>/comparison.json`;
* `scenarios/<scenario_id>/comparison.csv`;
* `scenarios/<scenario_id>/report.md`;
* `scenarios/<scenario_id>/chart-<scenario_id>.svg`.

## 5. Perguntas que todo resultado deve responder

* O sistema degradou?
* Em que ponto a degradacao comecou?
* O gêmeo detectou antes da falha evidente?
* A mitigacao melhorou o comportamento?
* O ganho foi mensuravel?
