"""用語辞典から除外する ID（AIツール記事と役割分担）。"""

# category=tool は丸ごと除外。genai 等に紛れ込んだ製品名もここで除外。
EXCLUDED_TERM_IDS = frozenset({
    "automatic1111",
    "azure-openai",
    "canva-ai",
    "comfyui",
    "copilot",
    "cursor-ai",
    "dall-e",
    "elevenlabs",
    "gemini",
    "github-copilot",
    "huggingface-hub",
    "lm-studio",
    "notion-ai",
    "ollama",
    "openai-api",
    "openrouter",
    "runway",
    "sora",
    "whisper",
})

EXCLUDED_CATEGORIES = frozenset({"tool"})
