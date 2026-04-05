# Componentes

## 1. Visao de componentes

O MVP deve ser composto por modulos pequenos e claramente separados.

## 2. Componentes principais

### 2.1 Load Generator

Responsavel por gerar trafego controlado.

Responsabilidades:

* simular volume de requisicoes;
* controlar concorrencia;
* reproduzir cenarios experimentais.

Nao responsabilidades:

* logica do gêmeo digital;
* persistencia analitica principal.

### 2.2 API Gateway / Transaction Ingress

Responsavel por receber solicitacoes de transacao.

Responsabilidades:

* expor endpoint principal;
* validar payload minimo;
* encaminhar para fluxo interno;
* registrar tempos de entrada.

### 2.3 Directory Service

Analogo simplificado ao diretorio de chaves.

Responsabilidades:

* consultar chave de destino;
* responder com dados simulados necessarios ao fluxo;
* permitir simulacao de degradacao.

### 2.4 Processing Core

Analogo simplificado ao processamento central.

Responsabilidades:

* processar a transacao;
* interagir com fila se necessario;
* registrar sucesso, falha ou timeout;
* expor metricas do processamento.

### 2.5 Queue/Broker

Responsavel por desacoplamento assincrono.

Responsabilidades:

* enfileirar eventos internos;
* suportar medicao de backlog;
* permitir simulacao de saturacao.

### 2.6 State Store / Database

Responsavel por persistencia minima.

Responsabilidades:

* armazenar transacoes simuladas;
* armazenar eventos relevantes;
* suportar consulta para analise posterior.

### 2.7 Observability Collector

Responsavel por consolidar dados observaveis.

Responsabilidades:

* coletar metricas e eventos;
* disponibilizar insumos ao gêmeo digital;
* registrar series temporais e logs relevantes.

### 2.8 Digital Twin Core

Responsavel pelo gêmeo digital.

Responsabilidades:

* manter representacao do estado operacional;
* calcular indicadores de saude;
* aplicar regras de deteccao;
* recomendar ou executar mitigacao.

### 2.9 Mitigation Controller

Responsavel por aplicar acoes.

Responsabilidades:

* ajustar parametros do ambiente;
* acionar throttling;
* aumentar workers simulados;
* isolar componente degradado quando configurado.

### 2.10 Dashboard / Visualization

Responsavel por exibir resultados.

Responsabilidades:

* mostrar estado operacional;
* exibir alertas;
* comparar cenarios experimentais.

## 3. Contratos entre componentes

Todo componente deve definir:

* entradas;
* saidas;
* eventos emitidos;
* metricas expostas;
* falhas esperadas.

## 4. Regras de implementacao

* Componentes devem ser independentes e testaveis.
* Nao usar acoplamento implicito.
* Nao compartilhar estado mutavel sem contrato explicito.
* Toda comunicacao assincrona deve gerar evento rastreavel.
