# AGENTS

## Proposito

Este arquivo orienta agentes de IA que atuam no repositorio.

## Regras obrigatorias

1. Leia `/docs/*.md` antes de qualquer alteracao.
2. Use `/prompts/prompt-mestre.md` como comportamento-base.
3. Escolha sempre a implementacao minima aderente ao escopo.
4. Nao invente requisitos, integracoes ou fluxos nao documentados.
5. Nao altere contratos arquiteturais sem refletir isso em `/docs`.
6. Mantenha o projeto reproduzivel localmente.
7. Preserve metricas, logs e rastreabilidade experimental.
8. Toda mudanca deve declarar objetivo, escopo e limitacoes.

## Fluxo padrao de trabalho

1. Ler docs.
2. Fazer checagem de conformidade.
3. Propor plano curto.
4. Implementar.
5. Validar.
6. Reportar arquivos alterados e aderencia ao escopo.

## Proibicoes

* nao introduzir cloud especifica sem necessidade;
* nao adicionar autenticacao complexa ao MVP;
* nao usar Kubernetes no bootstrap inicial;
* nao criar microsservicos alem do necessario;
* nao adicionar ML avancado na primeira versao.
