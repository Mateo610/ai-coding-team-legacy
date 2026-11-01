final consolidated tool list used by the orchestrator and implementation agent.
Each macro-tool includes the older tools it replaces.

⸻

A. File, Project & Code Navigation

1. fs_read

Replaces:
	•	read_file
	•	file_exists

Purpose: Read file content or check existence.

2. fs_write

Replaces:
	•	write_file
	•	save_file
	•	create_directory

Purpose: Write files or create directories safely.

3. fs_list

Replaces:
	•	list_directory
	•	find_files
	•	list_logs

Purpose: Enumerate directories, search for patterns, list logs.

4. project_scan

Replaces:
	•	scan_project
	•	find_entrypoints
	•	list_configs
	•	find_tests
	•	find_env_files

Purpose: Detect project structure, configs, test suites, env files.

5. code_search

Replaces:
	•	search_code
	•	find_usages
	•	find_definitions
	•	find_todos
	•	find_imports

Purpose: Search codebase by text, symbols, TODOs, imports.

⸻

B. Code Execution, Quality & Tests

6. code_check

Replaces:
	•	check_syntax
	•	check_types
	•	analyze_complexity

Purpose: Validate syntax, types, and static complexity.

7. code_format

Replaces:
	•	format_code
	•	organize_imports
	•	apply_code_quality

Purpose: Run formatters, organize imports, apply quality fixes.

8. code_execute

Replaces:
	•	execute_code

Purpose: Run code safely inside a sandbox.

9. test_run

Replaces:
	•	run_tests
	•	run_pytest
	•	run_npm_test
	•	run_vitest
	•	get_test_summary

Purpose: Uniform test execution across languages.

10. lint_run

Replaces:
	•	run_linter
	•	run_formatter
	•	fix_code
	•	lint_python
	•	lint_javascript
	•	show_lint_diff

Purpose: Lint/format code in any language.

⸻

C. Git & Version Control

11. git_inspect

Replaces:
	•	git_status
	•	git_diff
	•	git_log
	•	git_show
	•	git_branch

Purpose: Read-only Git inspection.

12. git_modify

Replaces:
	•	git_add
	•	git_commit

Purpose: Guarded write operations (requires confirmation).

⸻

D. DB & API

13. db_introspect

Replaces:
	•	db_get_schema
	•	db_list_tables

Purpose: Query schema-level database info.

14. db_query

Replaces:
	•	db_query (read-only)

Purpose: Read-only SQL execution with limit guardrails.

15. api_control

Replaces:
	•	api_start_server
	•	api_stop_server

Purpose: Control dev APIs locally.

16. api_test

Replaces:
	•	api_test_endpoint
	•	api_validate_response
	•	api_test_auth
	•	extract_api_spec

Purpose: Test HTTP endpoints, validate responses, inspect docs.

⸻

E. Runtime Infra: Tasks, Containers, Logs

17. task_run

Replaces:
	•	run_task
	•	list_tasks
	•	validate_task

Purpose: Unified task runner (npm, make, poetry, alembic).

18. docker_inspect

Replaces:
	•	docker_ps
	•	docker_compose_ps
	•	docker_status
	•	docker_health

Purpose: Inspect local Docker state/services.

19. docker_logs

Replaces:
	•	docker_logs

Purpose: Get logs from containers.

20. log_inspect

Replaces:
	•	read_log
	•	tail_log
	•	search_log
	•	filter_log

Purpose: Inspect, search, filter log files.

⸻

F. Docs, Dependencies & Security

21. docs_generate

Replaces:
	•	generate_readme
	•	generate_api_docs
	•	generate_code_comments
	•	update_changelog
	•	generate_architecture_doc

Purpose: Documentation generation.

22. deps_manage

Replaces:
	•	check_dependencies
	•	check_security
	•	update_dependencies
	•	list_dependencies
	•	add_dependency
	•	remove_dependency
	•	check_license

Purpose: Manage and audit dependencies.

23. security_scan

Replaces:
	•	scan_security
	•	check_secrets
	•	analyze_dependencies
	•	check_sql_injection
	•	check_xss
	•	security_audit

Purpose: General and targeted security scanning.

⸻

G. Web Research

24. web_get

Replaces:
	•	read_web_page
	•	read_documentation
	•	download_assets

Purpose: Fetch web content or assets.

25. web_analyze

Replaces:
	•	extract_information
	•	get_web_summary
	•	scrape_website
	•	extract_design_elements
	•	extract_structure
	•	analyze_design

Purpose: Analyze web pages for info or design patterns.

⸻

H. Model Escalation (Remote Models)

26. model_escalate

Replaces:
	•	check_complexity
	•	escalate_to_flagship
	•	get_flagship_help
	•	refine_with_flagship

Purpose: Delegate hard subtasks to Claude / DeepSeek / GPT-4.

⸻

4. How the Orchestrator Uses These Tools

Step 1 — Complexity Prediction
	•	If complexity < threshold → local model
	•	If >= threshold → call model_escalate(mode="consult")

Step 2 — Context Building

Tools used:
	•	project_scan
	•	fs_list
	•	code_search
	•	git_inspect
	•	db_introspect
	•	api_test (for API tasks)

Step 3 — Code Generation Using Tools

Implementation agent can now reliably pick from only 26 tools.
Typical flow:
	1.	Search for related code → code_search
	2.	Read or write files → fs_read / fs_write
	3.	Check syntax/types → code_check
	4.	Format code → code_format
	5.	Run tests → test_run
	6.	Inspect logs → log_inspect
	7.	Validate DB/API → db_query, api_test
	8.	Commit changes → git_modify

Step 4 — Validation
	•	code_check
	•	code_execute
	•	test_run

Step 5 — Error Analysis & Fix Loop

When validation fails:
	1.	Read error logs
	2.	Use code_search + fs_read to localize the issue
	3.	Fix code
	4.	Re-validate
	5.	If stuck → escalate: model_escalate(mode="refine")

⸻

5. Migration Plan (Cursor Helper)

You should follow this sequence inside Cursor:

Phase 1 — Create New Tool Definitions
	•	Define the new tool schemas (fs_read, fs_write, etc.)
	•	Place them in a new directory: tools_consolidated/

Phase 2 — Redirect Old Tools

For each old tool:
	•	Keep backend functions in tools/legacy/
	•	Update new macro-tools to call these internally

Phase 3 — Remove Old Tool References from Agents
	•	Update the orchestrator’s tool manifest to only include the 26 macro-tools
	•	Validation, TestGenerator, ErrorAnalyzer must be updated to use new tool names

Phase 4 — Update Test Suite
	•	Add tests for each macro-tool’s modes/actions

Phase 5 — Remove Dead Code Later

Once stabilized, remove unused micro-tool wrappers.

⸻

6. Final Notes

This setup provides:
	•	Clean surface area for the LLM (~26 tools)
	•	Retention of all functionality internally
	•	Future-proof structure
	•	Easier debugging
	•	Less token overhead
	•	More predictable behavior
	•	Higher success rate for tool calls
	•	Flexibility to extend later

This document should remain the source of truth
for tool refactoring and consolidation