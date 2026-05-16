import httpx
from langchain_core.messages import SystemMessage, HumanMessage
from app.state import AgentState
from app.config import get_model, TELEMETRY_URL
from app.schemas import HermesEnrichmentResponse
from app.prompts import HERMES_ANALYZER_SYSTEM_PROMPT
from pydantic import ValidationError

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
    """Flow decision-maker."""
    logs = state["context_data"][0]
    if "ERROR_HTTP" in logs or "ERROR_NET" in logs or "Nenhum log encontrado" in logs:
        return "error_handler"
    return "analyzer"

def analyze_error_node(state: AgentState):
    """Structured Root Cause Diagnosis with ValidationError fallback."""
    user_content = f"Serviço: {state['app_name']}\nLogs:\n{state['context_data'][0]}"
    
    model = get_model()
    structured_model = model.with_structured_output(HermesEnrichmentResponse)
    
    try:
        response = structured_model.invoke([
            SystemMessage(content=HERMES_ANALYZER_SYSTEM_PROMPT), 
            HumanMessage(content=user_content)
        ])
        return {"analysis_report": response}
        
    except ValidationError as val_err:
        fallback_schema = HermesEnrichmentResponse(
            severity="WARNING",
            title="Analysis Contract Violation",
            root_cause="O Hermes identificou o problema, mas falhou em formatar a resposta dentro das regras estritas do contrato.",
            evidence=f"Erro de Validação: {str(val_err)}",
            confidence_score=50
        )
        return {"analysis_report": fallback_schema}

def error_handler_node(state: AgentState):
    """Fallback for data unavailability."""
    fallback_response = HermesEnrichmentResponse(
        severity="HIGH",
        title="Telemetry Collector Failure",
        root_cause=f"O Hermes não conseguiu coletar telemetria para o app '{state['app_name']}'.",
        evidence=state["context_data"][0],
        confidence_score=1.0
    )
    return {"analysis_report": fallback_response}