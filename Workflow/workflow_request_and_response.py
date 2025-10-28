# pip install agent-framework-core
# pip install azure-identity
# pip install pydantic

import asyncio
from agent_utilities import generate_workflow_visualization
from agent_client_factory import get_azopenaichatclient
from dataclasses import dataclass
from pydantic import BaseModel

from agent_framework import (
    AgentExecutor,
    AgentExecutorRequest,
    AgentExecutorResponse,
    ChatMessage,
    Executor,
    RequestInfoEvent,
    RequestInfoExecutor,
    RequestInfoMessage,
    RequestResponse,
    Role,
    Workflow,
    WorkflowBuilder,
    WorkflowContext,
    WorkflowOutputEvent,
    handler,
)

# Define request message for human feedback
@dataclass
class HumanFeedbackRequest(RequestInfoMessage):
    """Request message for human feedback in the guessing game."""
    prompt: str = ""
    guess: int | None = None

# Define structured output model for agent's guess
class GuessOutput(BaseModel):
    """Structured output from the AI agent with response_format enforcement."""
    guess: int

# Main class to manage turns between agent and human
class TurnManager(Executor):
    """Coordinates turns between the AI agent and human player.

    Responsibilities:
    - Start the game by requesting the agent's first guess
    - Process agent responses and request human feedback
    - Handle human feedback and continue the game or finish
    """

    def __init__(self, id: str | None = None):
        super().__init__(id=id or "turn_manager")

    @handler
    async def start(self, _: str, ctx: WorkflowContext[AgentExecutorRequest]) -> None:
        """Start the game by asking the agent for an initial guess."""
        user = ChatMessage(Role.USER, text="Start by making your first guess.")
        await ctx.send_message(AgentExecutorRequest(messages=[user], should_respond=True))

    @handler
    async def on_agent_response(
        self,
        result: AgentExecutorResponse,
        ctx: WorkflowContext[HumanFeedbackRequest],
    ) -> None:
        """Handle the agent's guess and request human guidance."""
        # Parse structured model output (defensive default if agent didn't reply)
        text = result.agent_run_response.text or ""
        last_guess = GuessOutput.model_validate_json(text).guess if text else None

        # Craft a clear human prompt that defines higher/lower relative to agent's guess
        prompt = (
            f"The agent guessed: {last_guess if last_guess is not None else text}. "
            "Type one of: 'higher'/'h'/'high' (your number is higher than this guess), "
            "'lower'/'l'/'low' (your number is lower than this guess), correct, ok, yes, or exit."
        )
        await ctx.send_message(HumanFeedbackRequest(prompt=prompt, guess=last_guess))

    @handler
    async def on_human_feedback(
        self,
        feedback: RequestResponse[RequestInfoMessage, str],
        ctx: WorkflowContext[AgentExecutorRequest, str],
    ) -> None:
        """Continue the game or finish based on human feedback."""
        reply = (feedback.data or "").strip().lower()
        # Use the correlated request's guess to avoid extra state reads
        last_guess = getattr(feedback.original_request, "guess", None)

        if reply.lower() in ("correct", "ok", "yes"):
            await ctx.yield_output(f"Guessed correctly: {last_guess}")
            return

        # Provide feedback to the agent for the next guess
        user_msg = ChatMessage(
            Role.USER,
            text=f'Feedback: {reply}. Return ONLY a JSON object matching the schema {{"guess": <int 1..10>}}.',
        )
        await ctx.send_message(AgentExecutorRequest(messages=[user_msg], should_respond=True))

# Main function to build and run the workflow
async def main() -> None:
    # Create the chat agent with structured output enforcement
    chat_client = get_azopenaichatclient()
    agent = chat_client.create_agent(
        instructions=(
            "You guess a number between 1 and 20. "
            "If the user says 'higher'/'h'/'high' or 'lower'/'l'/'low', adjust your next guess. "
            'You MUST return ONLY a JSON object exactly matching this schema: {"guess": <integer 1..20>}. '
            "No explanations or additional text, just the JSON with the correct schema."
        ),
        response_format=GuessOutput,
    )

    turn_manager = TurnManager(id="turn_manager")
    agent_exec = AgentExecutor(agent=agent, id="agent")
    request_info_executor = RequestInfoExecutor(id="request_info")

    # Build the workflow
    workflow = (
        WorkflowBuilder()
        .set_start_executor(turn_manager)
        .add_edge(turn_manager, agent_exec)
        .add_edge(agent_exec, turn_manager)
        .add_edge(turn_manager, request_info_executor)
        .add_edge(request_info_executor, turn_manager)
        .build()
    )
    generate_workflow_visualization(workflow, name="diagrams/workflow_request_and_response")

    print("🎯 Number Guessing Game")
    print("Think of a number between 1 and 20, and I'll try to guess it!")
    print("-" * 50)
    input("Presioná Enter para continuar...")
    
    # Run the interactive workflow
    await run_interactive_workflow(workflow)

async def run_interactive_workflow(workflow: Workflow):
    """Run the workflow with human-in-the-loop interaction."""
    pending_responses: dict[str, str] | None = None
    completed = False
    workflow_output: str | None = None

    while not completed:
        # First iteration uses run_stream("start")
        # Subsequent iterations use send_responses_streaming with pending responses
        stream = (
            workflow.send_responses_streaming(pending_responses)
            if pending_responses
            else workflow.run_stream("start")
        )

        # Collect events for this turn
        events = [event async for event in stream]
        pending_responses = None

        # Process events to collect requests and detect completion
        # (request_id, prompt)
        requests: list[tuple[str, str]] = []
        for event in events:
            if isinstance(event, RequestInfoEvent) and isinstance(event.data, HumanFeedbackRequest):
                # RequestInfoEvent for our HumanFeedbackRequest
                requests.append((event.request_id, event.data.prompt))
            elif isinstance(event, WorkflowOutputEvent):
                # Capture workflow output when yielded
                workflow_output = str(event.data)
                completed = True

        if requests and not completed:
            responses: dict[str, str] = {}
            for req_id, prompt in requests:
                print(f"\n🤖 {prompt}")
                answer = input("👤 Enter your answer: ").lower()

                if answer == "exit":
                    print("👋 Exiting...")
                    return
                responses[req_id] = answer
            pending_responses = responses

    # Show final result
    print(f"\n🎉 {workflow_output}")

# Run the workflow
if __name__ == "__main__":
    asyncio.run(main())
