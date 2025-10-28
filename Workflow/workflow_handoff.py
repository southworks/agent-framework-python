
from agent_framework import AgentExecutor, WorkflowBuilder
from agent_client_factory import get_azopenaichatclient

def create_math_tutor(agent) -> AgentExecutor:
    return AgentExecutor(agent.create_agent(
        name="Math_Tutor",
        instructions="You provide help with math problems. Explain your reasoning at each step and include examples. Only respond about math.",
    ), id="math_tutor")

def create_history_tutor(agent) -> AgentExecutor:
    return AgentExecutor(agent.create_agent(
        name="History_Tutor",
        instructions="You provide assistance with historical queries. Explain important events and context clearly. Only respond about history.",
    ), id="history_tutor")

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
    workflow = (
        WorkflowBuilder()
        .set_start_executor(triage_agent)
        .add_agent(triage_agent, [math_tutor, history_tutor])
        .add_fan_in_edges([agent_recondo, agent_pagani, agent_beltran], aggregator)
        .add_edge(aggregator, request_info_executor)
        .add_edge(request_info_executor, agent_vignolo)
        .build()
    )
