"""用語辞典から削除する ID（重複・ニッチ過ぎ・製品寄り・試験優先度低）。"""

REMOVAL_IDS = frozenset({
    # ── 重複・別語でカバー ──
    "retrieval-augmented",  # rag
    "transfer-learning-dl",
    "transfer-learning-cv",
    "vae",  # variational-autoencoder
    "tokenization-nlp",  # tokenization
    "encoder-decoder-transformer",  # encoder-decoder + transformer
    "data-augmentation-cv",  # image-augmentation
    "differential-privacy-dl",  # differential-privacy
    "anomaly-detection-image",  # anomaly-detection
  # ── フレームワーク・製品寄り（SEO用語は restorations.py で維持） ──
    "private-gpt",
    "llamaindex",
    "semantic-kernel",
    # ── 古い／派生モデル名（代表派生は model_terms.py で維持） ──
    # ── ニッチな生成・GAN派生 ──
    "energy-based-model",
    "flow-based-model",
    "normalizing-flow",
    "score-based-model",
    "capsule-network",
    "differentiable-rendering",
    "panoptic-segmentation",
    "swish",
    "scheduled-sampling",
    "weight-tying",
    "fgsm",
    "membership-inference",
    "model-inversion",
    # ── 3D・ニッチ応用（PointNet/WaveNet は model_terms.py で維持） ──
    # ── tier3 哲学・学術寄り ──
    "xor-problem",
    "chinese-room",
    "brain-inspired-computing",
    "cognitive-science",
    "alpha-beta-pruning",
    "forward-chaining",
    "backward-chaining",
    "abstraction",
    # ── tier3 ML ──
    "elastic-net",
    "local-outlier-factor",
    "map-score",
    "one-class-svm",
    "umap",
    "uplift-modeling",
    "apriori-algorithm",
    "gaussian-process",
    "cost-sensitive-learning",
    "demographic-parity",
    "equalized-odds",
    "manifold-learning",
    "polynomial-regression",
    "survival-analysis",
    "inverse-reinforcement-learning",
    # ── tier3 genai / nlp ──
    "benchmark-hellaswag",
    "tree-of-thought",
    "semantic-role-labeling",
    # ── 重複しやすい細分化 ──
    "computer-vision-overview",  # cvカテゴリで扱う
    "feature-extraction-cv",
    "open-vocabulary-detection",
    "zero-shot-classification",
})
