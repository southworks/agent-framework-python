# Workflow to demonstrate branching using multi-selection based on spam detection results.
import asyncio
from agent_utilities import generate_workflow_visualization, get_input_text
from agent_client_factory import get_azopenaichatclient
from pathlib import Path
from typing import Any, Literal
from typing_extensions import Never

from agent_framework import (
    AgentExecutor,
    AgentExecutorRequest,
    AgentExecutorResponse,
    Case,
    ChatMessage,
    Default,
    Role,
    WorkflowBuilder,
    WorkflowContext,
    executor
)
from pydantic import BaseModel

class DetectionResult(BaseModel):
    """Represents the result of spam detection."""
    spam_decision: str
    reason: str
    email_content: str

class DetectionResultAgent(BaseModel):
    """Structured output returned by the spam detection agent."""
    spam_decision: Literal["NotSpam", "Spam", "Uncertain"]
    reason: str

class EmailResponse(BaseModel):
    """Represents the response from the email assistant."""
    response: str


@executor(id="to_detection_result")
async def to_detection_result(response: AgentExecutorResponse, ctx: WorkflowContext[DetectionResult]) -> None:
    parsed = DetectionResultAgent.model_validate_json(response.agent_run_response.text)
    email_content = response.full_conversation[0].text
    await ctx.send_message(DetectionResult(spam_decision=parsed.spam_decision, reason=parsed.reason, email_content=email_content))

@executor(id="send_email")
async def handle_email_response(response: AgentExecutorResponse, ctx: WorkflowContext[Never, str]) -> None:
    """Handle legitimate emails by drafting a professional response."""
    email_response = EmailResponse.model_validate_json(response.agent_run_response.text)
    await ctx.yield_output(f"Email sent:\n{email_response.response}")

@executor(id="handle_spam")
async def handle_spam_classifier_response(response: DetectionResult, ctx: WorkflowContext[Never, str]) -> None:
    """Handle spam emails by marking them appropriately."""
    if response.spam_decision == "Spam":
        await ctx.yield_output(f"Email marked as spam:\n{response.reason}")
    else:
        raise RuntimeError("This executor should only handle spam messages.")

@executor(id="handle_uncertain")
async def handle_uncertain(detection: DetectionResult, ctx: WorkflowContext[Never, str]) -> None:
    """Handle uncertain emails by marking them appropriately."""
    if detection.spam_decision == "Uncertain":
        await ctx.yield_output(f"Email marked as uncertain: {detection.reason}. Content:\n{detection.email_content}")
    else:
        raise RuntimeError("This executor should only handle Uncertain messages.")


@executor(id="to_email_assistant_request")
async def to_email_assistant_request(
    response: DetectionResult, ctx: WorkflowContext[AgentExecutorRequest]
) -> None:
    """Transform spam detection response into a request for the email assistant."""
    
    # Create a new request for the email assistant with the original email content
    request = AgentExecutorRequest(
        messages=[ChatMessage(Role.USER, text=response.email_content)],
        should_respond=True
    )
    await ctx.send_message(request)


async def get_email_sample() -> str:
    """Get email sample from user input."""
    print("\n".join([
        "Please select the email sample to process. the options are:",
        "1. Legitimate email",
        "2. Spam email",
        "3. Ambiguous email"
    ]))

    options = {
        "1": "email.txt",
        "2": "spam.txt",
        "3": "ambiguous_email.txt",
    }

    option = (await get_input_text("Select an option (1-3): ")).strip()
    if option not in options:
        raise ValueError("Invalid option selected.")

    email_path = Path(__file__).parent / "mail" / options[option]
    return email_path.read_text(encoding="utf-8", errors="replace")


def get_case(expected_decision: str):
    """Factory that returns a predicate matching a specific spam_decision value."""

    def condition(message: Any) -> bool:
        # Only match when the upstream payload is a DetectionResult with the expected decision.
        return isinstance(message, DetectionResult) and message.spam_decision == expected_decision

    return condition


# The main function
async def main() -> None:
    email = await get_email_sample()
    chat_client = get_azopenaichatclient()

    spam_detection_agent = AgentExecutor(
        chat_client.create_agent(
            instructions=(
                "You are a spam detection assistant that identifies spam emails. "
                "Be less confident in your assessments. "
                "Always return JSON with fields 'spam_decision' (one of NotSpam, Spam, Uncertain) "
                "and 'reason' (string)."
            ),
            response_format=DetectionResultAgent,
        ),
        id="spam_detection_agent",
    )

    email_assistant_agent = AgentExecutor(
        chat_client.create_agent(
            instructions=(
                "You are an email assistant that helps users draft professional responses to emails. "
                "Your input might be a JSON object that includes 'email_content'; base your reply on that content. "
                "Return JSON with a single field 'response' containing the drafted reply."
            ),
            response_format=EmailResponse,
        ),
        id="email_assistant_agent",
    )

    # Build workflow: spam_detection_agent -> to_detection_result -> switch (NotSpam or Spam or Default).
    workflow = (
        WorkflowBuilder()
        .set_start_executor(spam_detection_agent)
        .add_edge(spam_detection_agent, to_detection_result)
        .add_multi_selection_edge_group(
            to_detection_result,
            # TODO
            # [
            #     Case(condition=get_case("NotSpam"), target=to_email_assistant_request),
            #     Case(condition=get_case("Spam"), target=handle_spam_classifier_response),
            #     Case(condition=get_case("Uncertain"), target=handle_uncertain),
            # ],
        )
        .add_switch_case_edge_group(
            to_detection_result,
            [
                Case(condition=get_case("NotSpam"), target=to_email_assistant_request),
                Case(condition=get_case("Spam"), target=handle_spam_classifier_response),
                Default(target=handle_uncertain),
            ],
        )
        .add_edge(to_email_assistant_request, email_assistant_agent)
        .add_edge(email_assistant_agent, handle_email_response)
        .build()
    )
    generate_workflow_visualization(workflow, name="diagrams/workflow_branching_switch_case")

    # Since the start executor is an AgentExecutor, we need to send an AgentExecutorRequest object.
    request = AgentExecutorRequest(messages=[ChatMessage(Role.USER, text=email)], should_respond=True)
    events = await workflow.run(request)
    outputs = events.get_outputs()
    if outputs:
        print(f"Workflow output: {outputs[0]}")

# Run the main function
if __name__ == "__main__":
    asyncio.run(main())
