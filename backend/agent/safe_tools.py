"""
==============================================================================
Safe Tool Executor - Fixes LLM Type Mistakes Before Execution
==============================================================================
The LLM often generates wrong types:
- Passes "[\"product\"]" (string) instead of ["product"] (array)
- Passes "true" (string) instead of true (boolean)
- Passes "123" (string) instead of 123 (integer)

This executor intercepts tool calls and fixes these mistakes BEFORE
the ToolNode validates them.
"""

import json
from typing import List, Dict, Any, Optional
from langchain_core.messages import ToolMessage
from langchain_core.tools import BaseTool


class SafeToolExecutor:
    """
    A drop-in replacement for ToolNode that normalizes parameter types.
    
    How it works:
    1. Reads the tool's expected schema (from type hints)
    2. Compares with what the LLM actually sent
    3. Converts types to match the schema
    4. Then executes the tool
    """

    def __init__(self, tools: List[BaseTool]):
        self.tools_by_name = {t.name: t for t in tools}

    def _get_expected_types(self, tool_name: str) -> Dict[str, str]:
        """
        Extract expected parameter types from tool's Pydantic schema.
        
        Returns: {"param_name": "array", "param_name": "boolean", ...}
        """
        if tool_name not in self.tools_by_name:
            return {}
        
        tool = self.tools_by_name[tool_name]
        schema = tool.get_input_schema().schema()
        properties = schema.get('properties', {})
        
        types = {}
        for param_name, param_info in properties.items():
            # Get the primary type
            param_type = param_info.get('type', 'string')
            
            # Check for array items type
            if param_type == 'array' and 'items' in param_info:
                item_type = param_info['items'].get('type', 'string')
                types[param_name] = f"array<{item_type}>"
            else:
                types[param_name] = param_type
        
        return types

    def _normalize_value(self, value: Any, expected_type: str) -> Any:
        """
        Convert a value to the expected type.
        """
        # ── Array type ──────────────────────────────────────────────
        if expected_type.startswith('array'):
            if isinstance(value, list):
                # Already a list - just clean it
                return self._clean_array(value)
            
            if isinstance(value, str):
                # LLM sent a string that should be an array
                stripped = value.strip()
                
                # Try to parse as JSON
                if stripped.startswith('['):
                    try:
                        parsed = json.loads(stripped)
                        if isinstance(parsed, list):
                            return self._clean_array(parsed)
                    except json.JSONDecodeError:
                        pass
                
                # Try to parse escaped JSON (double-escaped)
                if '\\"' in stripped or "\\'" in stripped:
                    try:
                        # Handle double-escaped quotes
                        cleaned = stripped.replace('\\"', '"').replace("\\'", "'")
                        parsed = json.loads(cleaned)
                        if isinstance(parsed, list):
                            return self._clean_array(parsed)
                    except json.JSONDecodeError:
                        pass
                
                # Last resort: split by comma
                if stripped and stripped.lower() not in ('none', 'null', 'n/a', ''):
                    return [s.strip() for s in stripped.split(',') if s.strip()]
                
                return []
            
            if value is None:
                return []
            
            # Any other type, wrap in list
            return [value]
        
        # ── Boolean type ────────────────────────────────────────────
        if expected_type == 'boolean':
            if isinstance(value, bool):
                return value
            
            if isinstance(value, str):
                return value.strip().lower() in ('true', '1', 'yes', 'yeah')
            
            if isinstance(value, (int, float)):
                return bool(value)
            
            if value is None:
                return False
            
            return False
        
        # ── Integer type ────────────────────────────────────────────
        if expected_type == 'integer':
            if isinstance(value, int) and not isinstance(value, bool):
                return value
            
            if isinstance(value, str):
                try:
                    return int(value.strip())
                except ValueError:
                    return None
            
            if isinstance(value, float):
                return int(value)
            
            return None
        
        # ── Number type ─────────────────────────────────────────────
        if expected_type == 'number':
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                return value
            
            if isinstance(value, str):
                try:
                    return float(value.strip())
                except ValueError:
                    return None
            
            return None
        
        # ── String type (default) ──────────────────────────────────
        if isinstance(value, str):
            return value
        
        if value is None:
            return ""
        
        # Convert dicts/lists to string (for summary, notes, etc.)
        if isinstance(value, (dict, list)):
            # If it's a dict that looks like follow-up notes, extract the action
            if isinstance(value, dict) and 'action' in value:
                return value.get('action', str(value))
            return str(value)
        
        return str(value)

    def _clean_array(self, arr: list) -> list:
        """Clean up array items - remove empty strings, strip whitespace."""
        cleaned = []
        for item in arr:
            if isinstance(item, str):
                item = item.strip()
                if item and item.lower() not in ('none', 'null', 'n/a', ''):
                    cleaned.append(item)
            elif item is not None:
                cleaned.append(item)
        return cleaned

    def _fix_follow_up_notes(self, notes: Any) -> str:
        """
        Specifically handle follow_up_notes which LLM often sends as JSON.
        """
        if isinstance(notes, str):
            # If it's a JSON string, try to extract meaningful text
            try:
                parsed = json.loads(notes)
                if isinstance(parsed, dict):
                    parts = []
                    if 'action' in parsed:
                        parts.append(parsed['action'])
                    if 'timeline' in parsed:
                        parts.append(f"(Timeline: {parsed['timeline']})")
                    if 'reasoning' in parsed:
                        parts.append(f"- {parsed['reasoning']}")
                    return ' '.join(parts) if parts else notes
                elif isinstance(parsed, list):
                    # List of recommendation objects
                    actions = []
                    for item in parsed[:2]:  # Take first 2
                        if isinstance(item, dict) and 'action' in item:
                            actions.append(item['action'])
                    return '; '.join(actions) if actions else notes
            except (json.JSONDecodeError, TypeError):
                pass
            
            # Check for double-escaped JSON
            if '\\"' in notes:
                try:
                    cleaned = notes.replace('\\"', '"')
                    parsed = json.loads(cleaned)
                    if isinstance(parsed, dict) and 'action' in parsed:
                        return parsed['action']
                except:
                    pass
            
            return notes
        
        if isinstance(notes, dict):
            return notes.get('action', str(notes))
        
        if isinstance(notes, list):
            return '; '.join(str(item) for item in notes[:2])
        
        return str(notes) if notes else ""

    def normalize_params(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize all parameters for a tool call.
        """
        expected_types = self._get_expected_types(tool_name)
        normalized = {}
        
        for key, value in params.items():
            expected_type = expected_types.get(key, 'string')
            
            # Special handling for follow_up_notes
            if key == 'follow_up_notes':
                normalized[key] = self._fix_follow_up_notes(value)
                continue
            
            # Special handling for products_discussed - filter out dosages
            if key == 'products_discussed':
                normalized_value = self._normalize_value(value, expected_type)
                if isinstance(normalized_value, list):
                    # Remove items that look like dosages (e.g., "50mg", "100mg")
                    cleaned = []
                    for item in normalized_value:
                        if not isinstance(item, str):
                            cleaned.append(item)
                        elif not self._looks_like_dosage(item):
                            cleaned.append(item)
                    normalized[key] = cleaned
                else:
                    normalized[key] = normalized_value
                continue
            
            normalized[key] = self._normalize_value(value, expected_type)
        
        return normalized

    def _looks_like_dosage(self, text: str) -> bool:
        """Check if a string looks like a dosage rather than a product name."""
        import re
        dosage_patterns = [
            r'^\d+\s*mg$',           # "50mg", "100 mg"
            r'^\d+\s*ml$',           # "10ml"
            r'^\d+\s*mcg$',          # "25mcg"
            r'^\d+\s*mg/\d+\s*ml$',  # "50mg/2ml"
            r'^\d+\s*tablet',        # "1 tablet"
            r'^\d+\s*capsule',       # "2 capsules"
            r'^once\s+',             # "once daily"
            r'^twice\s+',            # "twice daily"
            r'^\d+\s*times\s+',      # "3 times daily"
            r'^daily$',              # "daily"
            r'^bid$',                # "bid"
            r'^tid$',                # "tid"
        ]
        text = text.strip().lower()
        return any(re.match(pattern, text) for pattern in dosage_patterns)

    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute tool calls with normalized parameters.
        
        This replaces ToolNode in the graph.
        """
        messages = state["messages"]
        last_message = messages[-1]
        
        tool_messages = []
        logged_this_call = False  # guards against duplicate log_interaction in one turn

        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            for tc in last_message.tool_calls:
                tool_name = tc['name']
                tool_call_id = tc['id']
                if tool_name == 'log_interaction' and logged_this_call:
                    tool_messages.append(ToolMessage(
                        content=json.dumps({
                            "success": False,
                            "error": "log_interaction already called this turn; skipped duplicate."
                        }),
                        name=tool_name,
                        tool_call_id=tool_call_id
                    ))
                    continue
                # Normalize the parameters
                raw_args = tc.get('args', {})
                normalized_args = self.normalize_params(tool_name, raw_args)
                
                # Log the normalization (for debugging)
                if normalized_args != raw_args:
                    print(f"[SAFE-TOOLS] Fixed types for {tool_name}:")
                    for key in set(list(raw_args.keys()) + list(normalized_args.keys())):
                        raw_val = raw_args.get(key, 'MISSING')
                        norm_val = normalized_args.get(key, 'MISSING')
                        if raw_val != norm_val:
                            print(f"  {key}: {type(raw_val).__name__} {repr(raw_val)[:60]} → {type(norm_val).__name__} {repr(norm_val)[:60]}")
                
                # Execute the tool
                if tool_name in self.tools_by_name:
                    tool = self.tools_by_name[tool_name]
                    try:
                        result = tool.invoke(normalized_args)
                        if tool_name == 'log_interaction':
                            logged_this_call = True
                        tool_messages.append(ToolMessage(
                            content=str(result),
                            name=tool_name,
                            tool_call_id=tool_call_id
                        ))
                    except Exception as e:
                        tool_messages.append(ToolMessage(
                            content=json.dumps({"success": False, "error": f"Tool execution failed: {str(e)}"}),
                            name=tool_name,
                            tool_call_id=tool_call_id
                        ))
                else:
                    tool_messages.append(ToolMessage(
                        content=json.dumps({"success": False, "error": f"Unknown tool: {tool_name}"}),
                        name=tool_name,
                        tool_call_id=tool_call_id
                    ))
        
        return {"messages": tool_messages}