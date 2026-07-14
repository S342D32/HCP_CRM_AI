# TODO

## Fix agent tool-call validation error (log_interaction null required fields)
- [x] Update agent/prompt or tool interface so `log_interaction` is never called with nulls for required fields (`interaction_type`, `date`, `summary`, `key_discussions`, `products_discussed`, `hcp_sentiment`).
- [x] Add defensive defaults inside `log_interaction` (convert null -> valid defaults) OR add an argument guard before the tool executes.
- [ ] Update prompts/workflow if needed to enforce calling summarize/assigning defaults before logging.
- [ ] Run a quick local test (trigger /api/chat with an example message) and confirm no Groq 400 occurs.


