# Evaluation Sets

This directory contains evaluation sets for testing the Self-Evolving Agent.

## Running Evaluations

```bash
# Run all evalsets
agents-cli eval run --all

# Run specific evalset
agents-cli eval run --evalset tests/eval/evalsets/use_existing_tool.evalset.json
agents-cli eval run --evalset tests/eval/evalsets/create_new_tool.evalset.json
agents-cli eval run --evalset tests/eval/evalsets/safety.evalset.json
```

## Evalsets

| File | What it tests |
|------|---------------|
| `use_existing_tool.evalset.json` | Agent finds and uses pre-registered tools from the registry |
| `create_new_tool.evalset.json` | Full pipeline: spec → code → test → sandbox → register → execute |
| `safety.evalset.json` | Agent refuses unsafe requests and blocks dangerous tool creation |

## Evaluation Metrics

Configured in `eval_config.json`:

- **tool_use_quality**: Registry-first behavior, correct tool execution, pipeline triggering, post-pipeline registration
- **final_response_quality**: Result accuracy, clear presentation, tool transparency, safety compliance
