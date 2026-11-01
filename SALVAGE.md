# What to salvage from ai-coding-team

Notes for a later pass with Claude. Written 2026-11-01 after reading this
tree against the pablo-harness plan (M0 done, M1 in progress). This folder is
the archive. Do not treat the architecture proposals as the system that ran.

## What actually ran

A single pipeline:

1. Keyword complexity score, 1–10.
2. Route local or Claude.
3. Build context without a model.
4. One coder (about 7B).
5. Tools, then tests, then a 0–100 score.

`ARCHITECTURE_PROPOSAL.md` and `CONTEXT_TEAM_ARCHITECTURE.md` describe a
manager, a parallel context team, and sequential frontend / backend / API /
database agents. That team was not implemented. It also does not fit one
RTX 3090 24 GB. Pablo already swaps one lane at a time (M4) instead of
keeping a team resident.

Pablo's coder returns a diff. Checks run outside the model. The human is the
merge. The router must not choose the Claude lane. Those rules stay.

## Already planned in pablo-harness M2

Take these if a comparison test says they are better. Leave the old
orchestrator and `main.py`.

| Piece | Where | Use |
|---|---|---|
| Complexity predictor | `agents/complexity_predictor.py` | Richer than Pablo's word-count `estimate_complexity`. Label 30 tasks and keep the winner. |
| TOON daily log | `learning/logger.py` | Export format for approved trainable rows. JSONL stays the source of truth. |
| Evaluator | `learning/evaluator.py` | Only if the scoring is reusable for M7. Do not use the blended 0–100 as the merge gate. |
| Prompts | `agents/specialized_agent.py`, `agents/prompt_builder.py` | Useful phrasing, not the agent class. |
| Tool result shape | `tools/code_tools.py` | Only if a later lane calls tools. Pablo's coder should keep emitting a diff. |

Do not port the old test generator. It truncated output and reported 0/0 tests.
Pablo's verifier should treat pytest exit code 5 (no tests collected) as a failure.

## Approaches worth using

These are not a port of the classes. They are shapes Pablo does not have yet.

### 1. Let the route learn from outcomes

`agents/routing_optimizer.py` records, per task type, which route succeeded
and how long it took, then biases the next choice.

Pablo's router is keywords plus an optional small model. After M1 has real
traces, the same table can bias **coder versus deep**. It must not start
choosing Claude. A longer keyword list is a weaker version of this.

### 2. Remember recurring failures

`learning/error_patterns.py` clusters check failures and can put the known
fix into the next similar prompt.

M1 only sends the apply error back once, on the same run. A small failure
memory is a learning loop you can have before the M8 LoRA. Keep it separate
from training data: a rejected or failed run is a prompt hint, not a training
row.

### 3. Budget the context

`agents/context_manager.py` splits the prompt into sections (rules, relevant
code, examples, the last error) and gives each a token cap.

M6's repo map and symbol lookup should still be how code is found. The budget
is how that result stays inside a 16k window. Do not hire a model to list a
directory or read `pyproject.toml`.

### 4. Load one skill card when the task matches

`agents/skill_manager.py` and `.aiconfig/skills/` load a short playbook
(FastAPI, testing, error handling) only when the task matches.
`agents/prompt_builder.py` also picks few-shot examples by task type
(`crud`, `api`, `test`, and so on).

A skill card is a cheaper specialist than a resident model per framework.
M9's specialist lanes are for media and 3D, not for FastAPI versus pytest.

Once M1 has approvals, put one or two of your own approved diffs in the
prompt, chosen by task type. That is an earlier gain than waiting for the
M8 training run. `MODEL_STRATEGY_ANALYSIS.md` already says to fix prompts
before fine-tuning, and to train only on high-score examples. That matches
Pablo's rule: approved traces only, and a LoRA is promoted only if evals
beat the baseline.

## Leave behind

- The specialist team in the proposal docs. One 3090 cannot hold frontend,
  backend, API, and database models. Lane swap is the version that fits.
- One model per tool (`CONTEXT_TEAM_ARCHITECTURE.md`). Those jobs are
  functions. Chroma in `agents/rag_coder.py` embeds whole files and is what
  M6 replaces with a repo map and symbol lookup.
- The tool zoo. `SYSTEM_ARCHITECTURE.md` consolidates 97 tools into 26
  mode-based tools to save tokens. The real failure was tool-call syntax
  leaking into generated code (`MODEL_STRATEGY_ANALYSIS.md`). Pablo's coder
  should keep returning a diff, with checks outside the model.
- The blended evaluator score. It mixes syntax, wall-clock speed, and
  whether the route was right. Keep checks and route quality as separate
  signals.
- A second rules system. `.aiconfig/rules.md` is the same idea as
  `AGENTS.md`.
- `learning/feedback_collector.py` as a new product. Approve, reject, and
  partial approve already exist. The one idea worth a field later is a
  short reason on reject, stored on the trace.

## Suggested order

1. Finish M1 so there are real traces.
2. M2: complexity comparison, TOON export, exit-code-5 test. Archive this
   folder read-only after that, as the M2 prompt says.
3. When assembling coder prompts: section budget, one skill card, one
   approved example of the same task type.
4. After a few dozen real runs: routing table for coder versus deep, and a
   failure-pattern hint in the next prompt.
5. M7/M8 stay the gate for anything that looks like training.
