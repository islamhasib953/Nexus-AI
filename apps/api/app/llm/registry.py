from app.llm.models import ModelSpec


class ModelRegistry:
    def __init__(self, models: tuple[ModelSpec, ...] | None = None) -> None:
        self._models = {model.id: model for model in models or default_models()}

    def get(self, model_id: str) -> ModelSpec:
        try:
            return self._models[model_id]
        except KeyError as error:
            raise ValueError(f"Unknown model id: {model_id}") from error

    def all(self) -> tuple[ModelSpec, ...]:
        return tuple(self._models.values())


def default_models() -> tuple[ModelSpec, ...]:
    return (
        ModelSpec("mock-chat", "mock", "mock-chat", 8192, True),
        ModelSpec("groq-gpt-oss-20b", "groq", "openai/gpt-oss-20b", 131072, True),
        ModelSpec("hf-qwen3", "huggingface", "Qwen/Qwen3-32B", 32768, True),
        ModelSpec("ollama-qwen3", "ollama", "qwen3:8b", 32768, True),
    )
