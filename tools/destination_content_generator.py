from typing import Any
from strands.types.tools import ToolUse, ToolResult

DESTINATIONS = {
    "Paris": {
        "description": "Paris, the City of Light, is the capital of France and a global center for art, fashion, gastronomy, and culture. Its 19th-century cityscape is crisscrossed by wide boulevards and the River Seine. Beyond iconic landmarks like the Eiffel Tower and Gothic Notre-Dame cathedral, the city is known for its cafe culture and designer boutiques along the Rue du Faubourg Saint-Honoré. Home to world-class museums, the Louvre and Musée d'Orsay, Paris remains a timeless attraction for millions of visitors each year.",
        "images": [
            "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4b/La_Tour_Eiffel_vue_de_la_Tour_Saint-Jacques%2C_Paris_ao%C3%BBt_2014_%282%29.jpg/1200px-La_Tour_Eiffel_vue_de_la_Tour_Saint-Jacques%2C_Paris_ao%C3%BBt_2014_%282%29.jpg",
            "https://upload.wikimedia.org/wikipedia/commons/thumb/6/66/Louvre_Museum_Wikimedia_Commons.jpg/1200px-Louvre_Museum_Wikimedia_Commons.jpg",
            "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1d/Arc_de_Triomphe%2C_Paris_21_October_2010.jpg/1200px-Arc_de_Triomphe%2C_Paris_21_October_2010.jpg"
        ]
    },
    "New York City": {
        "description": "New York City, the most populous city in the United States, is a global hub for finance, culture, art, and entertainment. Comprising five boroughs - Brooklyn, Queens, Manhattan, The Bronx, and Staten Island - the city is renowned for its iconic skyline, Broadway theaters, world-class museums like the Metropolitan Museum of Art, and landmarks such as the Statue of Liberty and Central Park. With its diverse neighborhoods, vibrant street life, and 24/7 energy, New York offers an unparalleled urban experience.",
        "images": [
            "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7a/View_of_Empire_State_Building_from_Rockefeller_Center_New_York_City_dllu_%28cropped%29.jpg/1200px-View_of_Empire_State_Building_from_Rockefeller_Center_New_York_City_dllu_%28cropped%29.jpg",
            "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d3/Statue_of_Liberty%2C_NY.jpg/1200px-Statue_of_Liberty%2C_NY.jpg",
            "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f7/Brooklyn_Bridge_Postdlf.jpg/1200px-Brooklyn_Bridge_Postdlf.jpg"
        ]
    },
    "Tokyo": {
        "description": "Tokyo, Japan's busy capital, mixes the ultramodern and the traditional, from neon-lit skyscrapers to historic temples. The opulent Meiji Shinto Shrine is known for its towering gate and surrounding woods. The Imperial Palace sits amid large public gardens. The city's many museums offer exhibits ranging from classical art (in the Tokyo National Museum) to a reconstructed kabuki theater (in the Edo-Tokyo Museum). Tokyo is also renowned for its vibrant food scene and efficient public transportation system.",
        "images": [
            "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b2/Skyscrapers_of_Shinjuku_2009_January.jpg/1200px-Skyscrapers_of_Shinjuku_2009_January.jpg",
            "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c5/Tokyo_Tower_and_around_Skyscrapers.jpg/1200px-Tokyo_Tower_and_around_Skyscrapers.jpg",
            "https://upload.wikimedia.org/wikipedia/commons/thumb/4/42/Senso-ji_Temple_Asakusa_Tokyo%2C_Japan.jpg/1200px-Senso-ji_Temple_Asakusa_Tokyo%2C_Japan.jpg"
        ]
    }
}

TOOL_SPEC = {
    "name": "destination_content_generator",
    "description": "Generates content based on a destination, including an extensive description and related public images.",
    "inputSchema": {
        "json": {
            "type": "object",
            "properties": {
                "destination": {
                    "type": "string",
                    "description": "The name of the destination to generate content for"
                }
            },
            "required": ["destination"]
        }
    }
}

def destination_content_generator(tool_use: ToolUse, **kwargs: Any) -> ToolResult:
    """
    Generates content based on a destination, including an extensive description and related public images.
    
    Args:
        tool_use (ToolUse): The tool use object containing the input parameters.
    
    Returns:
        ToolResult: A dictionary containing the generated content and status.
    """
    tool_use_id = tool_use["toolUseId"]
    destination = tool_use["input"]["destination"]
    
    if destination not in DESTINATIONS:
        return {
            "toolUseId": tool_use_id,
            "status": "error",
            "content": [{"text": f"Sorry, information for {destination} is not available. Available destinations are: {', '.join(DESTINATIONS.keys())}"}]
        }
    
    info = DESTINATIONS[destination]
    description = info["description"]
    images = info["images"]
    
    result = f"Description of {destination}:\n\n{description}\n\nRelated Images:\n"
    for img in images:
        result += f"{img}\n"
    
    return {
        "toolUseId": tool_use_id,
        "status": "success",
        "content": [{"text": result}]
    }