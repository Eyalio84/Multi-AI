"""Intelligent model selection based on task type, complexity, and budget."""
from config import MODE, MODELS


def route(
    task_type: str = "general",
    complexity: str = "medium",
    budget_preference: str = "balanced",
    context_length: int = 0,
) -> dict:
    """
    Select optimal model based on task characteristics.

    Args:
        task_type: general, coding, reasoning, creative, bulk, embedding,
                   image, video, audio, music, agent
        complexity: low, medium, high
        budget_preference: cheap, balanced, quality
        context_length: estimated input tokens

    Returns:
        {"provider": str, "model": str, "reason": str}
    """
    # Media/specialized — always Gemini
    if task_type == "video":
        return {"provider": "gemini", "model": "veo-3.1-generate-preview", "reason": "Video generation via Veo 3.1"}
    if task_type == "image":
        if budget_preference == "quality":
            return {"provider": "gemini", "model": "gemini-3-pro-image-preview", "reason": "High-quality image gen (Nano Banana Pro)"}
        return {"provider": "gemini", "model": "gemini-2.5-flash-image", "reason": "Fast image generation via Gemini"}
    if task_type == "audio":
        if budget_preference == "quality":
            return {"provider": "gemini", "model": "gemini-2.5-pro-preview-tts", "reason": "High-quality TTS via Gemini Pro"}
        return {"provider": "gemini", "model": "gemini-2.5-flash-preview-tts", "reason": "TTS via Gemini Flash"}
    if task_type == "music":
        return {"provider": "gemini", "model": "lyria-realtime-exp", "reason": "Music generation via Lyria"}
    if task_type == "embedding":
        return {"provider": "gemini", "model": "gemini-embedding-001", "reason": "Embeddings via Gemini"}
    if task_type == "agent":
        if MODE == "standalone":
            return {"provider": "claude", "model": "claude-opus-4-6", "reason": "Autonomous agent via Claude Agent SDK"}
        return {"provider": "gemini", "model": "deep-research-pro-preview", "reason": "Deep research agent via Gemini"}

    # Large context always Gemini (1M window)
    if context_length > 150000:
        return {"provider": "gemini", "model": "gemini-2.5-pro", "reason": "Large context requires Gemini's 1M window"}

    # Claude-code mode: always Gemini
    if MODE == "claude-code":
        if budget_preference == "cheap" or complexity == "low":
            return {"provider": "gemini", "model": "gemini-2.5-flash", "reason": "Fast & cheap (claude-code mode)"}
        return {"provider": "gemini", "model": "gemini-2.5-pro", "reason": "Best Gemini reasoning (claude-code mode)"}

    # Standalone mode: choose between providers
    if budget_preference == "cheap":
        if complexity == "low":
            return {"provider": "gemini", "model": "gemini-2.5-flash", "reason": "Cheapest option for simple tasks"}
        return {"provider": "claude", "model": "claude-haiku-4-5-20251001", "reason": "Budget Claude for medium tasks"}

    if task_type == "coding":
        if complexity == "high":
            return {"provider": "claude", "model": "claude-sonnet-4-6", "reason": "Claude excels at complex coding"}
        return {"provider": "gemini", "model": "gemini-2.5-flash", "reason": "Fast coding with Gemini Flash"}

    if task_type == "reasoning":
        if complexity == "high":
            return {"provider": "claude", "model": "claude-opus-4-6", "reason": "Claude Opus for deep reasoning"}
        return {"provider": "claude", "model": "claude-sonnet-4-6", "reason": "Claude Sonnet for reasoning"}

    if budget_preference == "quality":
        return {"provider": "claude", "model": "claude-opus-4-6", "reason": "Highest quality model"}

    # Default balanced
    if complexity == "high":
        return {"provider": "claude", "model": "claude-sonnet-4-6", "reason": "Balanced quality for complex tasks"}
    return {"provider": "gemini", "model": "gemini-2.5-flash", "reason": "Fast default for general tasks"}
