# AI-Augmented SDLC Assignment 1

This repository is being built in specification-first milestones for Assignment 1.

## Parts

- **Part 1A** — deterministic Smart Todo API; implementation and all release gates verified.
- **Part 1B** — non-deterministic Natural Language Reminder Agent using the approved
  `gemini-3.5-flash-lite` model; configuration, local validation, provider integration,
  story flows, CLI, offline evaluation orchestration, and quickstart documentation are
  implemented. Offline release checks pass; live release evaluation remains incomplete after
  a combined run exhausted the configured 140-provider-attempt ceiling.

Each part will keep its requirements, design, tests, implementation, and validation evidence
together. The Part 1A harness log records its passing release gates. The Part 1B harness log
records offline verification and explicitly notes that live evaluation remains pending.

## Current state

Part 1A is complete and verified on branch `001-smart-todo-api` through `1f80a52`; its
implementation, release evidence, and clean-checkout verification have been pushed to the
feature branch. The baseline is tagged `part-1a-pre-implementation`. Part 1B's specification,
plan, tasks, and traceability are approved using the existing Part 1B specification from the
prior `Assignment_1` checkout as its requirements baseline. Part 1B now has versioned
development/held-out datasets, executable requirement traceability, safe response
serialization, and deterministic offline scoring tests. No live Gemini evaluation has been
run.

The Part 1B combined live Gemini evaluation stopped at the 140-provider-attempt ceiling
without producing a report. A separate one-attempt diagnostic succeeded but did not satisfy
the evaluation criteria. Its release gate remains pending until a complete approved
evaluation report is reviewed.
