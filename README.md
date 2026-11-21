# AI-Augmented SDLC Assignment 1

This repository is being built in specification-first milestones for Assignment 1.

## Parts

- **Part 1A** — deterministic Smart Todo API; implementation and all release gates verified.
- **Part 1B** — non-deterministic Natural Language Reminder Agent using the approved
  `gemini-3.5-flash-lite` model; configuration, local validation, provider integration,
  story flows, CLI, and offline evaluation foundations are implemented. Full evaluation
  orchestration and release verification remain.

Each part will keep its requirements, design, tests, implementation, and validation evidence
together. The two `harness-log.md` files are intentionally ignored by Git because the student
will author them after implementation and verification are complete.

## Current state

Part 1A is complete and verified on branch `001-smart-todo-api` through `1f80a52`; its
implementation, release evidence, and clean-checkout verification have been pushed to the
feature branch. The baseline is tagged `part-1a-pre-implementation`. Part 1B's specification,
plan, tasks, and traceability are approved using the existing Part 1B specification from the
prior `Assignment_1` checkout as its requirements baseline. Part 1B now has versioned
development/held-out datasets, executable requirement traceability, safe response
serialization, and deterministic offline scoring tests. No live Gemini evaluation has been
run.

The student-authored harness logs for both parts remain pending and are intentionally not
created or committed by the agent.
