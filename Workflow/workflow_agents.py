# Workflow to demonstrate a simple workflow with two agents: a Writer and a Reviewer.
import asyncio

from agent_client_factory import get_azopenaichatclient
from agent_framework import AgentExecutor, AgentRunEvent, WorkflowBuilder
from agent_utilities import generate_workflow_visualization

async def main() -> None:
    # Create the chat client
    agent = get_azopenaichatclient()

    # Create a Writer agent that generates content
    writer = AgentExecutor(agent.create_agent(
        name="Writer",
        instructions=(
            "You are an excellent content writer. You create new content and edit contents based on the feedback."
        ),
    ), id="writer")

    # Create a Reviewer agent that provides feedback
    reviewer = AgentExecutor(agent.create_agent(
        name="Reviewer",
        instructions=(
            "You are an excellent content reviewer. "
            "Provide actionable feedback to the writer about the provided content. "
            "Provide the feedback in the most concise manner possible."
        ),
    ), id="reviewer")

    # Build the workflow with agents as executors
    workflow = WorkflowBuilder().set_start_executor(writer).add_edge(writer, reviewer).build()
    generate_workflow_visualization(workflow, name="diagrams/workflow_agents")

    # Run the workflow
    workflow_result = await workflow.run("Create a slogan for a new full gas SUV that is affordable and strong.")
    for event in workflow_result:
        if isinstance(event, AgentRunEvent):
            print(f"Agent: {event.executor_id} - Agent response: {event.data}")

# Run the main function
if __name__ == "__main__":
    asyncio.run(main())
