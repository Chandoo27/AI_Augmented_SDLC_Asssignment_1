# Requirement Traceability: Smart Todo API

This table connects the approved `US-*`, `FR-*`, `NFR-*`, and `AC-*` IDs to task IDs, exact
pytest node IDs, and implemented source symbols.

| Requirement | Story | Acceptance criteria | Tasks | Verification IDs | Implementation references |
|---|---|---|---|---|---|
| FR-001 | US-001 | AC-001–AC-004 | T003, T006, T011, T014 | `tests/test_tasks.py::test_create_task_returns_defaults_and_utc_timestamp`; `tests/test_tasks.py::test_create_task_accepts_documented_field_boundaries`; `tests/test_tasks.py::test_description_is_trimmed`; `tests/test_tasks.py::test_invalid_create_returns_422_without_persisting`; `tests/test_tasks.py::test_duplicate_tags_are_stored_once_case_insensitively` | `TaskCreate`, `TaskService.create_task`, `routes.create_task` |
| FR-002 | US-001 | AC-002 | T003–T004, T006, T011, T014 | `tests/test_tasks.py::test_create_task_returns_defaults_and_utc_timestamp`; `tests/test_tasks.py::test_task_crud_and_partial_update` | `Task.id`, `Task.created_at`, `TaskService.create_task` |
| FR-003 | US-001, US-002 | AC-006, AC-009 | T006–T007, T014–T015 | `tests/test_tasks.py::test_task_crud_and_partial_update`; `tests/test_tasks.py::test_unknown_task_operations_use_not_found`; `tests/test_filters.py::test_tag_filter_is_case_insensitive_exact_and_match_any` | `TaskService.get_task`, `TaskService.list_tasks`, routes |
| FR-004 | US-001 | AC-005, AC-017 | T003–T004, T006, T011–T012, T014 | `tests/test_tasks.py::test_task_crud_and_partial_update`; `tests/test_tasks.py::test_invalid_update_is_rejected`; `tests/test_tasks.py::test_later_sequential_update_wins_for_same_field`; `tests/test_tasks.py::test_concurrent_updates_preserve_different_fields`; `tests/test_storage.py::test_concurrent_different_field_updates_are_serialized` | `TaskUpdate`, `TaskService.update_task`, `JsonTaskStore.transact` |
| FR-005 | US-001 | AC-006–AC-007 | T006, T014 | `tests/test_tasks.py::test_task_crud_and_partial_update`; `tests/test_tasks.py::test_unknown_task_operations_use_not_found` | `TaskService.delete_task`, `routes.delete_task` |
| FR-006 | US-003 | AC-006, AC-008, AC-016 | T008, T016 | `tests/test_tasks.py::test_complete_and_reopen_are_idempotent`; `tests/test_tasks.py::test_unknown_task_operations_use_not_found` | `TaskService.set_status`, `routes.complete_task`, `routes.reopen_task` |
| FR-007 | US-002 | AC-009 | T007, T015 | `tests/test_filters.py::test_tag_filter_is_case_insensitive_exact_and_match_any`; `tests/test_filters.py::test_repeated_tag_query_parameters_are_supported`; `tests/test_filters.py::test_filter_without_matches_returns_empty_list` | `TaskFilters`, `TaskService.list_tasks`, `routes.list_tasks` |
| FR-008 | US-002 | AC-010, AC-015 | T007, T009, T015 | `tests/test_filters.py::test_priority_sort_orders_high_medium_low`; `tests/test_filters.py::test_priority_ties_use_created_at_then_id`; `tests/test_filters.py::test_filter_and_sort_can_be_combined`; `tests/test_filters.py::test_1000_task_list_filter_and_sort_latency` | `TaskService.priority_key`, `TaskService.list_tasks` |
| FR-009 | US-003 | AC-011, AC-013 | T002, T004, T008, T012, T016 | `tests/test_storage.py::test_missing_data_file_starts_with_empty_collection`; `tests/test_storage.py::test_tasks_survive_store_recreation`; `tests/test_storage.py::test_malformed_data_is_reported_and_left_unchanged`; `tests/test_storage.py::test_fr_009_directory_at_data_path_is_reported_and_preserved`; `tests/test_storage.py::test_failed_atomic_write_preserves_previous_data`; `tests/test_tasks.py::test_task_status_and_fields_survive_application_restart` | `JsonTaskStore._read`, `JsonTaskStore._write`, `create_app` |
| FR-010 | US-001–US-003 | AC-001–AC-018 | T003, T005–T008, T011, T013–T018 | API contract node IDs in `tests/test_tasks.py` and `tests/test_filters.py`; `tests/test_harness_runner.py::test_nonzero_gate_exit_is_preserved_as_failure`; `tests/test_harness_runner.py::test_report_preserves_gate_results_and_pass_status` | `routes`, `create_app`, `.github/workflows/ci.yml` |
| FR-011 | US-001, US-003 | AC-006, AC-012–AC-013 | T005, T011–T014, T016 | `tests/test_tasks.py::test_ac_012_validation_error_uses_stable_response_shape`; `tests/test_tasks.py::test_malformed_data_file_returns_sanitized_500_and_is_preserved`; `tests/test_tasks.py::test_generated_openapi_documents_success_and_error_schemas` | `ErrorResponse`, `_validation_details`, app exception handlers |
| FR-012 | US-001–US-003 | AC-014 | T017 | `tests/test_tasks.py::test_generated_openapi_documents_success_and_error_schemas`; source-scope inspection for no notifications, multi-user, or cloud-storage features | `create_app`, `routes` |
| NFR-001 | US-003 | AC-011, AC-013 | T004, T012, T017 | `tests/test_storage.py::test_missing_data_file_starts_with_empty_collection`; `tests/test_storage.py::test_tasks_survive_store_recreation`; `tests/test_storage.py::test_malformed_data_is_reported_and_left_unchanged`; `tests/test_storage.py::test_fr_009_directory_at_data_path_is_reported_and_preserved` | `JsonTaskStore` |
| NFR-002 | US-002 | AC-015 | T009, T017 | `tests/test_filters.py::test_1000_task_list_filter_and_sort_latency` | `TaskService.list_tasks`, `TaskService.priority_key` |
| NFR-003 | US-001, US-003 | AC-012–AC-013 | T002, T004–T006, T008, T012 | `tests/test_tasks.py::test_invalid_create_returns_422_without_persisting`; `tests/test_tasks.py::test_invalid_update_is_rejected`; `tests/test_tasks.py::test_ac_012_validation_error_uses_stable_response_shape`; `tests/test_tasks.py::test_malformed_data_file_returns_sanitized_500_and_is_preserved`; `tests/test_storage.py::test_fr_009_directory_at_data_path_is_reported_and_preserved` | request models, `TaskService`, `JsonTaskStore` |
| NFR-004 | US-003 | AC-011 | T004, T008, T012, T016 | `tests/test_storage.py::test_tasks_survive_store_recreation`; `tests/test_tasks.py::test_task_status_and_fields_survive_application_restart` | `JsonTaskStore`, `TaskService.set_status` |
| NFR-005 | US-001–US-003 | AC-018 | T001, T010, T018 | Root CI workflow and runner gates: pytest/coverage, Ruff, Bandit, pip-audit, secret scan | `.github/workflows/ci.yml`, `scripts/run_harness.py` |

## Review Notes

- The test cases were reviewed and approved against the specification before the
  `part-1a-pre-implementation` baseline checkpoint.
- A post-baseline harness repair corrected the secret-scan command invocation; test cases,
  gate definitions, and thresholds were not changed.
- `FR-009` now has a test for a directory at the configured data path; malformed and unreadable
  storage errors must not be silently treated as an empty collection.
- `FR-011` has an explicit stable error-shape test. Existing malformed-file tests verify
  sanitization and preservation.
- All 42 application and harness tests pass with 92.42% line coverage. The final six-gate
  harness report is `evidence/harness-runs/20261121T085120441932Z/results.json`.
- All six gates also pass from a clean clone after installing from `pyproject.toml`.
