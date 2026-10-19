from app.llm.models import ModelSpec


class ModelRegistry:
    def __init__(self, models: tuple[ModelSpec, ...] | None = None) -> None:
        configured = models or default_models()
        if len({model.id for model in configured}) != len(configured):
            raise ValueError("Model identifiers must be unique.")
        self._models = {model.id: model for model in configured}

    def get(self, model_id: str) -> ModelSpec:
        try:
            return self._models[model_id]
        except KeyError as error:
            raise ValueError(f"Unknown model id: {model_id}") from error

    def all(self) -> tuple[ModelSpec, ...]:
        return tuple(self._models.values())

    def by_provider(self, provider: str) -> tuple[ModelSpec, ...]:
        return tuple(model for model in self._models.values() if model.provider == provider)


def default_models() -> tuple[ModelSpec, ...]:
    return (
        ModelSpec(
            "mock-chat",
            "mock",
            "mock-chat",
            8192,
            True,
            supports_tools=False,
            capabilities=("chat", "structured_output", "test_only"),
        ),
        ModelSpec(
            "groq-gpt-oss-20b",
            "groq",
            "openai/gpt-oss-20b",
            131072,
            True,
            supports_tools=True,
            requires_api_key=True,
            capabilities=("chat", "structured_output", "tools"),
        ),
        ModelSpec(
            "groq-gpt-oss-120b",
            "groq",
            "openai/gpt-oss-120b",
            131072,
            True,
            supports_tools=True,
            requires_api_key=True,
            capabilities=("chat", "structured_output", "tools", "reasoning"),
        ),
        ModelSpec(
            "groq-qwen3.8-27b",
            "groq",
            "qwen/qwen3.8-27b",
            131072,
            True,
            supports_tools=True,
            requires_api_key=True,
            capabilities=("chat", "structured_output", "tools"),
        ),
        ModelSpec(
            "groq-allam-2-7b",
            "groq",
            "allam-2-7b",
            32768,
            True,
            supports_tools=True,
            requires_api_key=True,
            capabilities=("chat", "structured_output", "arabic"),
        ),
        ModelSpec(
            "hf-qwen3",
            "huggingface",
            "Qwen/Qwen3-32B",
            32768,
            True,
            requires_api_key=True,
            capabilities=("chat", "structured_output", "code", "reasoning"),
        ),
        ModelSpec(
            "ollama-qwen3",
            "ollama",
            "qwen3:8b",
            32768,
            True,
            capabilities=("chat", "structured_output", "local"),
        ),
    )
