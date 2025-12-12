from typing import Dict, List

class AnthropicModel:
    def __init__(self, name: str, api_id: str, description: str, context_window: str, max_output: str):
        self.name = name
        self.api_id = api_id
        self.description = description
        self.context_window = context_window
        self.max_output = max_output

# Model Definitions based on Anthropic documentation
MODELS: List[AnthropicModel] = [
    AnthropicModel(
        name="Claude Sonnet 4.5",
        api_id="claude-sonnet-4-5-20250929",
        description="Our smart model for complex agents and coding. Best balance of intelligence, speed, and cost.",
        context_window="200K tokens / 1M tokens (beta)",
        max_output="64K tokens"
    ),
    AnthropicModel(
        name="Claude Haiku 4.5",
        api_id="claude-haiku-4-5-20251001",
        description="Our fastest model with near-frontier intelligence.",
        context_window="200K tokens",
        max_output="64K tokens"
    ),
    AnthropicModel(
        name="Claude Opus 4.5",
        api_id="claude-opus-4-5-20251101",
        description="Premium model combining maximum intelligence with practical performance.",
        context_window="200K tokens",
        max_output="64K tokens"
    ),
    # Fallback/Legacy models if needed
    AnthropicModel(
        name="Claude 3.5 Sonnet",
        api_id="claude-3-5-sonnet-20240620",
        description="Previous generation Sonnet model.",
        context_window="200K tokens",
        max_output="4096 tokens"
    )
]

DEFAULT_MODEL_ID = "claude-sonnet-4-5-20250929"

def get_model_by_id(api_id: str) -> AnthropicModel:
    for model in MODELS:
        if model.api_id == api_id:
            return model
    return MODELS[0] # Return default if not found
