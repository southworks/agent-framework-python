# Demonstrates using multiple threads with a single agent instance.
import asyncio
from agent_client_factory import get_azopenaichatclient

async def main():
    # Create a minimal agent with instructions
    agent = get_azopenaichatclient().create_agent(
        instructions="You are good at telling jokes.",
        name="Joker"
    )

    # Create separate threads for different joke contexts
    pirate_joke_thread = agent.get_new_thread()
    robot_joke_thread = agent.get_new_thread()

    # Run jokes in parallel using the different threads
    pirate_joke = await agent.run("Tell me a joke about a pirate.", thread=pirate_joke_thread)
    print(pirate_joke.text)

    robot_joke = await agent.run("Tell me a joke about a robot.", thread=robot_joke_thread)
    print(robot_joke.text)

    # Continue the conversations in their respective threads
    pirate_joke_2 = await agent.run("Now explain the joke", thread=pirate_joke_thread)
    print(f"\nPirate joke explanation: {pirate_joke_2.text}")

    robot_joke_2 = await agent.run("Now explain the joke.", thread=robot_joke_thread)
    print(f"\nRobot joke explanation: {robot_joke_2.text}")

# Run the main function
if __name__ == "__main__":
    asyncio.run(main())
