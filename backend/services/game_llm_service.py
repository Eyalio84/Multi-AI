"""Local LLM service for game NPC dialogue.

Wraps llama-cpp-python for on-device inference with DeepSeek R1, Gemma 3 1B,
Gemma 2 2B, and Qwen models. Single model loaded at a time to manage memory.
"""

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Model paths — adjust to actual locations on device
MODELS_DIR = Path("/storage/emulated/0/Download/models")

MODEL_CONFIGS: dict[str, dict] = {
    "deepseek": {
        "name": "DeepSeek R1 1.5B",
        "pattern": "deepseek-r1*",
        "context_len": 2048,
        "default_temp": 0.7,
        "desc": "Best reasoning for complex NPC dialogue",
    },
    "gemma3_1b": {
        "name": "Gemma 3 1B",
        "pattern": "gemma-3*1b*",
        "context_len": 2048,
        "default_temp": 0.7,
        "desc": "Fastest responses for quick NPC interactions",
    },
    "gemma2_2b": {
        "name": "Gemma 2 2B",
        "pattern": "gemma-2*2b*",
        "context_len": 2048,
        "default_temp": 0.7,
        "desc": "Richest dialogue with more nuance",
    },
    "qwen": {
        "name": "Qwen 2.5",
        "pattern": "qwen*",
        "context_len": 2048,
        "default_temp": 0.7,
        "desc": "Multilingual NPC dialogue support",
    },
}


class GameLLMService:
    """Manages local LLM loading and NPC chat inference."""

    def __init__(self):
        self._model: Any = None
        self._model_type: str | None = None
        self._llama_cpp = None

    def _find_model_file(self, model_type: str) -> Path | None:
        """Find GGUF model file matching config pattern."""
        config = MODEL_CONFIGS.get(model_type)
        if not config:
            return None

        if not MODELS_DIR.exists():
            return None

        import glob
        pattern = str(MODELS_DIR / config["pattern"])
        # Search for .gguf files
        for ext in ("*.gguf", "*.bin"):
            matches = glob.glob(f"{pattern}{ext}") + glob.glob(f"{pattern}/{ext}")
            if matches:
                return Path(matches[0])

        # Also check direct name matches
        for f in MODELS_DIR.iterdir():
            if f.suffix in (".gguf", ".bin") and any(
                part in f.name.lower()
                for part in config["pattern"].replace("*", "").split()
                if part
            ):
                return f

        return None

    def get_status(self) -> dict:
        """Return current model status."""
        return {
            "loaded": self._model is not None,
            "model_type": self._model_type,
            "model_name": MODEL_CONFIGS.get(self._model_type, {}).get("name", "") if self._model_type else None,
            "available_models": {
                k: {
                    "name": v["name"],
                    "desc": v["desc"],
                    "file_found": self._find_model_file(k) is not None,
                }
                for k, v in MODEL_CONFIGS.items()
            },
        }

    def load_model(self, model_type: str) -> dict:
        """Load a local model. Unloads any existing model first."""
        if model_type not in MODEL_CONFIGS:
            return {"error": f"Unknown model type: {model_type}"}

        # Unload existing
        if self._model is not None:
            self.unload()

        model_path = self._find_model_file(model_type)
        if not model_path:
            return {"error": f"Model file not found for {model_type}. Check {MODELS_DIR}"}

        try:
            from llama_cpp import Llama
            self._llama_cpp = Llama

            config = MODEL_CONFIGS[model_type]
            self._model = Llama(
                model_path=str(model_path),
                n_ctx=config["context_len"],
                n_threads=4,
                verbose=False,
            )
            self._model_type = model_type
            logger.info(f"Loaded {config['name']} from {model_path}")
            return {
                "status": "loaded",
                "model": config["name"],
                "path": str(model_path),
            }
        except ImportError:
            return {"error": "llama-cpp-python not installed. Run: pip install llama-cpp-python"}
        except Exception as ex:
            logger.error(f"Failed to load model: {ex}")
            return {"error": str(ex)}

    def unload(self) -> dict:
        """Unload the current model to free memory."""
        if self._model is None:
            return {"status": "no_model_loaded"}

        name = MODEL_CONFIGS.get(self._model_type, {}).get("name", "Unknown")
        del self._model
        self._model = None
        self._model_type = None

        # Force garbage collection
        import gc
        gc.collect()

        logger.info(f"Unloaded {name}")
        return {"status": "unloaded", "model": name}

    def chat(
        self,
        npc_name: str,
        system_prompt: str,
        user_message: str,
        history: list[dict] | None = None,
        temperature: float | None = None,
        max_tokens: int = 150,
    ) -> dict:
        """Generate NPC dialogue response."""
        if self._model is None:
            return {"error": "No model loaded. Call load_model() first."}

        config = MODEL_CONFIGS.get(self._model_type, {})
        temp = temperature or config.get("default_temp", 0.7)

        # Build conversation messages
        messages = [{"role": "system", "content": system_prompt}]

        if history:
            for msg in history[-6:]:  # Keep last 6 messages for context
                messages.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", ""),
                })

        messages.append({"role": "user", "content": user_message})

        try:
            response = self._model.create_chat_completion(
                messages=messages,
                temperature=temp,
                max_tokens=max_tokens,
                stop=["User:", "Player:", "\n\n\n"],
            )

            content = response["choices"][0]["message"]["content"].strip()

            return {
                "npc_name": npc_name,
                "response": content,
                "model": config.get("name", self._model_type),
                "tokens_used": response.get("usage", {}).get("total_tokens", 0),
            }
        except Exception as ex:
            logger.error(f"NPC chat error: {ex}")
            return {"error": str(ex), "npc_name": npc_name}


game_llm_service = GameLLMService()
