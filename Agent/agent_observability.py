# This is a minimal example to test agent observability setup.
# This is the same code as in agent_minimal.py but with observability enabled.
import asyncio
from agent_client_factory import get_azopenaichatclient
from agent_framework.observability import setup_observability

# This is the only change compared to agent_minimal.py
setup_observability(enable_sensitive_data=False)

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
