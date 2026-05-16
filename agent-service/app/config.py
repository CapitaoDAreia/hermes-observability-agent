import os
from langchain_google_genai import ChatGoogleGenerativeAI

def get_model():
    """Unified Engine Factory for local or cloud execution."""
    provider = os.getenv("LLM_PROVIDER")
    
    if provider == "GEMINI":
        return ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            project=os.getenv("GOOGLE_CLOUD_PROJECT"),
        )
    
    # Fallback local via Ollama
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(
        base_url=os.getenv("OPENAI_API_BASE"),
        api_key="ollama",
        model=os.getenv("LLM_MODEL")
    )

TELEMETRY_URL = os.getenv("TELEMETRY_SERVICE_URL")