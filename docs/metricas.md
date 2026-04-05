# Metricas

## 1. Objetivo

Definir metricas operacionais, analiticas e experimentais do MVP.

## 2. Metricas transacionais

* throughput (req/s);
* latencia media;
* latencia p95;
* latencia p99;
* taxa de sucesso;
* taxa de erro;
* taxa de timeout.

## 3. Metricas de fila e processamento

* tamanho atual da fila;
* backlog maximo;
* tempo medio em fila;
* taxa de consumo;
* utilizacao de workers;
* taxa de retries.

## 4. Metricas por componente

### Directory Service

* tempo medio de consulta;
* taxa de erro;
* disponibilidade.

### Processing Core

* tempo medio de processamento;
* taxa de falha;
* numero de workers ativos.

### Twin Core

* tempo de decisao;
* numero de alertas emitidos;
* numero de mitigacoes acionadas;
* taxa de acerto da deteccao, quando aplicavel.

## 5. Metricas experimentais

* tempo ate detectar degradacao;
* antecedencia da deteccao em relacao a falha visivel;
* reducao percentual de latencia sob mitigacao;
* reducao de erro com gêmeo ativo;
* reducao de backlog com gêmeo ativo;
* tempo de recuperacao apos mitigacao.

## 6. Regras para metricas

* Toda metrica deve ter nome padronizado.
* Toda metrica deve ter unidade explicita.
* Toda metrica deve poder ser reproduzida entre execucoes.
* Metricas devem ser comparaveis entre cenarios.
