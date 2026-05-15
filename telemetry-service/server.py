import os
import json
import uvicorn
from fastapi import FastAPI, HTTPException

app = FastAPI(title="Hermes Telemetry Provider")

@app.get("/logs/{app_name}")
async def get_app_logs(app_name: str, limit: int = 15):
    """Endpoint REST simples para busca de logs."""
    
    if os.getenv("USE_GCP_LOGGING") == "true":
        try:
            from google.cloud import logging
            client = logging.Client()
            log_filter = f'resource.labels.service_name="{app_name}" AND severity>=ERROR'
            entries = client.list_entries(filter_=log_filter, max_results=limit)
            
            logs = [f"[{e.timestamp}] [{e.severity}] {e.payload}" for e in entries]
            return {"app": app_name, "logs": logs if logs else ["Nenhum log de erro encontrado."]}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro GCP: {str(e)}")

    mocks_path = "./mocks"
    file_path = os.path.join(mocks_path, f"{app_name}.json")
    
    if not os.path.exists(file_path):
        return {"app": app_name, "logs": [f"Modo local: Mock para {app_name} não encontrado."]}
        
    try:
        with open(file_path, "r") as f:
            data = json.load(f)
            logs = [f"[{d.get('timestamp')}] [ERROR] {d.get('message')}" for d in data[:limit]]
            return {"app": app_name, "logs": logs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro leitura mock: {str(e)}")

@app.get("/health")
async def health():
    return {"status": "ok", "mode": "GCP" if os.getenv("USE_GCP_LOGGING") == "true" else "LOCAL"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)