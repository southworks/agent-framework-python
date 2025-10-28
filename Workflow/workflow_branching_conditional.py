# Workflow to demonstrate branching using conditional edges based on spam detection results.
import asyncio
from agent_utilities import generate_workflow_visualization, get_input_text
from agent_client_factory import get_azopenaichatclient
from pathlib import Path
from typing import Any
from typing_extensions import Never

from agent_framework import (
    AgentExecutor,
    AgentExecutorRequest,
    AgentExecutorResponse,
    ChatMessage,
    Role,
    WorkflowBuilder,
    WorkflowContext,
    executor
)
from pydantic import BaseModel

class DetectionResult(BaseModel):
    """Represents the result of spam detection."""
    is_spam: bool
    reason: str
    email_content: str

class EmailResponse(BaseModel):
    """Represents the response from the email assistant."""
    response: str

def get_condition(expected_result: bool):
    """Create a condition callable that routes based on DetectionResult.is_spam."""
    # The returned function will be used as an edge predicate.
    def condition(message: Any) -> bool:
        # Defensive guard. If a non AgentExecutorResponse appears, let the edge pass to avoid dead ends.
        if not isinstance(message, AgentExecutorResponse):
            return True

        try:
            # Prefer parsing a structured DetectionResult from the agent JSON text.
            # Using model_validate_json ensures type safety and raises if the shape is wrong.
            detection = DetectionResult.model_validate_json(message.agent_run_response.text)
            # Route only when the spam flag matches the expected path.
            return detection.is_spam == expected_result
        except Exception:
            # Fail closed on parse errors so we do not accidentally route to the wrong path.
            # Returning False prevents this edge from activating.
            return False

    return condition

@executor(id="send_email")
async def handle_email_response(response: AgentExecutorResponse, ctx: WorkflowContext[Never, str]) -> None:
    """Handle legitimate emails by drafting a professional response."""
    # Downstream of the email assistant. Parse a validated EmailResponse and yield the workflow output.
    email_response = EmailResponse.model_validate_json(response.agent_run_response.text)
    await ctx.yield_output(f"Email sent:\n{email_response.response}")


@executor(id="handle_spam")
async def handle_spam_classifier_response(response: AgentExecutorResponse, ctx: WorkflowContext[Never, str]) -> None:
    """Handle spam emails by marking them appropriately."""
    # Spam path. Confirm the DetectionResult and yield the workflow output. Guard against accidental non spam input.
    detection = DetectionResult.model_validate_json(response.agent_run_response.text)
    if detection.is_spam:
        await ctx.yield_output(f"Email marked as spam:\n{detection.reason}")
    else:
        # This indicates the routing predicate and executor contract are out of sync.
        raise RuntimeError("This executor should only handle spam messages.")

@executor(id="to_email_assistant_request")
async def to_email_assistant_request(
    response: AgentExecutorResponse, ctx: WorkflowContext[AgentExecutorRequest]
) -> None:
    """Transform spam detection response into a request for the email assistant."""
    detection = DetectionResult.model_validate_json(response.agent_run_response.text)

    # Create a new request for the email assistant with the original email content
    request = AgentExecutorRequest(
        messages=[ChatMessage(Role.USER, text=detection.email_content)],
        should_respond=True
    )
    await ctx.send_message(request)

async def get_email_sample() -> str:
    """Get email sample from user input."""
    print("\n".join([
        "Please select the email sample to process. the options are:",
        "1. Legitimate email",
        "2. Spam email",
    ]))

    options = {
        "1": "email.txt",
        "2": "spam.txt",
    }

    option = (await get_input_text("Select an option (1-2): ")).strip()
    if option not in options:
        raise ValueError("Invalid option selected.")

    email_path = Path(__file__).parent / "mail" / options[option]
    return email_path.read_text(encoding="utf-8", errors="replace")

# The main function
async def main() -> None:
    email = await get_email_sample()
    chat_client = get_azopenaichatclient()

    # Create the agent for spam detection
    spam_detection_agent = AgentExecutor(
        chat_client.create_agent(
            instructions=(
                "You are a spam detection assistant that identifies spam emails. "
                "Always return JSON with fields is_spam (bool), reason (string), and email_content (string). "
                "Include the original email content in email_content."
            ),
            response_format=DetectionResult,
        ),
        id="spam_detection_agent",
    )

    # Create the agent for email assistance
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

    # Build the workflow 
    workflow = (
        WorkflowBuilder()
        .set_start_executor(spam_detection_agent)
        
        # This path handles legitimate emails: spam detection (IS NOT SPAM) -> to email assistant -> email assistant -> handle response
        .add_edge(spam_detection_agent, to_email_assistant_request, condition=get_condition(False))
        .add_edge(to_email_assistant_request, email_assistant_agent)
        .add_edge(email_assistant_agent, handle_email_response)
        
        # This path handles spam: spam detection (IS SPAM) -> handle spam
        .add_edge(spam_detection_agent, handle_spam_classifier_response, condition=get_condition(True))
        .build()
    )
    generate_workflow_visualization(workflow, name="diagrams/workflow_branching_conditional")
    
    # Since the start executor is an AgentExecutor, we need to send an AgentExecutorRequest object.
    request = AgentExecutorRequest(messages=[ChatMessage(Role.USER, text=email)], should_respond=True)
    events = await workflow.run(request)
    outputs = events.get_outputs()
    if outputs:
        print(f"Workflow output: {outputs[0]}")

# Run the main function
if __name__ == "__main__":
    asyncio.run(main())
