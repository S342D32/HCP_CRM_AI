# README: How This Repo + Tool Calling Works (Teacher → Student)

This document explains (1) how the **frontend** triggers backend work, (2) how the backend uses **tools**, and (3) how **tool calling/history/context** flows end-to-end.

> Note: “Tool calling” here means the agent/backend invoking helper functions (for example, calling internal tool functions) while building up an “interaction trail” (messages + tool results).

---

## 1) Big Picture (What runs where?)

### Frontend (React / Vite)
- The UI lives in `frontend/`.
- It sends user messages to the backend over HTTP (typically via `frontend/src/services/api.js`).
- It renders the chat + shows tool-related events (for example, a “ToolIndicator” component).

### Backend (Python)
- The backend lives in `backend/`.
- It exposes HTTP endpoints in `backend/routes/api.py` (and uses `backend/app.py` to start the server).
- It contains the agent logic in `backend/agent/`.

---

## 2) Step-by-step: User → Frontend → Backend

### Step A — User types a message
- The message is captured in UI components under `frontend/src/components/` (e.g., `ChatInterface.jsx` or `FormInterface.jsx`).

### Step B — Frontend calls backend API
- The message is sent to an endpoint in `backend/routes/api.py`.
- The frontend call is implemented through the API service layer:
  - `frontend/src/services/api.js`

### Step C — Backend receives the request
- `backend/app.py` receives the HTTP request and routes it.
- `backend/routes/api.py` parses input (message text, session info, etc.).

---

## 3) Step-by-step: Backend Agent Execution

### Step D — Backend builds the “agent state”
- The backend prepares conversation messages and any state needed by the agent.

### Step E — Graph/Agent runs
- The orchestration is in `backend/agent/graph.py`.
- The graph coordinates:
  - calling the model,
  - deciding whether a tool should be used,
  - executing the tool,
  - feeding tool output back into the model.

> If the repo uses a LangGraph-like approach, the “graph” is a workflow of nodes (actions), and edges define how the run proceeds based on state.

---

## 4) How Tool Calling Works (Conceptually)

### Step F — Model decides to use a tool
- During the run, the model may output something like:
  - “Call tool X with arguments Y”.

### Step G — Backend executes the tool
- Tools are defined in `backend/agent/tools.py`.
- Some tools might be wrapped/guarded:
  - `backend/agent/safe_tools.py`

### Step H — Tool result is appended to the conversation history
- After the tool executes, its output is added to the agent’s message history/state.

### Step I — Model continues with tool output
- The model is called again (or continues) with the updated context:
  - the new messages include the tool output,
  - so the model can incorporate results and decide the next action.

---

## 5) How “History & Context” is maintained

To make the agent coherent, the backend maintains:

1. **User messages** (what the user said)
2. **Assistant messages** (what the model said)
3. **Tool messages** (tool name + tool output)
4. **Any structured state** (session id, intermediate results, etc.)

This history is what gives the model context.

---

## 6) How Frontend displays tool usage

Typically:
- Tool events are either returned as part of the backend response (e.g., in a JSON field like `tools`, `steps`, `messages`), or
- The backend returns an interaction list that the UI renders.

Components like `frontend/src/components/ToolIndicator.jsx` and `InteractionList.jsx` are used to show:
- when a tool is called,
- what it returned,
- and how that affected the final answer.

---

## 7) Suggested “Mental Model” for Students

Think of the agent run like a loop:

1. Ask model: “What should we do next?”
2. If it says “use a tool”:
   - execute tool in backend
   - record tool output as a message
3. Ask model again with the new information
4. Repeat until the model produces the final answer

That loop is the core reason tool calling + history/context matters.

---

## 8) Quick File Map (Where to look)

- `backend/app.py`
  - starts server / app wiring
- `backend/routes/api.py`
  - HTTP endpoints
- `backend/agent/graph.py`
  - agent workflow/orchestration
- `backend/agent/tools.py`
  - tool implementations
- `backend/agent/safe_tools.py`
  - safe/wrapped versions of tools
- `frontend/src/services/api.js`
  - API calls to backend
- `frontend/src/components/ChatInterface.jsx`
  - chat input + output rendering
- `frontend/src/components/ToolIndicator.jsx`
  - tool status display
- `frontend/src/components/InteractionList.jsx`
  - rendering the interaction trail

---

## 9) Troubleshooting Notes

- If you see missing tool outputs in UI:
  - verify backend returns tool results in the JSON response
  - verify frontend expects the same field names
- If the agent doesn’t call tools:
  - check tool registration in `backend/agent/tools.py`
  - check the prompts / system instructions in `backend/agent/prompts.py`

---

## 10) How to run (basic)

Check `frontend/package.json` for scripts (Vite).
Check `backend/requirements.txt` and run the backend with whatever command `backend/app.py` uses.

(If you want, I can add exact run commands based on the existing package.json / backend startup code.)

