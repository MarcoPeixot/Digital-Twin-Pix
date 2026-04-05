# CLAUDE

## System working agreement

You are implementing an academic MVP of a digital twin for monitoring and mitigating degradation under high concurrent load in a transactional system inspired by Pix.

You must:

* read `/docs/*.md` before coding;
* follow `/prompts/prompt-mestre.md` behavior;
* prefer the smallest viable implementation;
* keep the system modular and observable;
* avoid requirement invention;
* keep every experiment reproducible.

Before writing code, always output:

* objective;
* supporting docs;
* included scope;
* excluded scope;
* implementation plan.

After writing code, always output:

* files changed;
* how to run;
* how to validate;
* limitations;
* scope adherence check.

Never do the following unless explicitly instructed:

* add production-grade infrastructure;
* add complex auth;
* add advanced ML;
* add cloud coupling;
* add architectural layers without immediate need.
