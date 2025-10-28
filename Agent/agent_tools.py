# This agent uses web search and Microsoft Learn MCP tools to get the latest SKU and pricing information for Azure Express Route.
import asyncio

from agent_client_factory import get_azopenaichatclient
from agent_framework import ChatAgent, HostedMCPTool, HostedWebSearchTool

PROMPT = (
    "I need the latest information related to SKUs of Azure Express Route and it prices"
    "Don't create an overview, add all the SKU details and alternatives available in Azure Express Route."
    "Respond in a concise table with the SKU names, bandwidth, and monthly price and add all the relevant links."
)

async def main():
    chat_client = get_azopenaichatclient()

    # In this example, we create a ChatAgent with two tools: HostedMCPTool and HostedWebSearchTool.
    # agent_framework.HostedCodeInterpreterTool can also be used if code execution is needed.
    # agent_framework.BaseTool can be used to create custom tools as well.
    agent = ChatAgent(
        chat_client=chat_client,
        instructions="You are a documentation assistant expert in Azure services",
        tools=[
            HostedMCPTool(
                name="Microsoft Learn MCP",
                url="https://learn.microsoft.com/api/mcp"
            ),
            HostedWebSearchTool(
                description="Useful for searching the web for up-to-date information about Azure services and products",
            )
        ]
    )

    result = await agent.run(PROMPT)
    print(result.text)

if __name__ == "__main__":
    asyncio.run(main())
