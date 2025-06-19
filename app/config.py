"""
Module: Config
Provides GPT client for AI-powered modules, using OpenAI as default. Extendable for other models.
"""
import openai
import os

def get_gpt_client(model_type: str = "openai"):
    """
    Return a GPT client for the specified model type. Currently supports OpenAI.
    Reads API key from environment variable or config.
    """
    if model_type == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            # Fallback: try to read from a local file or raise error
            try:
                with open("openai_api_key.txt") as f:
                    api_key = f.read().strip()
            except Exception:
                raise RuntimeError("OpenAI API key not found. Set OPENAI_API_KEY env variable or provide openai_api_key.txt.")
        openai.api_key = api_key
        return openai
    else:
        raise NotImplementedError(f"Model type '{model_type}' is not supported yet.") 