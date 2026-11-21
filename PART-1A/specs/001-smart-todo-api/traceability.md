# Requirement Traceability: Smart Todo API

This table connects the approved `US-*`, `FR-*`, `NFR-*`, and `AC-*` IDs to the task plan,
current pytest node IDs, and planned implementation areas. Source symbols will be confirmed
against the completed implementation before acceptance; planned areas are not evidence of
implementation.

| Requirement | Story | Acceptance criteria | Tasks | Verification IDs | Planned implementation area |
|---|---|---|---|---|---|
| FR-001 | US-001 | AC-001–AC-004 | T003, T006, T011, T014 | `test_create_task_returns_defaults_and_utc_timestamp`; `test_create_task_accepts_documented_field_boundaries`; `test_description_is_trimmed`; `test_invalid_create_returns_422_without_persisting`; `test_duplicate_tags_are_stored_once_case_insensitively` | `src/models.py`, `src/routes.py` |
| FR-002 | US-001 | AC-002 | T003–T004, T006, T011, T014 | `test_create_task_returns_defaults_and_utc_timestamp`; `test_task_crud_and_partial_update` | `src/models.py`, `src/services.py` |
| FR-003 | US-001, US-002 | AC-006, AC-009 | T006–T007, T014–T015 | `test_task_crud_and_partial_update`; `test_unknown_task_operations_use_not_found`; `test_tag_filter_is_case_insensitive_exact_and_match_any` | `src/routes.py`, `src/services.py` |
| FR-004 | US-001 | AC-005, AC-017 | T003–T004, T006, T011–T012, T014 | `test_task_crud_and_partial_update`; `test_invalid_update_is_rejected`; `test_later_sequential_update_wins_for_same_field`; `test_concurrent_updates_preserve_different_fields`; `test_concurrent_different_field_updates_are_serialized` | `src/services.py`, `src/storage.py` |
| FR-005 | US-001 | AC-006–AC-007 | T006, T014 | `test_task_crud_and_partial_update`; `test_unknown_task_operations_use_not_found` | `src/services.py`, `src/routes.py` |
| FR-006 | US-003 | AC-006, AC-008, AC-016 | T008, T016 | `test_complete_and_reopen_are_idempotent`; `test_unknown_task_operations_use_not_found` | `src/services.py`, `src/routes.py` |
| FR-007 | US-002 | AC-009 | T007, T015 | `test_tag_filter_is_case_insensitive_exact_and_match_any`; `test_repeated_tag_query_parameters_are_supported`; `test_filter_without_matches_returns_empty_list` | `src/services.py`, `src/routes.py` |
| FR-008 | US-002 | AC-010, AC-015 | T007, T009, T015 | `test_priority_sort_orders_high_medium_low`; `test_priority_ties_use_created_at_then_id`; `test_filter_and_sort_can_be_combined`; `test_1000_task_list_filter_and_sort_latency` | `src/services.py` |
| FR-009 | US-003 | AC-011, AC-013 | T002, T004, T008, T012, T016 | `test_missing_data_file_starts_with_empty_collection`; `test_tasks_survive_store_recreation`; `test_malformed_data_is_reported_and_left_unchanged`; `test_fr_009_directory_at_data_path_is_reported_and_preserved`; `test_failed_atomic_write_preserves_previous_data`; `test_task_status_and_fields_survive_application_restart` | `src/storage.py`, `src/main.py` |
| FR-010 | US-001–US-003 | AC-001–AC-018 | T003, T005–T008, T011, T013–T018 | HTTP contract tests in `tests/test_tasks.py` and `tests/test_filters.py`; harness exit-status tests in `tests/test_harness_runner.py` | `src/routes.py`, `src/main.py`, `.github/workflows/ci.yml` |
| FR-011 | US-001, US-003 | AC-006, AC-012–AC-013 | T005, T011–T014, T016 | `test_ac_012_validation_error_uses_stable_response_shape`; `test_malformed_data_file_returns_sanitized_500_and_is_preserved`; `test_generated_openapi_documents_success_and_error_schemas` | `src/models.py`, `src/main.py` |
| FR-012 | US-001–US-003 | AC-014 | T017 | `test_generated_openapi_documents_success_and_error_schemas`; scope inspection for no notifications, multi-user, or cloud-storage features | `src/main.py`, `src/routes.py` |
| NFR-001 | US-003 | AC-011, AC-013 | T004, T012, T017 | `test_missing_data_file_starts_with_empty_collection`; `test_tasks_survive_store_recreation`; `test_malformed_data_is_reported_and_left_unchanged`; `test_fr_009_directory_at_data_path_is_reported_and_preserved` | `src/storage.py` |
| NFR-002 | US-002 | AC-015 | T009, T017 | `test_1000_task_list_filter_and_sort_latency` | `src/services.py` |
| NFR-003 | US-001, US-003 | AC-012–AC-013 | T002, T004–T006, T008, T012 | `test_invalid_create_returns_422_without_persisting`; `test_invalid_update_is_rejected`; `test_ac_012_validation_error_uses_stable_response_shape`; `test_malformed_data_file_returns_sanitized_500_and_is_preserved`; `test_fr_009_directory_at_data_path_is_reported_and_preserved` | `src/models.py`, `src/services.py`, `src/storage.py` |
| NFR-004 | US-003 | AC-011 | T004, T008, T012, T016 | `test_tasks_survive_store_recreation`; `test_task_status_and_fields_survive_application_restart` | `src/storage.py` |
| NFR-005 | US-001–US-003 | AC-018 | T001, T010, T018 | Root CI workflow and runner gates: pytest/coverage, Ruff, Bandit, pip-audit, secret scan | `.github/workflows/ci.yml`, `scripts/run_harness.py` |

## Review Notes

- The test cases were reviewed and approved against the specification before the
  `part-1a-pre-implementation` baseline checkpoint.
- `FR-009` now has a test for a directory at the configured data path; malformed and unreadable
  storage errors must not be silently treated as an empty collection.
- `FR-011` has an explicit stable error-shape test. Existing malformed-file tests verify
  sanitization and preservation.
- Tests that require application modules are expected to fail collection until the implementation
  tasks are complete. No application harness run has been recorded yet.
