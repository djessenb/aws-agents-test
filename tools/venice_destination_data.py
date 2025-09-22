from typing import Any
from strands.types.tools import ToolUse, ToolResult

VENICE_DATA = {
    "description": "Venice, the capital of northern Italy's Veneto region, is built on more than 100 small islands in a lagoon in the Adriatic Sea. It has no roads, just canals – including the Grand Canal thoroughfare – lined with Renaissance and Gothic palaces. The central square, Piazza San Marco, contains St. Mark's Basilica, which is tiled with Byzantine mosaics, and the Campanile bell tower offering views of the city's red roofs. Known for its romantic gondola rides, stunning architecture, and rich history, Venice is often called the 'City of Canals' or 'The Floating City'.",
    "attractions": [
        "St. Mark's Basilica",
        "Doge's Palace",
        "Grand Canal",
        "Rialto Bridge",
        "Bridge of Sighs"
    ],
    "cuisine": [
        "Risotto al nero di seppia (Squid ink risotto)",
        "Sarde in saor (Sweet and sour sardines)",
        "Baccalà mantecato (Creamed dried cod)",
        "Bigoli in salsa (Whole wheat pasta with onions and anchovy sauce)"
    ],
    "best_time_to_visit": "April to June or September to November",
    "images": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/d/df/Venice_-_Rialto_Bridge3.jpg/1280px-Venice_-_Rialto_Bridge3.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/0/09/Basilica_di_San_Marco_%28Venice%29_-_Interior.jpg/1280px-Basilica_di_San_Marco_%28Venice%29_-_Interior.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1e/Gondola_on_the_Grand_Canal_%28Venice%2C_Italy%29.jpg/1280px-Gondola_on_the_Grand_Canal_%28Venice%2C_Italy%29.jpg"
    ]
}

TOOL_SPEC = {
    "name": "venice_destination_data",
    "description": "Generates destination data for Venice, including description, attractions, cuisine, best time to visit, and images.",
    "inputSchema": {
        "json": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
}

def venice_destination_data(tool_use: ToolUse, **kwargs: Any) -> ToolResult:
    """
    Generates destination data for Venice, including description, attractions, cuisine, best time to visit, and images.
    
    Args:
        tool_use (ToolUse): The tool use object containing the input parameters.
    
    Returns:
        ToolResult: A dictionary containing the generated content and status.
    """
    tool_use_id = tool_use["toolUseId"]
    
    result = f"Venice Destination Data:\n\n"
    result += f"Description:\n{VENICE_DATA['description']}\n\n"
    result += f"Top Attractions:\n" + "\n".join(f"- {attraction}" for attraction in VENICE_DATA['attractions']) + "\n\n"
    result += f"Local Cuisine:\n" + "\n".join(f"- {dish}" for dish in VENICE_DATA['cuisine']) + "\n\n"
    result += f"Best Time to Visit: {VENICE_DATA['best_time_to_visit']}\n\n"
    result += f"Images:\n" + "\n".join(VENICE_DATA['images'])
    
    return {
        "toolUseId": tool_use_id,
        "status": "success",
        "content": [{"text": result}]
    }