# pip install agent-framework-core
import asyncio

from agent_framework import (
    FileCheckpointStorage,
    WorkflowBuilder,
    WorkflowContext,
    executor,
)
from agent_utilities import generate_workflow_visualization, get_input_text
from typing_extensions import Never

CHECKPOINTS_FOLDER = "workflow_checkpoints_storage"

@executor(id="first_executor")
async def first(text: str, ctx: WorkflowContext[str]) -> None:
    """Replaces spaces with underscores in the input text."""
    await ctx.send_message(text.replace(' ', '_'))

@executor(id="second_executor")
async def second(text: str, ctx: WorkflowContext[str]) -> None:
    """Converts the text to uppercase."""
    await ctx.send_message(text.upper())

@executor(id="third_executor")
async def third(text: str, ctx: WorkflowContext[str]) -> None:
    """Add dots between the characters."""
    await ctx.send_message('.'.join(text))

@executor(id="final_executor")
async def final(text: str, ctx: WorkflowContext[Never]) -> None:
    """Yields the final processed text."""
    await ctx.yield_output(text)


async def main() -> None:
    # Checkpoint storage
    checkpoint_storage = FileCheckpointStorage(CHECKPOINTS_FOLDER)

    # Another option is to use the built-in in-memory storage
    # second_checkpoint_storage = InMemoryCheckpointStorage()

    # Build workflow with checkpointing enabled
    workflow = (
        WorkflowBuilder()
        .set_start_executor(first)
        .add_edge(first, second)
        .add_edge(second, third)
        .add_edge(third, final)
        .with_checkpointing(checkpoint_storage)
        .build()
    )

    generate_workflow_visualization(workflow, name="diagrams/workflow_checkpoints")

    # Run the workflow and create checkpoints
    print("\nRunning the workflow")
    input_text = "¡Checkpoints are great!"
    async for event in workflow.run_stream(input_text):
        print(f"Event: {event}")

    print("\nBelow you can see the saved checkpoints:")
    print(f"The checkpoint files are stored in the '{CHECKPOINTS_FOLDER}' folder.\n")
    checkpoints = await checkpoint_storage.list_checkpoints(workflow_id=workflow.id)
    for cp in checkpoints:
        print(f"Checkpoint ID: {cp.checkpoint_id}, Messages: {cp.messages}")

    last_checkpoint_id = await get_input_text("\nPaste the checkpoint ID to resume from (or press Enter to use the first checkpoint in the list):")
    if not last_checkpoint_id:
        last_checkpoint_id = checkpoints[0].checkpoint_id

    # Resume workflow from a specific checkpoint
    print(f"\nResuming from checkpoint: {last_checkpoint_id}")
    for event in await workflow.run_from_checkpoint(last_checkpoint_id):
        print(f"Event: {event}")

if __name__ == "__main__":
    asyncio.run(main())
