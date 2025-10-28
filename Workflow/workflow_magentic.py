import asyncio
import logging
from typing import cast

from agent_framework import (
    ChatAgent,
    HostedCodeInterpreterTool,
    MagenticAgentDeltaEvent,
    MagenticAgentMessageEvent,
    MagenticBuilder,
    MagenticCallbackEvent,
    MagenticCallbackMode,
    MagenticFinalResultEvent,
    MagenticOrchestratorMessageEvent,
    MagenticPlanReviewDecision,
    MagenticPlanReviewReply,
    MagenticPlanReviewRequest,
    RequestInfoEvent,
    WorkflowRunState,
)
from agent_utilities import generate_workflow_visualization
from agent_client_factory import get_azopenaichatclient, get_azopenairesponsesclient

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Standard_NC6s_v3. The NCv3-series will be retired on September 30, 2025
# https://learn.microsoft.com/en-us/azure/virtual-machines/ncv3-retirement
# NCads H100 v5-series
# https://learn.microsoft.com/en-us/azure/virtual-machines/ncads-h100-v5?source=recommendations
INITIAL_PROMPT = (
    "I am preparing a report on the energy efficiency of different machine learning model architectures. "
    "Compare the estimated training and inference energy consumption of GPT-3 and GPT-5."
    "Then, estimate the CO2 emissions associated with each, assuming training on an Azure Standard_NC40ads_H100_v5 "
    "VM for 24 hours. Provide tables for clarity, and recommend the most energy-efficient model "
    "per task type (image classification, text classification, and text generation)."
)

async def on_event(event: MagenticCallbackEvent) -> None:
    if isinstance(event, MagenticOrchestratorMessageEvent):
        # Manager's planning and coordination messages
        print(f"\n[ORCH:{event.kind}]\n\n{getattr(event.message, 'text', '')}\n{'-' * 26}")

    elif isinstance(event, MagenticAgentDeltaEvent):
        # Streaming tokens from agents
        print(event.text, end="", flush=True)

    elif isinstance(event, MagenticAgentMessageEvent):
        # Complete agent responses
        msg = event.message
        if msg is not None:
            response_text = (msg.text or "").replace("\n", " ")
            print(f"\n[AGENT:{event.agent_id}] {msg.role.value}\n\n{response_text}\n{'-' * 26}")

    elif isinstance(event, MagenticFinalResultEvent):
        # Final synthesized result
        print("\n" + "=" * 50)
        print("FINAL RESULT:")
        print("=" * 50)
        if event.message is not None:
            print(event.message.text)
        print("=" * 50)

async def main() -> None:
    researcher_agent = ChatAgent(
        name="ResearcherAgent",
        description="Specialist in research and information gathering",
        instructions="You are a Researcher. You find information without additional computation or quantitative analysis.",
        chat_client=get_azopenaichatclient(),
    )

    coder_agent = ChatAgent(
        name="CoderAgent",
        description="A helpful assistant that writes and executes code to process and analyze data.",
        instructions="You solve questions using code. Please provide detailed analysis and computation process.",
        chat_client=get_azopenairesponsesclient(),
        tools=HostedCodeInterpreterTool(),
    )

    print("\nBuilding Magentic Workflow...")

    # TODO: Create a custom StandardMagenticManager

    workflow = (
        MagenticBuilder()
        .participants(researcher=researcher_agent, coder=coder_agent)
        .on_event(on_event, mode=MagenticCallbackMode.STREAMING)
        .with_standard_manager(
            chat_client=get_azopenaichatclient(),
            max_round_count=5,
            max_stall_count=2,
            max_reset_count=1,
        )
        .with_plan_review()
        .build()
    )
    generate_workflow_visualization(workflow, name="diagrams/workflow_magentic")

    completion_event: WorkflowRunState | None = None
    pending_request: RequestInfoEvent | None = None

    print("\nStarting workflow execution...")
    while True:
        if pending_request is None:
            try:
                async for event in workflow.run_stream(INITIAL_PROMPT):
                    if isinstance(event, WorkflowRunState) and event == WorkflowRunState.IDLE_WITH_PENDING_REQUESTS:
                        completion_event = event
                    if isinstance(event, RequestInfoEvent) and event.request_type is MagenticPlanReviewRequest:
                        pending_request = event
                        review_req = cast(MagenticPlanReviewRequest, event.data)
                        if review_req.plan_text:
                            print(f"\n=== PLAN REVIEW REQUEST ===\n")
                            print(review_req.plan_text)
                            print("\n===========================\n")
            except Exception as e:
                print(f"Workflow execution failed: {e}")

        # Check if completed
        if completion_event is not None:
            break

        if pending_request is not None:
            print(f"\n=== PLAN REVIEW RESPONSE ===\n")
            print("TODO: Add a human approval step here. Auto-approving the plan...")
            reply = MagenticPlanReviewReply(decision=MagenticPlanReviewDecision.APPROVE)

            async for event in workflow.send_responses_streaming({pending_request.request_id: reply}):
                if isinstance(event, WorkflowRunState) and event == WorkflowRunState.IDLE_WITH_PENDING_REQUESTS:
                    completion_event = event
                elif isinstance(event, RequestInfoEvent):
                    # Another review cycle if needed
                    pending_request = event
                else:
                    pending_request = None

if __name__ == "__main__":
    asyncio.run(main())
