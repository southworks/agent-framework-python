import asyncio
from dataclasses import dataclass
from agent_framework import (
    AgentExecutor,
    AgentExecutorResponse,
    AgentRunEvent,
    AgentRunResponse,
    AgentRunUpdateEvent,
    ChatMessage, 
    Executor,
    RequestInfoEvent,
    RequestInfoExecutor,
    RequestInfoMessage,
    RequestResponse,
    Role,
    WorkflowBuilder, 
    WorkflowContext,
    handler
)
from agent_utilities import generate_workflow_visualization
from agent_client_factory import get_azopenaichatclient

EXPERT_INSTRUCTIONS = """
    Purpose

    You are an agent specializes in soccer capable of analyzing teams, players, and tournaments with a data-driven and realistic perspective. Its primary goal is to evaluate probabilities, rankings, and predictions related to the FIFA World Cup 2026 and other major competitions.
    Provide data-driven, unbiased, and verifiable football insights.

    Behavioral Directives

    1. Analytical focus:
    Always reason from data, team performance metrics, and tactical context.
    Use verifiable statistics or public data (FIFA, UEFA, CONMEBOL, Opta, etc.) when available.

    2. No bias or emotion:
    Avoid fan language, opinions, or emotional phrasing.
    Maintain an objective, professional tone suitable for expert briefings or reports.

    3. Structured responses:
    Provide brief justifications (1–2 sentences per item).
    Conclude with factors that could modify the result (e.g., injuries, form, coaching).
    Use Markdown or table formatting if supported.

    4. Transparency and uncertainty:
    If information is incomplete or outdated, explicitly state this and avoid speculation.

    5. Language style:
    Clear, formal English similar to sports analytics reports.
    Sentences should be declarative and concise.
"""

AGGREGATOR_INSTRUCTIONS = """
    You are a football analysis meta-expert specializing in synthesizing multiple expert opinions into a single, coherent consensus.
    Your behavior should be:
    - Analytical and impartial — evaluate reasoning quality and consistency over personal bias.
    - Evidence-oriented — value arguments backed by data or clear logic.
    - Concise and structured — express insights in a clear, ordered, and professional tone.
    - Specialized in football analysis — demonstrate familiarity with player form, tactics, historical performance, and statistical reasoning when relevant.
    - Your goal is to merge the insights of multiple analysts into the most balanced and justified final ranking.
"""

MY_PREDICTION = """
    1. Argentina because is Messi papa!
    2. France because is second
    3. España has a young generation coming up strong
"""

ENTRY_PROMPT = """
    You are a soccer analyst. I want you to tell me who you believe are the top three favorites to win the 2026 World Cup.
    Your task is to:
    Analyze recent team performances, FIFA rankings, player generations, and historical strength.
    Produce a ranking from 1 to 3 of the teams with the highest probability of winning, including a short explanation for each.
    Conclude with a brief note on what factors could change this ranking before the tournament.
"""

SUMMARY_PROMPT = """
    Here are the all agent outputs about who are the top three favorites to win the 2026 World Cup:

    Expert number 1:
    {expert_1_prediction}

    Expert number 2:
    {expert_2_prediction}

    Expert number 3:
    {expert_3_prediction}

    My own prediction:
    {my_prediction}

    Compare their analyses and produce your synthesis following this structure:
    1. Consensus / Agreements
    2. Key Divergences
    3. Agent Evaluation (reasoning quality, consistency, use of evidence)
    4. Caveats / Uncertainties
    5. Final Aggregated Ranking (1 to 3)
"""

@dataclass
class HumanFeedbackRequest(RequestInfoMessage):
    """Request message for human feedback."""
    new_prediction: str = ""


class Dispatcher(Executor):
    """The purpose of this executor is to dispatch the input of the workflow to other executors."""

    @handler
    async def handle(self, input: str, ctx: WorkflowContext[str]):
        await ctx.set_shared_state("shared_file_id", MY_PREDICTION)
        await ctx.send_message(input)


class Aggregator(Executor):
    """The aggregator."""

    @handler
    async def handle(self, input: list[AgentExecutorResponse], ctx: WorkflowContext[str]):
        # for response in input:
        #     print(f"Received prediction from {response.executor_id}:")
        #     print(response.agent_run_response.text)
        
        aggregated_prompt = SUMMARY_PROMPT.format(
            expert_1_prediction=input[0].agent_run_response.text,
            expert_2_prediction=input[1].agent_run_response.text,
            expert_3_prediction=input[2].agent_run_response.text,
            my_prediction=await ctx.get_shared_state("shared_file_id")
        )

        await ctx.send_message(aggregated_prompt)


