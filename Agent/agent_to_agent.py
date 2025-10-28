# Demonstrates connecting to and communicating with an A2A-compliant agent.

import asyncio
import httpx

from a2a.client import A2ACardResolver
from agent_framework.a2a import A2AAgent

async def main():
    """Demonstrates connecting to and communicating with an A2A-compliant agent."""
    
    # Set A2A agent host URL
    a2a_agent_host = "agent_host_url"
    if not a2a_agent_host:
        raise ValueError("A2A_AGENT_HOST environment variable is not set")

    print(f"Connecting to A2A agent at: {a2a_agent_host}")

    # Initialize A2ACardResolver
    async with httpx.AsyncClient(timeout=60.0) as http_client:
        resolver = A2ACardResolver(httpx_client=http_client, base_url=a2a_agent_host)

        # Get agent card
        agent_card = await resolver.get_agent_card(relative_card_path="/.well-known/agent.json")
        print(f"Found agent: {agent_card.name} - {agent_card.description}")

        # Create A2A agent instance
        agent = A2AAgent(
            name=agent_card.name,
            description=agent_card.description,
            agent_card=agent_card,
            url=a2a_agent_host,
        )

        # Invoke the agent and output the result
        print("\nSending message to A2A agent...")
        response = await agent.run("Tell me a joke about a pirate.")

        # Print the response
        print("\nAgent Response:")
        for message in response.messages:
            print(message.text)


if __name__ == "__main__":
    asyncio.run(main())
