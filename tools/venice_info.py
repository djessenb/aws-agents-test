from typing import Any
from strands.types.tools import ToolUse, ToolResult

VENICE_INFO = {
    "name": "Venice",
    "country": "Italy",
    "region": "Veneto",
    "nickname": "The Floating City",
    "population": "About 260,000 (city proper)",
    "language": "Italian (Venetian dialect is also spoken)",
    "currency": "Euro (€)",
    "geography": "Built on 118 small islands connected by 400+ bridges",
    "history": "Founded in 421 AD, became a major maritime power in the 10th century",
    "climate": "Mediterranean with hot summers and cool winters",
    "transportation": "Primarily by boat (vaporetti, gondolas) and on foot",
    "economy": "Tourism, shipbuilding, services, and manufacturing",
    "culture": "Known for art, architecture, music, and Venetian glass",
    "festivals": "Venice Carnival, Venice Film Festival, Festa del Redentore",
    "landmarks": [
        "St. Mark's Basilica",
        "Doge's Palace",
        "Grand Canal",
        "Rialto Bridge",
        "Bridge of Sighs"
    ],
    "fun_fact": "Venice has 177 canals and over 400 bridges, but no roads for cars."
}

TOOL_SPEC = {
    "name": "venice_info",
    "description": "Provides comprehensive information about Venice, Italy.",
    "inputSchema": {
        "json": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
}

def venice_info(tool_use: ToolUse, **kwargs: Any) -> ToolResult:
    """
    Provides comprehensive information about Venice, Italy.
    
    Args:
        tool_use (ToolUse): The tool use object containing the input parameters.
    
    Returns:
        ToolResult: A dictionary containing the generated content and status.
    """
    tool_use_id = tool_use["toolUseId"]
    
    result = "Venice Information:\n\n"
    for key, value in VENICE_INFO.items():
        if isinstance(value, list):
            result += f"{key.capitalize()}:\n" + "\n".join(f"- {item}" for item in value) + "\n\n"
        else:
            result += f"{key.capitalize()}: {value}\n\n"
    
    return {
        "toolUseId": tool_use_id,
        "status": "success",
        "content": [{"text": result}]
    }