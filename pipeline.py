from langgraph.graph import StateGraph, END
from state.schema import PipelineState
from agents.intent_parser import parse_intent
from agents.image_analyser import analyse_images
from agents.storyboard_writer import write_storyboard
from agents.script_generator import generate_script
from agents.compiler_fixer import compile_and_fix
from agents.renderer import render_video


def should_retry_or_fail(state: PipelineState) -> str:
    # If compilation succeeded
    if state.get("final_video_path") == "__READY__":
        return "renderer"
    # If we have a final video path (rendered)
    if state.get("final_video_path") and state.get("final_video_path") != "__READY__":
        return "renderer"
    # If failure report set
    if state.get("failure_report"):
        return "fail"
    # If max retries exceeded
    if state["retry_count"] >= state["max_retries"]:
        return "fail"
    # Otherwise retry
    return "script_generator"


def build_graph() -> StateGraph:
    graph = StateGraph(PipelineState)

    graph.add_node("intent_parser",     parse_intent)
    graph.add_node("image_analyser",    analyse_images)
    graph.add_node("storyboard_writer", write_storyboard)
    graph.add_node("script_generator",  generate_script)
    graph.add_node("compiler_fixer",    compile_and_fix)
    graph.add_node("renderer",          render_video)

    graph.set_entry_point("intent_parser")
    graph.add_edge("intent_parser",     "image_analyser")
    graph.add_edge("image_analyser",    "storyboard_writer")
    graph.add_edge("storyboard_writer", "script_generator")
    graph.add_edge("script_generator",  "compiler_fixer")

    graph.add_conditional_edges(
        "compiler_fixer",
        should_retry_or_fail,
        {
            "renderer":         "renderer",
            "script_generator": "script_generator",
            "fail":             END,
        },
    )
    graph.add_edge("renderer", END)

    return graph.compile()
