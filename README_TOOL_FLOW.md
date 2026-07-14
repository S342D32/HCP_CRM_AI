# LangGraph Project

A quick guide for running this repo and understanding how frontend ↔ backend tool calling works.

---

# README: Backend + Frontend + Tool Calling (Teacher → Student)


This repo contains:
- **Frontend** (React/Vite) in `frontend/`
- **Backend** (Python) in `backend/`

It also includes an agent workflow (tool calling + history/context) implemented on the backend.

---

## 1) How to run the project

### Backend (Python)
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   (Run this inside `backend/`)

2. Start the server:
   ```bash
   python app.py
   ```
   (Run this inside `backend/`)

3. Environment variables:
   - Use `backend/.env.example` as a template.
   - Ensure your real `.env` is **not committed** (it is ignored by `.gitignore`).

### Frontend (React / Vite)
1. Install dependencies:
   ```bash
   npm install
   ```
   (Run this inside `frontend/`)

2. Start dev server:
   ```bash
   npm run dev
   ```

---

## 2) Important: `.env.example` + Git push behavior

- The repo includes an **example env file** (so you can see required variables).
- During `git push`, the real `.env` file must be excluded.
- This is handled by `.gitignore`.

Expected behavior:
- ✅ Commit `backend/.env.example`
- ❌ Do **not** commit `backend/.env`

---

## 3) End-to-end flow: Frontend → Backend → Agent → Tools

### Step A — User types a message (Frontend)
- The UI (React) captures the user’s input.
- Components involved commonly include:
  - `frontend/src/components/ChatInterface.jsx`
  - `frontend/src/components/FormInterface.jsx`

### Step B — Frontend sends the request to the backend
- The message is sent via an API call.
- API wrapper is typically:
  - `frontend/src/services/api.js`

### Step C — Backend receives the request
- Backend server wiring is in:
  - `backend/app.py`
- HTTP endpoints are in:
  - `backend/routes/api.py`

### Step D — Backend constructs agent state (history/context)
- The backend prepares:
  - conversation history (messages so far)
  - any session identifiers (if used)
  - and any additional state needed by the agent graph

### Step E — Agent graph runs (Tool calling orchestration)
- The orchestration/graph logic is in:
  - `backend/agent/graph.py`

The graph controls the loop:
1. Ask the model what to do next
2. If the model requests a tool:
   - execute the tool
   - append tool output to history
3. Ask the model again, now with the new tool result
4. Stop when the model produces the final answer

---

## 4) Where tools are implemented

- Tool implementations live in:
  - `backend/agent/tools.py`
- “Safe” or guarded wrappers live in:
  - `backend/agent/safe_tools.py`

---

## 5) What “history & context” means (student-friendly)

Think of the agent run like a conversation log.
Every time something happens, it gets added to the log:
1. **User message**: what the user asked
2. **Assistant message**: what the model decided
3. **Tool message**: what the tool returned
4. (Then the model reads the updated log and continues)

Without tool outputs being appended into history, the model cannot correctly reference what tools returned.

---

## 6) How frontend shows tool usage

Typically the backend response includes structured data such as:
- which tools were called
- tool outputs (or summaries)
- intermediate steps

The frontend renders that as part of the UI using components such as:
- `frontend/src/components/ToolIndicator.jsx`
- `frontend/src/components/InteractionList.jsx`

---

## 7) Quick “mental model” (loop)

1. Frontend sends message to backend
2. Backend runs agent graph
3. Graph/model may request a tool
4. Backend executes tool and saves tool output into history
5. Model continues using the updated history
6. Backend returns the final response + any tool trace
7. Frontend displays the answer (and tool trace)

---

## 8) Files map (where to look)

- `frontend/`
  - `src/services/api.js` (frontend → backend HTTP calls)
  - `src/components/*` (UI rendering, tool display)

- `backend/`
  - `app.py` (server start + wiring)
  - `routes/api.py` (HTTP endpoints)
  - `agent/graph.py` (agent workflow + loop)
  - `agent/tools.py` (tool implementations)
  - `agent/safe_tools.py` (guarded tool variants)

---

## 9) If something breaks (common checks)

- Backend can’t start:
  - verify dependencies with `pip install -r requirements.txt`
  - verify environment variables copied from `.env.example`

- Frontend can’t call backend:
  - verify backend port / base URL in `frontend/src/services/api.js`

- Tool output not appearing in UI:
  - verify backend response includes tool trace fields
  - verify frontend expects the same response shape

