# Workflow to demonstrate agent handoff based on user queries about math or history.
import asyncio
from agent_framework import AgentExecutor, WorkflowBuilder
from agent_client_factory import get_azopenaichatclient

# Math Tutor Agent
def create_math_tutor(agent) -> AgentExecutor:
    return AgentExecutor(agent.create_agent(
        name="Math_Tutor",
        instructions="You provide help with math problems. Explain your reasoning at each step and include examples. Only respond about math.",
    ), id="math_tutor")

# History Tutor Agent
def create_history_tutor(agent) -> AgentExecutor:
    return AgentExecutor(agent.create_agent(
        name="History_Tutor",
        instructions="You provide assistance with historical queries. Explain important events and context clearly. Only respond about history.",
    ), id="history_tutor")

# Triage Agent to determine which tutor to handoff to
def create_triage_agent(agent) -> AgentExecutor:
    return AgentExecutor(agent.create_agent(
        name="Triage_Agent",
        instructions="You determine which agent to use based on the user's homework question. ALWAYS handoff to another agent.",
    ), id="triage_agent")

async def main() -> None:
    # Create the executors
    openai_client = get_azopenaichatclient()
    triage_agent = create_triage_agent(openai_client)
    math_tutor = create_math_tutor(openai_client)
    history_tutor = create_history_tutor(openai_client)

    # Build the workflow
    # There is NO handoff edge for Python at the moment (only for C#)

# Run the main function
if __name__ == "__main__":
    asyncio.run(main())
