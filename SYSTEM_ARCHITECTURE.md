# AI Coding Team - System Architecture & Tools

## Table of Contents
1. [Complete Tools List](#complete-tools-list)
2. [Information Processing Flow](#information-processing-flow)
3. [Orchestrator & Agent Architecture](#orchestrator--agent-architecture)
4. [Model Specifications](#model-specifications)
5. [Component Details](#component-details)

---

## Complete Tools List

**Total Tools: 26 Consolidated Tools** (replaces 97 individual tools)

**Consolidation**: Tools have been consolidated into 26 macro-tools with mode-based design for cleaner agent interfaces and reduced token overhead (~73% reduction).

### A. File, Project & Code Navigation (5 tools)

1. **fs_read** - Read file content or check existence
   - Modes: `read` (default), `exists`
   - Replaces: `read_file`, `file_exists`

2. **fs_write** - Write files or create directories
   - Modes: `write` (default), `save`, `directory`
   - Replaces: `write_file`, `save_file`, `create_directory`

3. **fs_list** - Enumerate directories, search for patterns, list logs
   - Modes: `directory` (default), `files`, `logs`
   - Replaces: `list_directory`, `find_files`, `list_logs`

4. **project_scan** - Detect project structure, configs, test suites, env files
   - Modes: `full` (default), `entrypoints`, `configs`, `tests`, `env`
   - Replaces: `scan_project`, `find_entrypoints`, `list_configs`, `find_tests`, `find_env_files`

5. **code_search** - Search codebase by text, symbols, TODOs, imports
   - Modes: `text` (default), `usages`, `definitions`, `todos`, `imports`
   - Replaces: `search_code`, `find_usages`, `find_definitions`, `find_todos`, `find_imports`

### B. Code Execution, Quality & Tests (5 tools)

6. **code_check** - Validate syntax, types, and static complexity
   - Modes: `syntax` (default), `types`, `complexity`
   - Replaces: `check_syntax`, `check_types`, `analyze_complexity`

7. **code_format** - Run formatters, organize imports, apply quality fixes
   - Modes: `format` (default), `imports`, `quality`
   - Replaces: `format_code`, `organize_imports`, `apply_code_quality`

8. **code_execute** - Run code safely inside a sandbox
   - Replaces: `execute_code`

9. **test_run** - Uniform test execution across languages
   - Framework: `auto` (default), `pytest`, `npm_test`, `vitest`
   - Replaces: `run_tests`, `run_pytest`, `run_npm_test`, `run_vitest`, `get_test_summary`

10. **lint_run** - Lint/format code in any language
    - Modes: `lint` (default), `format`, `fix`
    - Replaces: `run_linter`, `run_formatter`, `fix_code`, `lint_python`, `lint_javascript`, `show_lint_diff`

### C. Git & Version Control (2 tools)

11. **git_inspect** - Read-only Git inspection
    - Modes: `status` (default), `diff`, `log`, `show`, `branch`
    - Replaces: `git_status`, `git_diff`, `git_log`, `git_show`, `git_branch`

12. **git_modify** - Guarded write operations (requires confirmation)
    - Actions: `add`, `commit`
    - Replaces: `git_add`, `git_commit`

### D. DB & API (4 tools)

13. **db_introspect** - Query schema-level database info
    - Modes: `schema` (default), `tables`
    - Replaces: `db_get_schema`, `db_list_tables`

14. **db_query** - Read-only SQL execution with limit guardrails
    - Replaces: `db_query` (renamed wrapper)

15. **api_control** - Control dev APIs locally
    - Actions: `start`, `stop`
    - Replaces: `api_start_server`, `api_stop_server`

16. **api_test** - Test HTTP endpoints, validate responses, inspect docs
    - Modes: `test` (default), `validate`, `auth`, `spec`
    - Replaces: `api_test_endpoint`, `api_validate_response`, `api_test_auth`, `extract_api_spec`

### E. Runtime Infrastructure (4 tools)

17. **task_run** - Unified task runner (npm, make, poetry, alembic)
    - Modes: `run` (default), `list`, `validate`
    - Replaces: `run_task`, `list_tasks`, `validate_task`

18. **docker_inspect** - Inspect local Docker state/services
    - Modes: `ps` (default), `compose`, `status`, `health`
    - Replaces: `docker_ps`, `docker_compose_ps`, `docker_status`, `docker_health`

19. **docker_logs** - Get logs from containers
    - Replaces: `docker_logs` (renamed wrapper)

20. **log_inspect** - Inspect, search, filter log files
    - Modes: `read` (default), `tail`, `search`, `filter`
    - Replaces: `read_log`, `tail_log`, `search_log`, `filter_log`

### F. Docs, Dependencies & Security (3 tools)

21. **docs_generate** - Documentation generation
    - Modes: `readme` (default), `api_docs`, `comments`, `changelog`, `architecture`
    - Replaces: `generate_readme`, `generate_api_docs`, `generate_code_comments`, `update_changelog`, `generate_architecture_doc`

22. **deps_manage** - Manage and audit dependencies
    - Modes: `check` (default), `security`, `update`, `list`, `add`, `remove`, `license`
    - Replaces: `check_dependencies`, `check_security`, `update_dependencies`, `list_dependencies`, `add_dependency`, `remove_dependency`, `check_license`

23. **security_scan** - General and targeted security scanning
    - Modes: `general` (default), `secrets`, `dependencies`, `sql_injection`, `xss`, `audit`
    - Replaces: `scan_security`, `check_secrets`, `analyze_dependencies`, `check_sql_injection`, `check_xss`, `security_audit`

### G. Web Research (2 tools)

24. **web_get** - Fetch web content or assets
    - Modes: `read` (default), `documentation`, `assets`
    - Replaces: `read_web_page`, `read_documentation`, `download_assets`

25. **web_analyze** - Analyze web pages for info or design patterns
    - Modes: `extract` (default), `summary`, `scrape`, `design_elements`, `structure`, `design`
    - Replaces: `extract_information`, `get_web_summary`, `scrape_website`, `extract_design_elements`, `extract_structure`, `analyze_design`

### H. Model Escalation (1 tool)

26. **model_escalate** - Delegate hard subtasks to Claude / DeepSeek / GPT-4
    - Modes: `consult` (default), `check_complexity`, `help`, `refine`
    - Replaces: `check_complexity`, `escalate_to_flagship`, `get_flagship_help`, `refine_with_flagship`

---

**Migration Layer**: All 95 old tool names are automatically migrated to new consolidated tools during execution. See `tools/consolidated/migration.py` for details.
- `docker_compose_ps` - List docker-compose services
- `docker_logs` - Get Docker logs
- `docker_health` - Check container health
- `docker_status` - Get container status

### 13. Log Reader Tools (5 tools)
- `read_log` - Read log file
- `tail_log` - Tail log file
- `search_log` - Search log file
- `filter_log` - Filter log by criteria
- `list_logs` - List log files

### 14. Documentation Tools (6 tools)
- `generate_readme` - Generate README.md
- `generate_api_docs` - Generate API documentation
- `generate_code_comments` - Generate code comments
- `extract_api_spec` - Extract API specification
- `update_changelog` - Update CHANGELOG.md
- `generate_architecture_doc` - Generate architecture documentation

### 15. Package Manager Tools (7 tools)
- `check_dependencies` - Check dependency status
- `check_security` - Check security vulnerabilities
- `update_dependencies` - Update dependencies
- `list_dependencies` - List all dependencies
- `add_dependency` - Add dependency
- `remove_dependency` - Remove dependency
- `check_license` - Check package licenses

### 16. Security Scanning Tools (6 tools)
- `scan_security` - General security scan
- `check_secrets` - Check for exposed secrets
- `analyze_dependencies` - Analyze dependency security
- `check_sql_injection` - Check for SQL injection vulnerabilities
- `check_xss` - Check for XSS vulnerabilities
- `security_audit` - Comprehensive security audit

### 17. Web Research Tools (5 tools)
- `read_web_page` - Read web page content
- `read_documentation` - Read documentation pages
- `extract_information` - Extract specific information
- `get_web_summary` - Get web page summary
- `search_web` - Search the web (DuckDuckGo)

### 18. Model Escalation Tools (4 tools)
- `escalate_to_flagship` - Escalate to flagship model (DeepSeek, GPT-4, Claude)
- `check_complexity` - Check task complexity
- `get_flagship_help` - Get help from flagship model
- `refine_with_flagship` - Refine solution using flagship model

---

## Information Processing Flow

### High-Level Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INPUT                               │
│                    (Task Description)                            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATOR                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  1. Project Structure Detection                           │  │
│  │     - Detect if new project needed                        │  │
│  │     - Create project structure if needed                  │  │
│  └───────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  2. Complexity Prediction                                 │  │
│  │     - Analyze task complexity (1-10 scale)                │  │
│  │     - Uses: keywords, codebase size, novelty              │  │
│  │     - Threshold: >= 8 → Claude, < 8 → Local              │  │
│  └───────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  3. Task Type Detection                                   │  │
│  │     - Detect: crud, api, database, algorithm, test, etc.  │  │
│  │     - Used for: context building, token limits            │  │
│  └───────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  4. Context Building (ContextManager)                     │  │
│  │     - Build optimized context based on task type          │  │
│  │     - Include: project info, architecture, dependencies   │  │
│  └───────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
              ┌──────────────┴──────────────┐
              │                             │
              ▼                             ▼
     ┌────────────────┐          ┌──────────────────┐
     │  LOCAL ROUTE   │          │  CLAUDE ROUTE    │
     │  (< 8)         │          │  (>= 8)          │
     └────────┬───────┘          └────────┬─────────┘
              │                           │
              ▼                           ▼
     ┌─────────────────────────────────────────────┐
     │     IMPLEMENTATION AGENT                     │
     │  ┌───────────────────────────────────────┐  │
     │  │  Model: qwen2.5-coder:7b              │  │
     │  │  Dynamic Token Limits:                │  │
     │  │    - API: 7500 tokens (2.5x)          │  │
     │  │    - Database: 7500 tokens (2.5x)     │  │
     │  │    - CRUD: 6000 tokens (2.0x)         │  │
     │  │    - Algorithm: 3600 tokens (1.2x)    │  │
     │  │    - General: 3000 tokens (base)      │  │
     │  └───────────────────────────────────────┘  │
     │  ┌───────────────────────────────────────┐  │
     │  │  Prompt Building (PromptBuilder)      │  │
     │  │  - Task-specific prompts              │  │
     │  │  - Few-shot examples                  │  │
     │  │  - Quality checklists                 │  │
     │  └───────────────────────────────────────┘  │
     │  ┌───────────────────────────────────────┐  │
     │  │  Skill Selection (SkillManager)       │  │
     │  │  - Dynamic skill loading              │  │
     │  │  - Token-budgeted selection           │  │
     │  │  - Framework/library detection        │  │
     │  └───────────────────────────────────────┘  │
     │  ┌───────────────────────────────────────┐  │
     │  │  Tool Execution                       │  │
     │  │  - 26 consolidated tools available   │  │
     │  │  - Parse tool calls from output       │  │
     │  │  - Execute tools, add results         │  │
     │  └───────────────────────────────────────┘  │
     └────────────────────────┬────────────────────┘
                              │
                              ▼
                  ┌───────────────────────┐
                  │  CODE GENERATION      │
                  │  (Streaming Response) │
                  └───────────┬───────────┘
                              │
                              ▼
                  ┌───────────────────────┐
                  │  CODE QUALITY         │
                  │  - Format code        │
                  │  - Organize imports   │
                  │  - Type checking      │
                  └───────────┬───────────┘
                              │
                              ▼
                  ┌───────────────────────┐
                  │  VALIDATION AGENT     │
                  │  ┌─────────────────┐  │
                  │  │ Syntax Check    │  │
                  │  │ Execution Check │  │
                  │  │ Test Execution  │  │
                  │  └─────────────────┘  │
                  └───────────┬───────────┘
                              │
                              ▼
                  ┌───────────────────────┐
                  │  ERROR ANALYZER       │
                  │  (If validation fails)│
                  │  - Parse errors       │
                  │  - Suggest fixes      │
                  │  - Generate fix task  │
                  └───────────┬───────────┘
                              │
                              ▼
                  ┌───────────────────────┐
                  │  ITERATIVE REFINEMENT │
                  │  (Max 3 iterations)   │
                  │  - Retry with fixes   │
                  │  - Escalate if needed │
                  └───────────┬───────────┘
                              │
                              ▼
                  ┌───────────────────────┐
                  │  EVALUATION           │
                  │  - Success score      │
                  │  - Quality metrics    │
                  └───────────┬───────────┘
                              │
                              ▼
                  ┌───────────────────────┐
                  │  LOGGING              │
                  │  - Log interaction    │
                  │  - Store for learning │
                  └───────────┬───────────┘
                              │
                              ▼
                  ┌───────────────────────┐
                  │     FINAL RESULT      │
                  │  - Generated code     │
                  │  - Validation results │
                  │  - Evaluation score   │
                  └───────────────────────┘
```

### Detailed Flow Steps

#### Step 1: Project Structure Detection
- **Component**: `ProjectStructureHelper`
- **Purpose**: Detect if task requires new project creation
- **Actions**:
  - Detect project type (Flask, FastAPI, Django, React, etc.)
  - Extract project name
  - Create project structure (directories, config files)
  - Update context with project info

#### Step 2: Complexity Prediction
- **Component**: `ComplexityPredictor`
- **Algorithm**:
  - **Lexical Analysis**: Keywords (architecture, distributed, optimize, etc.)
  - **Codebase Size**: Files involved (thresholds: 5, 10)
  - **Pattern Familiarity**: Has similar examples? (-2 complexity)
  - **Novelty**: Pattern familiarity < 0.3? (+2 complexity)
  - **Task Length**: > 30 words? (+1 complexity)
- **Output**: Complexity score 1-10
- **Routing Decision**:
  - `complexity >= 8` → Claude route
  - `complexity < 8` → Local route

#### Step 3: Task Type Detection
- **Component**: `ContextManager.detect_task_type()`
- **Supported Types**:
  - `api` - API endpoints, routes
  - `database` - Database models, queries
  - `crud` - CRUD operations
  - `algorithm` - Algorithms, data structures
  - `test` - Test generation
  - `frontend` - Frontend code
  - `devops` - DevOps configs
  - `etl` - ETL pipelines
  - `data_analysis` - Data analysis
  - `general` - General tasks
- **Detection Method**: Pattern matching on task keywords
- **Usage**: Context building, token limits, skill selection

#### Step 4: Context Building
- **Component**: `ContextManager`
- **Process**:
  1. Detect task type
  2. Create `ContextConfig` based on task type
  3. Build context with relevant sections:
     - Project info (for CRUD, API, database tasks)
     - Architecture (for complex tasks)
     - Dependencies (for integration tasks)
     - Relevant code (for test tasks)
     - Current file (for modification tasks)
  4. Token-aware context building (budget management)

#### Step 5: Code Generation
- **Agent**: `ImplementationAgent` (local) or Claude (remote)
- **Process**:
  1. **Prompt Building** (`PromptBuilder`):
     - Role & mission
     - Context (from ContextManager)
     - Skills (from SkillManager)
     - Few-shot examples
     - Quality checklist
     - Tools list
  2. **Skill Selection** (`SkillManager`):
     - Detect frameworks/libraries mentioned
     - Select relevant skills within token budget
     - Prioritize: primary skills > keyword matches > task type matches
  3. **Model Call**:
     - Streaming response
     - Dynamic token limits based on task type
     - Tool call parsing
  4. **Tool Execution**:
     - Parse tool calls from output
     - Execute tools (97 available)
     - Add tool results to output

#### Step 6: Code Quality
- **Tools Used**:
  - `format_code` - Format code
  - `organize_imports` - Organize imports
  - `check_types` - Type checking
  - `apply_code_quality` - Apply quality improvements

#### Step 7: Validation
- **Agent**: `ValidationAgent`
- **Steps**:
  1. **Syntax Check** - Validate Python/JS syntax
  2. **Execution Check** - Try to execute code safely
  3. **Test Execution** (`TestGeneratorAgent`):
     - Generate tests if needed
     - Run tests (pytest, npm test, vitest)
     - Collect results

#### Step 8: Error Analysis (if validation fails)
- **Component**: `ErrorAnalyzer`
- **Process**:
  1. Parse errors (syntax, runtime, test failures)
  2. Extract specific errors with locations
  3. Generate fix suggestions with code examples
  4. Create enhanced task prompt with error context

#### Step 9: Iterative Refinement
- **Max Iterations**: 3
- **Process**:
  1. If validation fails → Analyze errors
  2. Generate fix task with error context
  3. Retry code generation with fix task
  4. Re-validate
  5. Repeat until success or max iterations

#### Step 10: Evaluation & Logging
- **Evaluation**: `SuccessEvaluator`
  - Score: 0-100
  - Factors: syntax, execution, tests passed
- **Logging**: `InteractionLogger`
  - Store interaction data
  - Track metrics (complexity, route, success)

---

## Orchestrator & Agent Architecture

### Orchestrator (`agents/orchestrator.py`)

**Role**: Main coordinator that routes tasks and manages the entire pipeline

**Model**:
- **Name**: `qwen2.5-coder:14b`
- **Temperature**: 0.3
- **Max Tokens**: 4000
- **Context Window**: ~32K tokens (Qwen2.5 14B)

**Responsibilities**:
1. Receive user task
2. Predict complexity
3. Route to local or Claude
4. Build context
5. Coordinate agents
6. Handle retries and fallbacks
7. Validate results
8. Log interactions

**Key Methods**:
- `build_with_validation()` - Main entry point
- `build_with_validation_iterative()` - With iterative refinement
- `_execute_claude()` - Execute Claude route
- `check_health()` - Health check

### Implementation Agent (`agents/specialized_agent.py`)

**Role**: Generates production-ready code

**Model**:
- **Name**: `qwen2.5-coder:7b`
- **Temperature**: 0.2 (focused, deterministic)
- **Base Max Tokens**: 3000
- **Dynamic Token Limits**:
  - API: 7500 tokens (2.5x multiplier)
  - Database: 7500 tokens (2.5x multiplier)
  - ETL: 7500 tokens (2.5x multiplier)
  - CRUD: 6000 tokens (2.0x multiplier)
  - Frontend: 6000 tokens (2.0x multiplier)
  - DevOps: 6000 tokens (2.0x multiplier)
  - Data Analysis: 6000 tokens (2.0x multiplier)
  - Test: 4500 tokens (1.5x multiplier)
  - Algorithm: 3600 tokens (1.2x multiplier)
  - General: 3000 tokens (1.0x multiplier)
- **Max Cap**: 12,000 tokens (hard limit)
- **Context Window**: ~32K tokens (Qwen2.5 7B)

**Capabilities**:
- Dynamic skill loading based on task
- Task-specific prompt building
- Tool execution (26 consolidated tools with automatic migration from 95 old tools)
- Streaming response collection
- Few-shot learning

**Skills**:
- Primary skill file: `implementation.md`
- Additional skills: Loaded dynamically by `SkillManager`
- Framework skills: Flask, FastAPI, Django, SQLAlchemy, Pandas, NumPy
- Task-type skills: ETL patterns, data analysis patterns

### Validation Agent (`agents/specialized_agent.py`)

**Role**: Validates generated code

**Model**:
- **Name**: `qwen2.5-coder:7b`
- **Temperature**: 0.1 (very deterministic)
- **Max Tokens**: 3000
- **Context Window**: ~32K tokens

**Responsibilities**:
1. Syntax validation
2. Code execution testing
3. Test generation and execution

### Test Generator Agent (`agents/specialized_agent.py`)

**Role**: Generates tests for code

**Model**:
- **Name**: `qwen2.5-coder:14b` (uses orchestrator model)
- **Temperature**: 0.2
- **Max Tokens**: 8000 (increased for complete test generation)
- **Context Window**: ~32K tokens

**Capabilities**:
- Generate unit tests
- Generate integration tests
- Run tests (pytest, npm test, vitest)
- Analyze test results
- Validate test completeness

### Error Analyzer (`agents/error_analyzer.py`)

**Role**: Analyzes errors and generates fix suggestions

**Process**:
1. Parse validation results
2. Extract error types (syntax, runtime, test failure)
3. Extract specific errors with locations
4. Generate fix suggestions with code examples
5. Create enhanced task prompt

**Error Types Detected**:
- Syntax errors
- Runtime errors (TypeError, NameError, AttributeError, etc.)
- Test failures (AssertionError, collection errors)
- Import errors

### Complexity Predictor (`agents/complexity_predictor.py`)

**Role**: Predicts task complexity for routing

**Algorithm**:
- **Base**: 5 (neutral)
- **Complex Keywords**: +3 (architecture, distributed, optimize, etc.)
- **Medium Keywords**: +1 (implement, create, add feature)
- **Simple Keywords**: -1 (fix bug, add test, update style)
- **Files Involved**:
  - > 10 files: +2
  - > 5 files: +1
- **Pattern Familiarity**:
  - Has similar example: -2
- **Novelty**:
  - Pattern familiarity < 0.3: +2
- **Task Length**:
  - > 30 words: +1

**Output**: Score 1-10
**Threshold**: >= 8 routes to Claude

### Context Manager (`agents/context_manager.py`)

**Role**: Builds optimized context for agents

**Task Type Detection**:
- Pattern matching on keywords
- Priority order: api, database, etl, data_analysis, frontend, devops → crud → algorithm → test → general

**Context Building**:
- Task-type-specific context config
- Token-aware building
- Include sections: project_info, architecture, dependencies, relevant_code, current_file

### Prompt Builder (`agents/prompt_builder.py`)

**Role**: Builds optimized prompts for agents

**Components**:
1. Role & mission
2. Context (from ContextManager)
3. Skills (from SkillManager)
4. Few-shot examples
5. Quality checklist
6. Tools list (if enabled)

**Examples**: Loaded from `.aiconfig/examples/`

### Skill Manager (`agents/skill_manager.py`)

**Role**: Dynamically selects relevant skills

**Process**:
1. Detect frameworks/libraries in task
2. Match skills by keywords
3. Filter by task type relevance
4. Select within token budget
5. Prioritize: primary skills > keyword matches > task type matches

**Skills Location**: `.aiconfig/skills/`

---

## Model Specifications

### Local Models (Ollama)

#### Orchestrator Model
- **Name**: `qwen2.5-coder:14b`
- **Type**: Qwen2.5 Coder 14B
- **Context Window**: ~32K tokens
- **Temperature**: 0.3
- **Max Tokens**: 4000
- **Use Case**: Complexity prediction, routing

#### Implementation/Validation Models
- **Name**: `qwen2.5-coder:7b`
- **Type**: Qwen2.5 Coder 7B
- **Context Window**: ~32K tokens
- **Temperature**: 
  - Implementation: 0.2
  - Validation: 0.1
- **Max Tokens**: 
  - Base: 3000
  - Dynamic (Implementation): 3000-12,000 (task-dependent)
  - Validation: 3000

#### Test Generator Model
- **Name**: `qwen2.5-coder:14b` (uses orchestrator model)
- **Type**: Qwen2.5 Coder 14B
- **Context Window**: ~32K tokens
- **Temperature**: 0.2
- **Max Tokens**: 8000 (increased for complete test generation)

### Remote Model (Claude)

#### Claude Route
- **Name**: `claude-sonnet-4-20250514`
- **Type**: Anthropic Claude Sonnet 4
- **Context Window**: 200K tokens
- **Max Tokens**: 4000
- **Use Case**: Complex tasks (complexity >= 8)
- **API**: Anthropic API

### Flagship Models (Model Escalation)

#### DeepSeek (Recommended)
- **Name**: `deepseek-chat`
- **API Base**: `https://api.deepseek.com/v1`
- **Max Tokens**: 4000 (configurable)
- **Use Case**: Escalation for complex problems
- **Cost**: Low (cost-effective)

#### OpenAI GPT-4
- **Name**: `gpt-4-turbo-preview`
- **API Base**: `https://api.openai.com/v1`
- **Max Tokens**: 4000 (configurable)
- **Use Case**: Escalation for complex problems
- **Cost**: Medium-High

#### Anthropic Claude
- **Name**: `claude-3-5-sonnet-20241022`
- **API Base**: `https://api.anthropic.com/v1`
- **Max Tokens**: 4000 (configurable)
- **Use Case**: Escalation for complex problems
- **Cost**: Medium

**Escalation Triggers**:
- Task too complex for base model
- Multiple failed attempts
- Explicit user request
- Error analysis suggests complexity issue

---

## Component Details

### Configuration (`config/models.yaml`)

```yaml
models:
  orchestrator:
    name: "qwen2.5-coder:14b"
    temperature: 0.3
    max_tokens: 4000
    
  implementation:
    name: "qwen2.5-coder:7b"
    temperature: 0.2
    max_tokens: 3000  # Base, dynamically adjusted
    
  validation:
    name: "qwen2.5-coder:7b"
    temperature: 0.1
    max_tokens: 3000

routing:
  complexity_threshold: 8  # >= 8 routes to Claude
  
  weights:
    lexical: 3
    codebase_size: 2
    novelty: 2
    historical: -1

claude:
  model: "claude-sonnet-4-20250514"
  max_tokens: 4000

timeouts:
  model_request: 180      # Model API requests
  model_streaming: 300    # Streaming collection
  tool_execution: 30      # Tool execution
  code_execution: 10      # Code execution
  test_execution: 60      # Test execution
  health_check: 5         # Health checks
  file_operations: 10     # File operations
```

### Retry & Error Handling

**Retry Handler** (`agents/retry_handler.py`):
- Exponential backoff
- Max attempts: 3 (local), 2 (Claude)
- Retries on: `RetryableError`, `ModelConnectionError`, `ModelTimeoutError`
- Fallback: Claude → Local, Local → (fail)

**Error Types**:
- `ModelConnectionError` - Connection issues (retryable)
- `ModelTimeoutError` - Timeout (retryable)
- `AgentError` - Agent execution error (may be retryable)
- `ValidationError` - Validation failure (not retryable, but can iterate)
- `ConfigurationError` - Config error (not retryable)

### Health Checking

**Health Checker** (`agents/health_check.py`):
- Checks: Ollama connection, Claude API, file system, models available
- Status: healthy, degraded, unhealthy
- Response time tracking

### Logging

**Structured Logger** (`agents/structured_logger.py`):
- JSON format logs
- Levels: DEBUG, INFO, WARNING, ERROR
- Console + file output

**Interaction Logger** (`learning/logger.py`):
- Stores interaction data (TOON format)
- Tracks: task, context, output, complexity, route, success score
- Location: `data/interactions/*.toon`

### Learning & Evaluation

**Success Evaluator** (`learning/evaluator.py`):
- Score: 0-100
- Factors: syntax (40%), execution (30%), tests (30%)
- Feedback: Detailed feedback for improvement

---

## Summary

**Total Tools**: 26 consolidated tools (replaces 97 individual tools)

**Models**:
- Orchestrator: qwen2.5-coder:14b (Ollama)
- Implementation: qwen2.5-coder:7b (Ollama) - Dynamic tokens
- Validation: qwen2.5-coder:7b (Ollama)
- Test Generator: qwen2.5-coder:7b (Ollama)
- Complex Tasks: claude-sonnet-4-20250514 (Anthropic)
- Escalation: DeepSeek, GPT-4, Claude (configurable)

**Flow**: User → Orchestrator → Complexity → Routing → Context → Agent → Code → Quality → Validation → Error Analysis → Iteration → Evaluation → Logging

**Key Features**:
- Dynamic token limits based on task type
- Automatic skill selection
- Task-specific context building
- 26 consolidated tools for real-world interaction (replaces 97 individual tools)
- Model escalation for complex tasks
- Iterative refinement with error analysis