class UserPredictionManager(Executor):
    """Manages user feedback to refine the prediction."""

    # @handler
    # async def start(self, _: str, ctx: WorkflowContext[str]) -> None:
    #     """Start the game by asking the agent for an initial guess."""
    #     await ctx.send_message("This is a dummy message")

    def __init__(self, id: str | None = None):
        super().__init__(id=id or "user_prediction_manager")

    @handler
    async def on_agent_response(
        self,
        result: str,
        ctx: WorkflowContext[HumanFeedbackRequest],
    ) -> None:
        """Handle request human feedback."""
        # Parse structured model output (defensive default if agent didn't reply)
        print(f"This is the input: {result}")
        
        user_prediction = await ctx.get_shared_state("shared_file_id")

        new_prediction = (
            f"The current user prediction is:\n{user_prediction}\n\n"
            "If you would like to provide an updated prediction, please enter it now"
            "Otherwise, just leave the input blank and press Enter."
        )
        await ctx.send_message(HumanFeedbackRequest(new_prediction=new_prediction))

    @handler
    async def on_human_feedback(
        self,
        feedback: RequestResponse[RequestInfoMessage, str],
        ctx: WorkflowContext[AgentExecutorResponse],
    ) -> None:
        """Continue the workflow based on human feedback."""
        reply = (feedback.data or "").strip().lower()
        print(f"User feedback received: {reply}")

        # Use the correlated request's guess to avoid extra state reads
        last_guess = getattr(feedback.original_request, "guess", None)
        print(f"Original request's guess: {last_guess}")

        # user_prediction = feedback.data or last_guess or ""
        user_prediction = await ctx.get_shared_state("shared_file_id")
        msg = ChatMessage(role=Role.USER, text=user_prediction)
        response = AgentRunResponse(messages=[msg])
        result = AgentExecutorResponse(
            executor_id=ctx.executor.id,
            agent_run_response=response,
        )
        await ctx.send_message(result)


def create_expert_recondo(chat_client) -> AgentExecutor:
    return AgentExecutor(chat_client.create_agent(
        name="Gaston_Recondo",
        instructions=EXPERT_INSTRUCTIONS,
        temperature=0,
        top_p=0.8,
    ), id="expert_gaston_recondo")

def create_expert_pagani(chat_client) -> AgentExecutor:
    return AgentExecutor(chat_client.create_agent(
        name="Horacio_Pagani",
        instructions=EXPERT_INSTRUCTIONS,
        temperature=1,
        top_p=0.8,
    ), id="expert_horacio_pagani")

def create_expert_beltran(chat_client) -> AgentExecutor:
    return AgentExecutor(chat_client.create_agent(
        name="Morena_Beltran",
        instructions=EXPERT_INSTRUCTIONS,
        temperature=0.5,
        top_p=0.4,
    ), id="expert_morena_beltran")

def create_expert_vignolo(chat_client) -> AgentExecutor:
    return AgentExecutor(chat_client.create_agent(
        name="Sebastian_Vignolo",
        instructions=AGGREGATOR_INSTRUCTIONS,
        temperature=0.1,
        top_p=0.8,
    ), id="expert_sebastian_vignolo")

async def main() -> None:
    # Create the executors
    dispatcher = Dispatcher(id="dispatcher")
    aggregator = Aggregator(id="aggregator")
    user_prediction_manager = UserPredictionManager(id="user_prediction_manager")
    request_info_executor = RequestInfoExecutor(id="request_info")
    openai_client = get_azopenaichatclient()
    agent_recondo = create_expert_recondo(openai_client)
    agent_pagani = create_expert_pagani(openai_client)
    agent_beltran = create_expert_beltran(openai_client)
    agent_vignolo = create_expert_vignolo(openai_client)

    # Build the workflow
    workflow = (
        WorkflowBuilder()
        .set_start_executor(dispatcher)
        .add_fan_out_edges(dispatcher, [agent_recondo, agent_pagani, agent_beltran, user_prediction_manager])
        .add_edge(user_prediction_manager, request_info_executor)
        .add_edge(request_info_executor, user_prediction_manager)
        .add_fan_in_edges([user_prediction_manager, agent_recondo, agent_pagani, agent_beltran], aggregator)
        .add_edge(aggregator, agent_vignolo)
        .build()
    )
    generate_workflow_visualization(workflow, name="diagrams/world_cup_2026")
    print("This workflow has been created to predict the top 3 favorites to win the 2026 World Cup.")
    input("Press Enter to continue...")

    # Run the workflow
    EXECUTE_WITH_STREAMING = True
    pending_responses: dict[str, str] | None = None

    if EXECUTE_WITH_STREAMING:
        async for event in workflow.run_stream(ENTRY_PROMPT):
            if isinstance(event, RequestInfoEvent):
                print()
                print(f"Request info event!: {event}")
                workflow.send_responses_streaming(pending_responses)
                print()
            elif not isinstance(event, AgentRunUpdateEvent):
                print(f"Event: {event}")
            elif event.executor_id == agent_vignolo.id:
                print(event.data, end="", flush=True)
    else:
        for event in await workflow.run(ENTRY_PROMPT):
            if not isinstance(event, AgentRunEvent):
                print(f"Event: {event}")
            elif isinstance(event, AgentRunEvent) and event.executor_id == agent_vignolo.id:
                print("Result of the workflow: \n")
                print(event.data)

if __name__ == "__main__":
    asyncio.run(main())
