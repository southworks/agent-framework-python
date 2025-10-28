# This is an example of Agent Middleware.
import asyncio

from collections.abc import Awaitable, Callable
from agent_framework import FunctionInvocationContext
from agent_client_factory import get_azopenaichatclient
from datetime import datetime

# Function that returns the current time
def get_time():
    """Get the current time."""
    return datetime.now().strftime("%H:%M:%S")

# Middleware to log function calls
# There are several types of middleware you can create, you can fin more details in the documentation.
# https://learn.microsoft.com/en-us/agent-framework/user-guide/agents/agent-middleware?pivots=programming-language-python
# - Agent Middleware
# - Function Middleware
# - Chat Middleware
async def logging_function_middleware(
    context: FunctionInvocationContext,
    next: Callable[[FunctionInvocationContext], Awaitable[None]],
) -> None:
    """Middleware that logs function calls."""
    print(f"The middleware was called from function '{context.function.name}'")
    await next(context)
    print(f"Result from function '{context.function.name}': {context.result}")

# Main function to create an agent with middleware and tools
async def main():
    # Add both the function and middleware to your agent
    agent = get_azopenaichatclient().create_agent(
        name="TimeAgent",
        instructions="You can tell the current time.",
        tools=[get_time],
        middleware=[logging_function_middleware],
    )

    result = await agent.run("What time is it?")
    print(result.text)

# Run the main function
if __name__ == "__main__":
    asyncio.run(main())
