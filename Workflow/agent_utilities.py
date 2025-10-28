import sys
from agent_framework import Workflow, WorkflowViz
from aioconsole import ainput
from enum import Enum

class WorkflowVisualizationType(str, Enum):
    SVG = "svg"
    PNG = "png"
    PDF = "pdf"
    MERMAID = "mermaid"
    DIGRAPH = "digraph"


async def get_input_text(console_text="Input text: ") -> str:
    """Get input text from stdin, command line argument, or user prompt."""
    if not sys.stdin.isatty():
        return sys.stdin.read()
    if len(sys.argv) > 1:
        return " ".join(sys.argv[1:])

    return await ainput(console_text)

def generate_workflow_visualization(workflow: Workflow, type=WorkflowVisualizationType.SVG, name="workflow_diagram") -> None:
    """Generate and save workflow visualization in the specified format."""
    try:
        workflowViz = WorkflowViz(workflow)
        match type:
            case WorkflowVisualizationType.SVG:
                svg_file = workflowViz.save_svg(name)
                print(f"SVG file saved to: {svg_file}")
            case WorkflowVisualizationType.PNG:
                png_file = workflowViz.save_png(name)
                print(f"PNG file saved to: {png_file}")
            case WorkflowVisualizationType.PDF:
                pdf_file = workflowViz.save_pdf(name)
                print(f"PDF file saved to: {pdf_file}")
            case WorkflowVisualizationType.MERMAID:
                print(workflowViz.to_mermaid())
            case WorkflowVisualizationType.DIGRAPH:
                print(workflowViz.to_digraph())
            case _:
                print("Invalid visualization type")
    except ImportError as error:
        print(error)