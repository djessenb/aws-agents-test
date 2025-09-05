from strands import Agent
from strands_tools import calculator

# Create agent with tools and EU model
agent = Agent(
    tools=[calculator],
    model="anthropic.claude-3-5-sonnet-20240620-v1:0"  # Updated model ID for EU region
)

result = agent("What is the square root of 1764")
print(result)

from mcp.client.streamable_http import streamablehttp_client
from strands import Agent
from strands.tools.mcp.mcp_client import MCPClient

def create_streamable_http_transport():
   return streamablehttp_client("http://localhost:8000/mcp/")

streamable_http_mcp_client = MCPClient(create_streamable_http_transport)

# Use the MCP server in a context manager
with streamable_http_mcp_client:

    # Get the tools from the MCP server
    tools = streamable_http_mcp_client.list_tools_sync()

    # Create agent with tools and EU model
    agent = Agent(
        tools=tools,
        model="anthropic.claude-3-5-sonnet-20240620-v1:0"  # Updated model ID for EU region
    )

    # Let the agent handle the tool selection and parameter extraction
    response = agent("What is 125 plus 375?")
    print(response)
    response = agent("If I have 1000 and spend 246, how much do I have left?")
    print(response)
    response = agent("What is 24 multiplied by 7 divided by 3?")
    print(response)