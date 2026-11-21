# Traceability: Gemini Reminder Agent

This is the planning traceability baseline. Implementation symbols are planned names and
must be replaced with actual file/symbol references before implementation acceptance.
The evaluation case IDs are families; each dataset row must use a unique stable ID.

| Requirement | Story / acceptance | Planned evaluation IDs | Planned tests | Planned implementation |
|---|---|---|---|---|
| FR-001 | US-001..US-003, AC-001..AC-008 | `EV-INTENT-*` | `TEST-INTENT-*` | `prompt.build_request`, `evaluation.score_semantics` |
| FR-002 | US-001, AC-001..AC-002 | `EV-CREATE-*` | `TEST-CREATE-*` | `prompt.build_request`, `validation.validate_action` |
| FR-003 | US-002, AC-003, AC-005 | `EV-RESCHEDULE-*` | `TEST-RESCHEDULE-*` | `validation.validate_target` |
| FR-004 | US-002, AC-004..AC-005 | `EV-SNOOZE-*` | `TEST-SNOOZE-*` | `validation.validate_datetime` |
| FR-005 | US-001..US-003, AC-002, AC-005..AC-006 | `EV-CLARIFY-*` | `TEST-CLARIFICATION-*` | `validation.validate_action` |
| FR-006 | AC-009 | `EV-SCHEMA-*` | `TEST-OUTPUT-*` | `output.serialize_response` |
| FR-007 | AC-009 | `EV-SCHEMA-*` | `TEST-SCHEMA-*` | `validation.validate_response_schema` |
| FR-008 | US-003, AC-006..AC-008 | `EV-PROP-*` | `TEST-VALIDATION-*` | `validation.validate_request`, `validation.validate_action` |
| FR-009 | US-003, AC-006..AC-008, AC-012 | `EV-INVALID-*`, `EV-NO-SIDE-EFFECT-*` | `TEST-SAFE-INPUT-*` | `validation.validate_request`, `cli.run` |
| FR-010 | AC-010 | `EV-TRACE-*` | `TEST-TRACEABILITY-*` | `evaluation.validate_traceability` |
| FR-011 | AC-010 | `EV-HARNESS-*`, `EV-REPORT-*` | `TEST-EVALUATION-*` | `evaluation.run_evaluation`, `evaluation.write_report` |
| FR-012 | AC-009, AC-011 | `EV-GEMINI-CALL-*` | `TEST-GEMINI-ADAPTER-*` | `gemini_client.GeminiAdapter.generate` |
| FR-013 | AC-008..AC-009, AC-011..AC-012 | `EV-UNTRUSTED-*`, `EV-INVALID-MODEL-*` | `TEST-MODEL-BOUNDARY-*` | `prompt.build_request`, `validation.validate_action` |
| FR-014 | AC-010..AC-011 | `EV-SECRET-*`, `EV-ERROR-REDACTION-*` | `TEST-CONFIG-PRIVACY-*` | `config.load_settings`, `evaluation.write_report` |
| NFR-001 | AC-009 | `EV-SCHEMA-*` | `TEST-SCHEMA-THRESHOLD` | `validation.validate_response_schema` |
| NFR-002 | AC-006..AC-009 | `EV-PROP-*` | `TEST-PROPERTY-THRESHOLD` | `validation.validate_action` |
| NFR-003 | AC-001..AC-007 | `EV-SEMANTIC-*`, `EV-CLARIFY-*` | `TEST-SEMANTIC-THRESHOLD` | `evaluation.score_semantics` |
| NFR-004 | AC-010 | `EV-REPORT-VERSION-*` | `TEST-REPRODUCIBILITY-*` | `evaluation.write_report` |
| NFR-005 | AC-009..AC-010 | `EV-QUALITY-*` | `TEST-QUALITY-GATES` | CI configuration |
| NFR-006 | AC-009 | `EV-COVERAGE-*` | `TEST-COVERAGE-*` | core validation/adapter/output modules |
| NFR-007 | AC-008, AC-010..AC-011 | `EV-PRIVACY-*`, `EV-ERROR-REDACTION-*` | `TEST-PRIVACY-*` | `cli.run`, `evaluation.write_report` |
| NFR-008 | AC-010 | `EV-DOC-*` | `TEST-DOCUMENTATION-*` | `specs/001-reminder-agent/` |
| NFR-009 | AC-009 | `EV-REPEATED-CALL-*` | `TEST-NONDETERMINISM-*` | `gemini_client.GeminiAdapter`, `evaluation.run_evaluation` |
| NFR-010 | AC-011 | `EV-CALL-BUDGET-*`, `EV-TIMEOUT-*` | `TEST-BUDGET-RETRY-*` | `config.load_settings`, `evaluation.run_evaluation` |

**Acceptance gate**: each FR/NFR must link to at least one concrete evaluation row, test
identifier, and implemented source symbol. Missing links fail the traceability test and
release harness.
