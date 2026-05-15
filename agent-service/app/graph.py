import os
import httpx
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from app.state import AgentState
from langgraph.graph import StateGraph, END

def get_model():
    """
    Unified Engine (The Right Way):
    - Local: Ollama
    - Cloud: Gemini through ChatGoogleGenerativeAI (configured for Vertex/ADC)
    """
    provider = os.getenv("LLM_PROVIDER")
    
    if provider == "GEMINI":
        return ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            project=os.getenv("GOOGLE_CLOUD_PROJECT"),
            # location=os.getenv("GCP_LOCATION", "us-central1")
        )
    
    # Fallback local via Ollama
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(
        base_url=os.getenv("OPENAI_API_BASE"),
        api_key="ollama",
        model=os.getenv("LLM_MODEL")
    )

model = get_model()
TELEMETRY_URL = os.getenv("TELEMETRY_SERVICE_URL")

# --- GRAPH NODES ---

async def fetch_context_node(state: AgentState):
    """Fetch logs through REST API."""
    app_name = state["app_name"]
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{TELEMETRY_URL}/logs/{app_name}", timeout=10.0)
            if response.status_code == 200:
                logs_data = response.json().get("logs", [])
                return {"context_data": ["\n".join(logs_data)]}
            return {"context_data": [f"ERROR_HTTP: Status {response.status_code}"]}
    except Exception as e:
        return {"context_data": [f"ERROR_NET: Falha ao conectar na telemetria - {str(e)}"]}

def route_after_fetch(state: AgentState):
    """Flow decision-maker: Protects the LLM from empty contexts or infrastructure errors."""
    logs = state["context_data"][0]
    
    if "ERROR_MCP" in logs or "Nenhum log encontrado" in logs:
        return "error_handler"
    return "analyzer"

def analyze_error_node(state: AgentState):
    """Structured Root Cause Diagnosis."""
    system_prompt = (
        "You are Hermes, Senior SRE Agent. Analyze the logs and identify the root cause.\n"
        "Always respond using structured, technical Markdown focused on immediate action."
    )
    user_content = f"Serviço: {state['app_name']}\nLogs:\n{state['context_data'][0]}"
    
    response = model.invoke([
        SystemMessage(content=system_prompt), 
        HumanMessage(content=user_content)
    ])
    return {"analysis_report": response.content}

def error_handler_node(state: AgentState):
    """Fallback for data unavailability."""
    return {"analysis_report": "❌ **Telemetry Error:** Logs could not be retrieved. Check connectivity or IAM permissions."}

# --- WORKFLOW ---

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