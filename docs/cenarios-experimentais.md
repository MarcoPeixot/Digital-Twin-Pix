# Cenarios Experimentais

## 1. Objetivo

Definir os cenarios controlados usados para validar o comportamento do sistema e do gêmeo digital.

## 2. Cenarios base

### Cenario 1 - Operacao normal

Objetivo:
Estabelecer baseline.

Condicoes:

* volume moderado;
* sem falhas induzidas;
* baixa fila;
* baixa taxa de erro.

### Cenario 2 - Pico repentino de acesso

Objetivo:
Avaliar degradacao por concorrencia.

Condicoes:

* aumento abrupto de taxa de requisicoes;
* pressao sobre filas e processamento;
* risco de aumento de latencia e timeout.

### Cenario 3 - Degradacao do Directory Service

Objetivo:
Avaliar impacto de lentidao em dependencia critica.

Condicoes:

* aumento artificial de latencia;
* possiveis falhas intermitentes;
* propagacao da degradacao.

### Cenario 4 - Saturacao da fila

Objetivo:
Avaliar acumulo e perda de capacidade.

Condicoes:

* consumidores insuficientes;
* backlog crescente;
* tempo medio de permanencia elevado.

### Cenario 5 - Falha parcial do Processing Core

Objetivo:
Avaliar resiliencia do sistema e reacao do gêmeo.

Condicoes:

* reducao de capacidade;
* falha em parte dos workers;
* aumento da taxa de erro.

## 3. Modos de execucao

Cada cenario deve ser executado em dois modos:

* sem gêmeo digital ativo;
* com gêmeo digital ativo.

## 4. Variaveis controladas

* taxa de entrada;
* concorrencia;
* numero de workers;
* latencia artificial;
* tamanho de fila;
* timeout.

## 5. Criterios de comparacao

* tempo ate degradacao perceptivel;
* tempo ate saturacao;
* latencia media e p95/p99;
* taxa de erro;
* backlog maximo;
* tempo de recuperacao.
