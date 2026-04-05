# Contexto de Negocio

## 1. Visao geral

Este projeto de iniciacao cientifica investiga como um gêmeo digital pode ser utilizado para monitorar, prever degradacoes e apoiar acoes preventivas em cenarios de picos de acessos simultaneos em sistemas criticos.

O caso de uso adotado e um ambiente simplificado inspirado no ecossistema do Pix, com enfase em comportamento operacional, concorrencia, filas, latencia e falhas sob carga. O objetivo nao e reproduzir integralmente o Pix real, suas normas completas ou seu funcionamento institucional detalhado. O objetivo e construir um ambiente experimental tecnicamente coerente que represente, de forma simplificada, componentes analogos como:

* modulo de diretorio de chaves (inspirado no DICT);
* modulo de liquidacao/processamento central (inspirado no SPI);
* mensageria e filas internas;
* observabilidade operacional;
* gêmeo digital para espelhamento e decisao.

## 2. Problema de negocio

Sistemas criticos sujeitos a grande volume transacional podem sofrer degradacao rapida durante picos de acesso. Em muitos cenarios, a deteccao ocorre tarde demais, quando ja existem filas acumuladas, aumento de latencia, timeouts e falhas em cascata.

O problema central investigado e:

**Como um gêmeo digital pode representar o estado operacional de um sistema de pagamentos sob alta concorrencia e permitir deteccao antecipada de risco, recomendacao de acoes e eventual mitigacao automatica?**

## 3. Objetivo geral

Projetar e validar um MVP de gêmeo digital capaz de:

* espelhar o estado operacional do sistema transacional simulado;
* monitorar sinais de degradacao;
* detectar padroes de risco em tempo quase real;
* recomendar ou executar acoes de mitigacao;
* produzir evidencias experimentais comparando operacao com e sem gêmeo digital.

## 4. Objetivos especificos

* Construir um simulador simplificado do fluxo transacional.
* Produzir cenarios controlados de pico de carga e falha.
* Instrumentar o ambiente com metricas, eventos e logs.
* Implementar o nucleo do gêmeo digital baseado inicialmente em regras.
* Medir impacto do uso do gêmeo em latencia, erros, backlog e recuperacao.

## 5. Escopo do MVP

Inclui:

* simulacao de fluxo transacional simplificado;
* geracao de carga concorrente;
* coleta de metricas operacionais;
* modelo de estado do gêmeo digital;
* motor de decisao baseado em regras;
* acoes de mitigacao em ambiente controlado.

Nao inclui:

* integracao com infraestrutura bancaria real;
* conformidade regulatoria integral do Pix real;
* liquidacao financeira real;
* seguranca bancaria real completa;
* machine learning avancado na primeira versao;
* interface visual complexa fora do necessario para demonstracao.

## 6. Premissas

* O ambiente e academico e experimental.
* O foco e comportamento sistemico, nao fidelidade regulatoria total.
* O gêmeo digital deve operar sobre dados observaveis do ambiente simulado.
* O MVP deve ser pequeno, explicavel e reproduzivel.

## 7. Criterios de sucesso

O MVP sera considerado bem-sucedido se:

* o fluxo transacional simplificado funcionar ponta a ponta;
* o sistema puder ser degradado por cenarios de pico/falha;
* o gêmeo conseguir refletir o estado operacional;
* o gêmeo detectar risco antes do colapso total em pelo menos parte dos cenarios;
* exista comparacao quantitativa entre execucao com e sem gêmeo digital.

## 8. Restricoes

* Tempo de desenvolvimento limitado.
* Desenvolvimento majoritariamente assistido por IA.
* Arquitetura deve ser modular e facil de explicar academicamente.
* O projeto deve evitar complexidade desnecessaria.
