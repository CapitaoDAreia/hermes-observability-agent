from langgraph.graph import StateGraph, END
from app.state import AgentState
from app.nodes import (
    fetch_context_node,
    route_after_fetch,
    analyze_error_node,
    error_handler_node
)

workflow = StateGraph(AgentState)

workflow.add_node("fetcher", fetch_context_node)
workflow.add_node("analyzer", analyze_error_node)
workflow.add_node("error_handler", error_handler_node)

workflow.set_entry_point("fetcher")

workflow.add_conditional_edges(
    "fetcher",
    route_after_fetch,
    {
        "analyzer": "analyzer",
        "error_handler": "error_handler"
    }
)

workflow.add_edge("analyzer", END)
workflow.add_edge("error_handler", END)

app_graph = workflow.compile()