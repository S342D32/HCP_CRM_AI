"""
==============================================================================
LangGraph Agent - The Brain of the Application
==============================================================================
"""

import re
import json
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, List
import operator
from groq import BadRequestError

# Import tools
from .tools import ALL_TOOLS
from .safe_tools import SafeToolExecutor
from .prompts import SYSTEM_PROMPT

_agent_instance = None


def clean_response(text: str) -> str:
    """Remove reasoning steps from LLM response."""
    if not text:
        return text
    
    lines = text.split('\n')
    cleaned_lines = []
    in_reasoning = False
    
    for line in lines:
        stripped = line.strip()
        
        if not cleaned_lines and not stripped:
            continue
        
        if re.match(r'^##?\s*step\s*\d+', stripped, re.IGNORECASE):
            in_reasoning = True
            continue
        
        if re.match(r'^##?\s*(analyze|identify|extract|check|convert|recall|provide|parse|log|request)', stripped, re.IGNORECASE):
            in_reasoning = True
            continue
        
        if re.match(r'^\d+\.\s*(analyze|identify|extract|check|convert|recall|provide|parse|log|request)', stripped, re.IGNORECASE):
            continue
        
        if 'tools used' in stripped.lower():
            continue
        if stripped.startswith('✓') or stripped.startswith('√'):
            continue
        
        if in_reasoning and not stripped:
            in_reasoning = False
            continue
        
        if in_reasoning:
            continue
        
        cleaned_lines.append(line)
    
    result = '\n'.join(cleaned_lines).strip()
    result = re.sub(r'##?\s*step\s*\d+[^\n]*', '', result, flags=re.IGNORECASE)
    result = re.sub(r'\n{3,}', '\n\n', result)
    
    return result.strip()


class AgentState(TypedDict):
    messages: Annotated[List, operator.add]


class HCPAgent:
    def __init__(self, groq_api_key: str, model_name: str):
        self.llm = ChatGroq(
            api_key=groq_api_key,
            model=model_name,
            temperature=0.1
        ).bind_tools(ALL_TOOLS)

        # ★ Use SafeToolExecutor instead of ToolNode ★
        self.safe_executor = SafeToolExecutor(ALL_TOOLS)
        self.graph = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(AgentState)

        workflow.add_node("agent", self._agent_node)
        
        # ★ Use custom executor instead of ToolNode ★
        workflow.add_node("tools", self._tools_node)

        workflow.set_entry_point("agent")

        workflow.add_conditional_edges(
            "agent",
            self._should_continue,
            {
                "continue": "tools",
                "end": END
            }
        )

        workflow.add_edge("tools", "agent")

        return workflow.compile()

    def _agent_node(self, state: AgentState):
        messages = state["messages"]
        try:
            response = self.llm.invoke(messages)
        except BadRequestError as e:
            # Groq rejected the tool call before it reached our code (bad arg types, etc).
            # Feed the error back to the model and ask it to retry with correct types.
            correction = HumanMessage(content=(
                "Your last tool call was rejected because one or more parameters had the "
                "wrong type (for example, products_discussed must be a JSON array like "
                '["Product A", "Product B"], not a string). Please retry the same tool call '
                "with corrected types. Do not apologize or explain — just call the tool again."
            ))
            retry_messages = messages + [correction]
            try:
                response = self.llm.invoke(retry_messages)
            except BadRequestError:
                # Give up gracefully instead of surfacing a raw 400 to the user.
                response = AIMessage(content=(
                    "I had trouble logging that — could you rephrase the products discussed "
                    "as a simple comma-separated list (e.g. 'Halio, Jasio')?"
                ))
        return {"messages": [response]}

    # ★ Custom tools node that uses SafeToolExecutor ★
    def _tools_node(self, state: AgentState):
        return self.safe_executor.execute(state)

    def _should_continue(self, state: AgentState):
        last_message = state["messages"][-1]

        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "continue"

        return "end"

    def run(self, user_message: str, chat_history: list = []) -> dict:
        messages = [SystemMessage(content=SYSTEM_PROMPT)]

        for msg in chat_history:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))

        messages.append(HumanMessage(content=user_message))

        final_state = self.graph.invoke({"messages": messages})

        tool_calls = []
        tool_results = []
        final_response = ""

        for msg in final_state["messages"]:
            if isinstance(msg, AIMessage) and hasattr(msg, "tool_calls") and msg.tool_calls:
                for tc in msg.tool_calls:
                    tool_calls.append({
                        "name": tc["name"],
                        "args": tc["args"]
                    })

            elif isinstance(msg, ToolMessage):
                tool_results.append({
                    "tool": msg.name,
                    "result": msg.content
                })

        for msg in reversed(final_state["messages"]):
            if isinstance(msg, AIMessage) and msg.content:
                final_response = msg.content
                break

        final_response = clean_response(final_response)

        return {
            "response": final_response,
            "tool_calls": tool_calls,
            "tool_results": tool_results
        }


def init_agent(groq_api_key: str, model_name: str) -> HCPAgent:
    global _agent_instance
    _agent_instance = HCPAgent(groq_api_key, model_name)
    return _agent_instance


def get_agent() -> HCPAgent:
    return _agent_instance