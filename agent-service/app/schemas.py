from pydantic import BaseModel, Field

class HermesEnrichmentResponse(BaseModel):
    severity: str = Field(..., description="Nível de criticidade recalculado pelo Hermes (CRITICAL, WARNING, INFO).")
    title: str = Field(..., description="Título curto e técnico do incidente (ex: 'Auth-Service OOM Killed').")
    root_cause: str = Field(..., description="O motivo do erro (o 'porquê' e o 'onde') baseado na análise dos logs.")
    evidence: str = Field(..., description="O trecho exato do log ou erro bruto que comprova a causa raiz.")
    confidence_score: float = Field(..., description="Grau de certeza da análise (de 0 a 10).")