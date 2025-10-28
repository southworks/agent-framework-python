# This example demonstrates a visualization of fan-out/fan-in workflow
import asyncio

from dataclasses import dataclass
from agent_framework import (
    AgentExecutor,
    AgentExecutorRequest,
    AgentExecutorResponse,
    ChatMessage,
    Executor,
    Role,
    WorkflowBuilder,
    WorkflowContext,
    handler,
)
from typing_extensions import Never
from agent_client_factory import get_azopenaichatclient
from agent_utilities import WorkflowVisualizationType, generate_workflow_visualization

# Define a dataclass to hold aggregated insights
@dataclass
class AggregatedInsights:
    """Structured output from the aggregator."""
    research: str
    marketing: str
    legal: str

# Executor to dispatch prompts to expert agents
class DispatchToExperts(Executor):
    """Dispatches the incoming prompt to all expert agent executors (fan-out)."""

    @handler
    async def dispatch(self, prompt: str, ctx: WorkflowContext[AgentExecutorRequest]) -> None:
        initial_message = ChatMessage(Role.USER, text=prompt)
        for expert_id in self._expert_ids:
            await ctx.send_message(
                AgentExecutorRequest(messages=[initial_message], should_respond=True),
                target_id=expert_id,
            )

# Executor to aggregate responses from expert agents
class AggregateInsights(Executor):
    """Aggregates expert agent responses into a single consolidated result (fan-in)."""

    @handler
    async def aggregate(self, results: list[AgentExecutorResponse], ctx: WorkflowContext[Never, str]) -> None:
        by_id: dict[str, str] = {}
        for r in results:
            by_id[r.executor_id] = r.agent_run_response.text

        research_text = by_id.get("researcher", "")
        marketing_text = by_id.get("marketer", "")
        legal_text = by_id.get("legal", "")

        aggregated = AggregatedInsights(
            research=research_text,
            marketing=marketing_text,
            legal=legal_text,
        )

        # Provide a readable, consolidated string as the final workflow result.
        consolidated = (
            "Consolidated Insights\n"
            "====================\n\n"
            f"Research Findings:\n{aggregated.research}\n\n"
            f"Marketing Angle:\n{aggregated.marketing}\n\n"
            f"Legal/Compliance Notes:\n{aggregated.legal}\n"
        )

        await ctx.yield_output(consolidated)

# Main function to build and visualize the workflow
async def main() -> None:
    # Create agent executors for domain experts
    chat_client = get_azopenaichatclient()

    researcher = AgentExecutor(
        chat_client.create_agent(
            instructions=(
                "You're an expert market and product researcher. Given a prompt, provide concise, factual insights,"
                " opportunities, and risks."
            ),
        ),
        id="researcher",
    )
    marketer = AgentExecutor(
        chat_client.create_agent(
            instructions=(
                "You're a creative marketing strategist. Craft compelling value propositions and target messaging"
                " aligned to the prompt."
            ),
        ),
        id="marketer",
    )
    legal = AgentExecutor(
        chat_client.create_agent(
            instructions=(
                "You're a cautious legal/compliance reviewer. Highlight constraints, disclaimers, and policy concerns"
                " based on the prompt."
            ),
        ),
        id="legal",
    )

    expert_ids = [researcher.id, marketer.id, legal.id]

    dispatcher = DispatchToExperts(expert_ids=expert_ids, id="dispatcher")
    aggregator = AggregateInsights(expert_ids=expert_ids, id="aggregator")

    # Build a simple fan-out/fan-in workflow
    workflow = (
        WorkflowBuilder()
        .set_start_executor(dispatcher)
        .add_fan_out_edges(dispatcher, [researcher, marketer, legal])
        .add_fan_in_edges([researcher, marketer, legal], aggregator)
        .build()
    )

    # Generate workflow visualization
    print("Generating workflow visualization...")
    generate_workflow_visualization(workflow, name="diagrams/workflow_visualization")
    generate_workflow_visualization(workflow, type=WorkflowVisualizationType.MERMAID)
    generate_workflow_visualization(workflow, type=WorkflowVisualizationType.DIGRAPH)

# Run the workflow
if __name__ == "__main__":
    asyncio.run(main())
