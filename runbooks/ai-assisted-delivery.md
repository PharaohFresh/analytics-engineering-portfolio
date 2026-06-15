# Runbook: AI-Assisted Delivery (Governed Acceleration)

This repo was built with an AI coding agent used as an **accountable accelerator** — the same
governed pattern I run on production platforms. The differentiator isn't "I used AI"; it's *where
the human gate sits* and *how the work stays verifiable*.

## Where AI helped
- Drafting staging models from source column lists (mechanical rename/typing).
- Generating first-pass `schema.yml` tests and model descriptions.
- Writing boilerplate (runbooks, PR template, the `qa_audit.py` skeleton).

## Where the human stays in control (the gates)
- **Grain and modeling decisions are mine**, stated before any SQL is generated. AI doesn't get to invent the grain.
- **Every generated model is read and run in dev before it's trusted** — nothing is merged because "the agent wrote it."
- **Tests are the contract.** AI-drafted tests are reviewed; a model ships only when `dbt build` is green AND `qa_audit.py` reconciles independently.
- **No prod access from the agent.** Promotion to prod is PR-based with human approval (see `GOVERNANCE.md`).
- **No secrets in context.** Credentials live in gitignored `profiles.yml`, never pasted into a prompt.

## Why this matters
Speed without verification is a liability in data work — a wrong number that looks confident is worse
than no number. This setup keeps the velocity of AI assistance while preserving the audit trail and
human accountability that make the output trustworthy.
