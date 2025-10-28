Agent Framework Samples

This repository contains small, focused samples that demonstrate how to build agents and workflows using Agent Framework. The examples cover sequential and concurrent workflows, branching and switching, human-in-the-loop interactions, visualization, multi-agent orchestration (Magentic), and basic agent patterns.

Prerequisites

- Python 3.11+ recommended
- Create and activate a virtual environment
  - Windows PowerShell: `python -m venv .venv && .venv\\Scripts\\Activate.ps1`
  - bash/zsh: `python -m venv .venv && source .venv/bin/activate`
- Install dependencies (typical):
  - `pip install agent-framework-core azure-identity pydantic aioconsole httpx`
  - For A2A sample: `pip install a2a-client` (or the appropriate package providing `a2a.client`)
- Azure credentials for Azure OpenAI clients used by the samples
  - Install Azure CLI and sign in: `az login`
  - Samples use `AzureCliCredential()` or `DefaultAzureCredential()`
- Optional: OPENAI-style API key if using the OpenAI clients in `Agent/`
  - Set `OPENAI_API_KEY` if needed

Configuration

- Update endpoints and deployments in `Workflow/agent_client_factory.py` and `Agent/agent_client_factory.py` to match your Azure OpenAI resource, project endpoint, and deployment names.
- Some samples generate diagrams into `Workflow/diagrams/`. Ensure the folder exists (it is included) and that graphviz or required tooling is available via `agent_framework` if exporting to PNG/PDF.

How to Run

- From the repo root, with your virtual environment active: `python <path-to-script>.py`
- Most scripts run standalone and print results to the console. Some prompt for input.

Agent Samples

- `Agent/agent_minimal.py` — Minimal agent that responds to a simple prompt.
- `Agent/agent_basic.py` — Agent with text and image content, shows both streaming and non‑streaming calls.
- `Agent/agent_to_agent.py` — Agent2Agent (A2A) protocol integration. Requires an external A2A‑compliant agent and `A2A_AGENT_HOST` env var.
- `Agent/agent_tools.py` — ChatAgent using tools: Microsoft Learn MCP + Web Search to gather up‑to‑date info (requires network access).
- `Agent/agent_observability.py` — Minimal agent with observability enabled via `setup_observability` (uses OpenTelemetry under the hood).
- `Agent/agent_multi_threads.py` — Demonstrates multiple concurrent conversation threads on a single agent instance.
- `Agent/agent_middleware.py` — Shows function middleware logging with a simple tool (`get_time`).

Workflow Samples

- `Workflow/workflow_sequential.py` — Sequential workflow of simple executors that transform text (uppercase -> uppercase -> reverse) and yield final output.
- `Workflow/workflow_concurrent.py` — Fan‑out/fan‑in numeric example computing count, sum, and average concurrently, then aggregating outputs.
- `Workflow/workflow_agents.py` — Simple two‑agent chain: Writer -> Reviewer. Generates a diagram in `Workflow/diagrams/workflow_agents.svg`.
- `Workflow/workflow_visualization.py` — Fan‑out/fan‑in with three agent executors (research/marketing/legal). Demonstrates visualization to SVG, Mermaid, and Digraph.
- `Workflow/workflow_request_and_response.py` — Human‑in‑the‑loop “number guessing” game using `RequestInfoExecutor`. Streams turns and waits for your input.
- `Workflow/workflow_branching_conditional.py` — Conditional branching based on a spam detection agent’s JSON output; routes to email drafting or spam handling. Reads samples from `Workflow/mail/`.
- `Workflow/workflow_branching_switch_case.py` — Switch‑case branching with three outcomes: NotSpam, Spam, Default (Uncertain). Chains to email assistant for legitimate emails.
- `Workflow/workflow_branching_multi_selection.py` — Shows `add_multi_selection_edge_group` placeholder (TODO) plus active switch‑case flow as above.
- `Workflow/workflow_magentic.py` — Magentic multi‑agent orchestration (researcher + code interpreter). Streams planning, agent messages, and a final synthesized result. Auto‑approves plan review.
- `Workflow/world_cup_2026.py` — Multi‑expert analysis and aggregation workflow for World Cup 2026 favorites. Includes a simple user‑prediction manager and streaming synthesis.
- `Workflow/workflow_handoff.py` — WIP handoff/triage pattern (triage agent to domain tutors). This file contains placeholder code and unresolved references; treat as in‑progress.
- `Workflow/workflow_checkpoints.py` — Demonstrates checkpointing: run until a human approval is requested, list checkpoints, and resume from the latest checkpoint by supplying the pending response.

Diagrams and Utilities

- `Workflow/agent_utilities.py` —
  - `generate_workflow_visualization(workflow, type, name)` saves/export diagrams (SVG/PNG/PDF) or prints Mermaid/Digraph.
  - `get_input_text()` reads from stdin, CLI args, or interactive prompt.
- Diagrams are saved under `Workflow/diagrams/` (e.g., `workflow_branching_conditional.svg`).

Email Samples

- `Workflow/mail/` contains `email.txt`, `spam.txt`, and `ambiguous_email.txt` used by the branching samples.

Environment Notes

- Azure
  - Ensure `az login` has been run and your subscription has access to the configured Azure OpenAI resource.
  - Edit endpoints and deployment names in `agent_client_factory.py` files as needed.
- OpenAI‑style API
  - If you switch to the OpenAI client variants, set `OPENAI_API_KEY` and adjust base URLs accordingly.
- A2A Sample
  - Set `A2A_AGENT_HOST` to an A2A‑compliant agent URL and ensure `/.well-known/agent.json` is available.

Quick Start Commands

- Sequential: `python Workflow/workflow_sequential.py`
- Concurrent: `python Workflow/workflow_concurrent.py`
- Agents chain: `python Workflow/workflow_agents.py`
- Visualization: `python Workflow/workflow_visualization.py`
- Human‑in‑loop: `python Workflow/workflow_request_and_response.py`
- Branching (conditional): `python Workflow/workflow_branching_conditional.py`
- Switch‑case: `python Workflow/workflow_branching_switch_case.py`
- Checkpoints: `python Workflow/workflow_checkpoints.py`
- Magentic: `python Workflow/workflow_magentic.py`
- World Cup: `python Workflow/world_cup_2026.py`
- Agent basics: `python Agent/agent_basic.py` or `python Agent/agent_minimal.py`
- Agent tools: `python Agent/agent_tools.py`
- Agent observability: `python Agent/agent_observability.py`
- Agent multi‑threads: `python Agent/agent_multi_threads.py`
- Agent middleware: `python Agent/agent_middleware.py`
- A2A: `python Agent/agent_to_agent.py` (with `A2A_AGENT_HOST` set)

Troubleshooting

- Import errors for agent_framework or Azure clients: verify `agent-framework-core` and `azure-identity` are installed and your Python interpreter matches the virtual environment.
- Credential issues: run `az login` again or switch to `DefaultAzureCredential` with proper environment variables.
- Diagram export errors: some formats may require Graphviz or OS packages; try SVG first or install Graphviz.
- Endpoint/Deployment errors: update `Workflow/agent_client_factory.py` to match your Azure OpenAI resource configuration.
