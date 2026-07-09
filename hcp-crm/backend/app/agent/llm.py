from langchain_groq import ChatGroq

from app.config import settings

_llm_cache = {}


def get_llm(model: str | None = None, temperature: float = 0.2) -> ChatGroq:
    """Return a (cached) ChatGroq client for the given model.

    Defaults to the required gemma2-9b-it model. Pass model="llama-3.3-70b-versatile"
    to experiment with the optional larger model.
    """
    model_name = model or settings.groq_model
    cache_key = (model_name, temperature)
    if cache_key not in _llm_cache:
        _llm_cache[cache_key] = ChatGroq(
            api_key=settings.groq_api_key,
            model=model_name,
            temperature=temperature,
        )
    return _llm_cache[cache_key]
