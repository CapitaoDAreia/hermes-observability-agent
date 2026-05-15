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
        "analysis_report": "",
        "messages": []
    }
    
    try:
        final_state = await app_graph.ainvoke(initial_state)
        
        return {
            "status": "processed",
            "app_detected": final_state.get("app_name", app_name),
            "analysis": final_state.get("analysis_report", "Erro no processamento da análise.")
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Erro interno no processamento do Grafo: {str(e)}"
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)