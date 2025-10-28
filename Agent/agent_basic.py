# Basic agent example
import asyncio
from agent_framework import ChatMessage, Role, TextContent, UriContent
from agent_client_factory import get_azopenaichatclient

# Message with image content
message = ChatMessage(
    # User role, you can also use Role.ASSISTANT, Role.TOOL or Role.SYSTEM
    role=Role.USER,
    contents=[
        TextContent(text="Tell me a joke about this image?"),
        UriContent(uri="https://upload.wikimedia.org/wikipedia/commons/thumb/7/73/Pennywise_Cosplay_3.jpg/250px-Pennywise_Cosplay_3.jpg", media_type="image/jpeg")
    ]
)

async def main():
    # Create a minimal agent with instructions
    agent = get_azopenaichatclient().create_agent(
        instructions="You are good at telling jokes.",
        name="Joker"
    )
    
    GPT_JOKE_PROMPT = "Tell me a joke about a ChatGPT."
    print(GPT_JOKE_PROMPT)
    # Call the agent in a streaming manner for the GPT joke
    async for update in agent.run_stream(GPT_JOKE_PROMPT):
        if update.text:
            print(update.text, end="", flush=True)
    print()

    PIRATE_JOKE_PROMPT = "Tell me a joke about a pirate."
    print(PIRATE_JOKE_PROMPT)
    # Call the agent synchronously for the pirate joke
    result_pirate_joke = await agent.run(PIRATE_JOKE_PROMPT)
    print(result_pirate_joke.text)
    print()

    IMAGE_JOKE_PROMPT = "Tell me a joke about this image: https://upload.wikimedia.org/wikipedia/commons/thumb/7/73/Pennywise_Cosplay_3.jpg/250px-Pennywise_Cosplay_3.jpg"
    print(IMAGE_JOKE_PROMPT)
    # Call the agent synchronously for the image joke
    result_clown_joke = await agent.run(message)
    print(result_clown_joke.text)
    print()

# Run the main function
if __name__ == "__main__":
    asyncio.run(main())
