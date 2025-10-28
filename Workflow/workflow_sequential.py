# Example of a sequential workflow using Agent Framework Core

# pip install agent-framework-core
# pip install aioconsole

import asyncio
from agent_utilities import get_input_text
from agent_framework import WorkflowBuilder, WorkflowContext, WorkflowOutputEvent, WorkflowViz, executor
from typing_extensions import Never

@executor(id="upper_case_executor")
async def to_upper_case(text: str, ctx: WorkflowContext[str]) -> None:
    """Transform the input to uppercase and forward it to the next step."""
    result = text.upper()

    await ctx.send_message(result)
	
@executor(id="another_upper")
async def another_to_upper_text(text: str, ctx: WorkflowContext[str]) -> None:
    """Reverse the input and yield the workflow output."""
    result = text.upper()

    await ctx.send_message(result)

@executor(id="reverse_text_executor")
async def reverse_text(text: str, ctx: WorkflowContext[Never, str]) -> None:
    """Reverse the input and yield the workflow output."""
    result = text[::-1]

    # Yield the final output for this workflow run
    # yield_output is used to produce the output of the workflow
    await ctx.yield_output(result)

# Main function to run the workflow
async def main():
    print("Please provide input text (via stdin or command line argument) to process.")
    text = await get_input_text()

    # Build the sequential workflow
    workflow = (
        WorkflowBuilder()
        .add_edge(to_upper_case, another_to_upper_text)
        .add_edge(another_to_upper_text, reverse_text)
        .set_start_executor(to_upper_case)
        .build()
    )

    # Run the workflow and stream events
    async for event in workflow.run_stream(text):
        print(f"Event: {event}")
        if isinstance(event, WorkflowOutputEvent):
            print(f"Workflow completed with result: {event.data}")

if __name__ == "__main__":
    asyncio.run(main())
