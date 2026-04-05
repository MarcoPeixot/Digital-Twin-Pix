# Prompt Mestre

Voce esta trabalhando no MVP academico de um gêmeo digital para monitoramento e mitigacao de degradacao operacional em um sistema transacional inspirado no ecossistema do Pix.

Antes de qualquer implementacao, leia obrigatoriamente:

* `/docs/contexto-negocio.md`
* `/docs/processos.md`
* `/docs/componentes.md`
* `/docs/arquitetura.md`
* `/docs/cenarios-experimentais.md`
* `/docs/metricas.md`
* `/docs/resultados.md`

Regras mandatorias:

1. Nao invente requisitos fora dos documentos.
2. Nao amplie escopo sem justificativa explicita.
3. Priorize a menor implementacao viavel.
4. Toda decisao deve ser rastreavel para algum arquivo de `/docs`.
5. Sempre explicite premissas antes de codar.
6. Sempre liste o que esta fora do escopo da tarefa atual.
7. Gere codigo modular, testavel e executavel localmente com Docker Compose.
8. Toda alteracao deve preservar observabilidade minima.
9. Nao introduza dependencias pesadas sem necessidade clara.
10. Ao final, reporte aderencia ao escopo e arquivos alterados.

Formato obrigatorio de resposta antes de implementar:

* Objetivo da tarefa
* Documentos usados
* Escopo incluido
* Escopo excluido
* Plano de implementacao

Formato obrigatorio ao final:

* Arquivos criados/alterados
* Como executar
* Como validar
* Riscos ou limitacoes
* Checagem de aderencia ao `/docs`
