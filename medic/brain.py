import json
import os
from abc import ABC, abstractmethod

from dotenv import load_dotenv

load_dotenv()
import requests


class AIBackend(ABC):
    """Abstract base class for AI backends"""

    @abstractmethod
    def query(self, prompt: str) -> str:
        """Send prompt to AI and return response"""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this backend is properly configured and reachable"""
        pass


class OpenAIBackend(AIBackend):
    """OpenAI GPT backend (cloud-based)"""

    def __init__(self, api_key=None, model="gpt-4.1-mini"):
        self.api_key = api_key or os.getenv("API_KEY") or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.url = "https://api.openai.com/v1/chat/completions"

    def is_available(self) -> bool:
        return self.api_key is not None

    def query(self, prompt: str) -> str:
        if not self.api_key:
            return "Error: OpenAI API key not found. Set API_KEY or OPENAI_API_KEY env variable."

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
        }

        try:
            response = requests.post(
                self.url,
                headers=headers,
                data=json.dumps(payload),
                timeout=60
            )
            if response.status_code != 200:
                return f"Error {response.status_code}: {response.text}"
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except requests.exceptions.Timeout:
            return "Error: Request timed out. OpenAI API may be slow or unreachable."
        except Exception as e:
            return f"Connection Error: {e}"


class OllamaBackend(AIBackend):
    """Ollama backend (local models like Llama3, DeepSeek, Mistral)"""

    def __init__(self, host=None, model="llama3.2"):
        self.host = host or os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.model = model or os.getenv("OLLAMA_MODEL", "llama3.2")
        self.url = f"{self.host}/api/chat"

    def is_available(self) -> bool:
        """Check if Ollama server is running"""
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=2)
            return response.status_code == 200
        except:
            return False

    def query(self, prompt: str) -> str:
        # Check if Ollama is reachable
        if not self.is_available():
            return (
                f"Error: Cannot connect to Ollama at {self.host}.\n"
                "Make sure Ollama is installed and running:\n"
                "  1. Install: https://ollama.com/download\n"
                "  2. Run: ollama run {model}\n"
                "  3. Or start server: ollama serve"
            ).format(model=self.model)

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False
        }

        try:
            response = requests.post(
                self.url,
                json=payload,
                timeout=120  # Local models can be slow
            )
            if response.status_code != 200:
                # Try to parse error
                try:
                    error_data = response.json()
                    error_msg = error_data.get("error", response.text)
                except:
                    error_msg = response.text
                return f"Error {response.status_code}: {error_msg}"

            data = response.json()
            return data["message"]["content"]
        except requests.exceptions.Timeout:
            return "Error: Request timed out. Local models can be slow—try a smaller model or check system resources."
        except Exception as e:
            return f"Connection Error: {e}"


class BackendFactory:
    """Factory for creating AI backends"""

    _backends = {
        "openai": OpenAIBackend,
        "ollama": OllamaBackend,
    }

    @classmethod
    def create(cls, backend_name: str, model: str = None, **kwargs) -> AIBackend:
        """Create a backend instance by name"""
        backend_name = backend_name.lower()
        if backend_name not in cls._backends:
            available = ", ".join(cls._backends.keys())
            raise ValueError(f"Unknown backend '{backend_name}'. Available: {available}")

        # Pass model parameter if provided
        if model:
            kwargs["model"] = model

        return cls._backends[backend_name](**kwargs)

    @classmethod
    def list_backends(cls) -> list:
        """List available backend names"""
        return list(cls._backends.keys())

    @classmethod
    def auto_select(cls, model: str = None) -> AIBackend:
        """
        Auto-select best available backend:
        1. Try Ollama (local, private, free)
        2. Fall back to OpenAI (requires API key)
        """
        ollama = OllamaBackend(model=model) if model else OllamaBackend()
        if ollama.is_available():
            print("🔮 Using local Ollama backend (private & offline)")
            return ollama

        openai = OpenAIBackend(model=model) if model else OpenAIBackend()
        if openai.is_available():
            print("☁️  Using OpenAI backend (cloud-based)")
            return openai

        raise RuntimeError(
            "No AI backend available.\n"
            "  - Install Ollama for local/private mode: https://ollama.com\n"
            "  - Or set OPENAI_API_KEY env variable for cloud mode."
        )


# Legacy function for backward compatibility
def query_model(prompt, backend=None, model=None):
    """
    Query AI model with optional backend selection.

    Args:
        prompt: The prompt to send
        backend: Backend name ("openai", "ollama") or None for auto-select
        model: Specific model name to use (e.g., "gpt-4", "deepseek-r1:8b")

    Returns:
        Response string from the AI
    """
    if backend is None:
        ai = BackendFactory.auto_select(model=model)
    else:
        ai = BackendFactory.create(backend, model=model)

    return ai.query(prompt)
