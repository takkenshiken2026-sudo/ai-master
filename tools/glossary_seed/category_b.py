"""案B: 5カテゴリ（MECE）の分類ルール（参照用）。

シードファイルが正の分類。新規用語追加時の判断基準として使う。

  basics       基礎・機械学習
  models-tech  モデル・技術
  genai-use    生成AI活用
  data-ops     データ・運用
  governance   倫理・ビジネス
"""

from __future__ import annotations

# 旧 genai から models-tech へ（固有名詞モデル・学習手法・モデル属性）
GENAI_MODELS_TECH_IDS = frozenset({
    "adapter",
    "adapter-tuning",
    "alignment",
    "audio-language-model",
    "closed-model",
    "constitutional-ai",
    "continued-pretraining",
    "dpo",
    "embedding-model",
    "foundation-model",
    "full-fine-tuning",
    "generative-ai",
    "gpt",
    "gpt-3",
    "gpt-4",
    "gpt-4o",
    "human-eval",
    "benchmark-mmlu",
    "instruction-tuning",
    "llm",
    "lora",
    "lora-rank",
    "mixtral",
    "model-merging",
    "multimodal-ai",
    "o1-model",
    "open-weights",
    "peft",
    "prefix-tuning",
    "pretraining",
    "qlora",
    "reward-model",
    "sft",
    "speculative-decoding",
    "claude-model",
    "codex-model",
    "dalle-model",
    "deepseek",
    "falcon-llm",
    "flux-model",
    "gemini-model",
    "gemma",
    "imagen",
    "palm-model",
    "phi-model",
    "qwen",
    "sdxl",
    "sora-model",
    "stable-diffusion",
    "vision-language-model",
    "whisper-model",
    "evaluation-harness",
    "model-card",
})

# 旧カテゴリのデフォルト変換
OLD_CATEGORY_DEFAULT = {
    "basic": "basics",
    "ml": "basics",
    "dl": "models-tech",
    "nlp": "models-tech",
    "cv": "models-tech",
    "data": "data-ops",
    "ethics": "governance",
    "biz": "governance",
}

# ID 単位の上書き（デフォルト変換後に適用）
ID_OVERRIDES: dict[str, str] = {
    # basic
    "nlp": "models-tech",
    "connectionism": "models-tech",
    "self-supervised-learning": "models-tech",
    "ai-ethics-overview": "governance",
    # ml → data-ops / models-tech
    "mlops": "data-ops",
    "feature-store": "data-ops",
    "fi-feature-platform": "data-ops",
    "generative-model": "models-tech",
    "discriminative-model": "models-tech",
    "model-evaluation": "basics",
    "model-drift": "data-ops",
    "model-registry": "data-ops",
    # genai split handled below
    "token": "models-tech",
    "bos-token": "models-tech",
    "eos-token": "models-tech",
    "special-token": "models-tech",
    "chat-template": "models-tech",
    # datasets → data-ops
    "instruction-dataset": "data-ops",
    "preference-dataset": "data-ops",
    "eval-dataset": "data-ops",
    "data-card": "data-ops",
    "synthetic-data-generation": "data-ops",
    "human-preference": "models-tech",
    "preference-pair": "models-tech",
    # literacy spans governance
    "ai-literacy": "governance",
    "responsible-ai": "governance",
    "model-card-genai": "governance",
    "model-governance-ethics": "governance",
}


NEW_CATEGORIES = frozenset({
    "basics",
    "models-tech",
    "genai-use",
    "data-ops",
    "governance",
})


def category_for_term(term_id: str, old_category: str) -> str:
    if old_category in NEW_CATEGORIES:
        return ID_OVERRIDES.get(term_id, old_category)

    if old_category == "genai":
        if term_id in GENAI_MODELS_TECH_IDS:
            return "models-tech"
        return "genai-use"

    cat = OLD_CATEGORY_DEFAULT.get(old_category, old_category)
    return ID_OVERRIDES.get(term_id, cat)
