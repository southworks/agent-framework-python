# Minimal agent example
import asyncio
from agent_client_factory import get_azopenaichatclient

async def main():
    # Create a minimal agent without specific instructions
    agent = get_azopenaichatclient().create_agent()

    # Test the agent with a simple prompt
    result = await agent.run("hello!")

    # Print the agent's response
    print(result.text)

# Run the main function
if __name__ == "__main__":
    asyncio.run(main())
