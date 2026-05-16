from fastapi import FastAPI, Request
from app.graph import app_graph

app = FastAPI(title="SRE AI Agent API")

@app.post("/webhook")
async def handle_alert(request: Request):
    payload = await request.json()
    
    try:
        app_name = payload.get("alerts", [{}])[0].get("labels", {}).get("app", "unknown-service")
    except (IndexError, AttributeError):
        app_name = "unknown-service"
    
    initial_state = {
        "alert_payload": payload,
        "app_name": app_name,
        "context_data": [],
        "analysis_report": None,
        "messages": []
    }
    
    try:
        final_state = await app_graph.ainvoke(initial_state)
        analysis_report = final_state.get("analysis_report")
        
        if hasattr(analysis_report, "model_dump"):
            analysis_data = analysis_report.model_dump()
        else:
            analysis_data = {
                "severity": "UNKNOWN",
                "title": "Analysis Format Error",
                "root_cause": "O grafo não retornou um objeto de análise válido.",
                "evidence": str(analysis_report),
                "confidence_score": 0.0
            }
        
        return {
            "status": "processed",
            "app_detected": final_state.get("app_name", app_name),
            "analysis": analysis_data
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Erro interno no processamento do Grafo: {str(e)}"
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)