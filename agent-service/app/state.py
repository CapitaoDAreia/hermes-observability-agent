from typing import Annotated, TypedDict, List, Dict
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    alert_payload: Dict

    app_name: str

    context_data: List[str]

    analysis_report: str

    messages: Annotated[list, add_messages]