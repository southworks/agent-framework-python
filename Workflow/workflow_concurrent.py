import asyncio
import random

from agent_framework import Executor, WorkflowBuilder, WorkflowContext, WorkflowOutputEvent, handler
from agent_utilities import generate_workflow_visualization
from typing_extensions import Never

class Dispatcher(Executor):
    """
    The sole purpose of this executor is to dispatch the input of the workflow to
    other executors.
    """

    @handler
    async def handle(self, numbers: list[int], ctx: WorkflowContext[list[int]]):
        if not numbers:
            raise RuntimeError("Input must be a valid list of integers.")

        await ctx.send_message(numbers)

class Average(Executor):
    """Calculate the average of a list of integers."""

    @handler
    async def handle(self, numbers: list[int], ctx: WorkflowContext[float]):
        average: float = sum(numbers) / len(numbers)
        await ctx.send_message(average)

class Sum(Executor):
    """Calculate the sum of a list of integers."""

    @handler
    async def handle(self, numbers: list[int], ctx: WorkflowContext[int]):
        total: int = sum(numbers)
        await ctx.send_message(total)

class Count(Executor):
    """Count the number of integers in a list."""

    @handler
    async def handle(self, numbers: list[int], ctx: WorkflowContext[int]):
        count: int = len(numbers)
        await ctx.send_message(count)

class Aggregator(Executor):
    """Aggregate the results from the different tasks and yield the final output."""

    @handler
    async def handle(self, results: list[int | float], ctx: WorkflowContext[Never, list[int | float]]):
        await ctx.yield_output(results)

async def main() -> None:
    # Create the executors
    dispatcher = Dispatcher(id="dispatcher")
    count = Count(id="ito")
    summation = Sum(id="summation")
    average = Average(id="average")
    aggregator = Aggregator(id="aggregator")

    # Build a simple fan out and fan in workflow
    workflow = (
        WorkflowBuilder()
        .set_start_executor(dispatcher)
        .add_fan_out_edges(dispatcher, [average, summation, count])
        .add_fan_in_edges([count, summation, average], aggregator)
        .build()
    )
    generate_workflow_visualization(workflow, name="diagrams/workflow_concurrent")

    # Run the workflow
    output: list[int | float] | None = None
    range_number = random.randint(1, 100)
    async for event in workflow.run_stream([random.randint(1, 100) for _ in range(range_number)]):
        if isinstance(event, WorkflowOutputEvent):
            output = event.data

    if output is not None:
        print(output)

# Run the main function
if __name__ == "__main__":
    asyncio.run(main())
