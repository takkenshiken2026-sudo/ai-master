"""案B: 5カテゴリ用語シード（MECE）。

  basics       基礎・機械学習
  models-tech  モデル・技術
  genai-use    生成AI活用
  data-ops     データ・運用
  governance   倫理・ビジネス
"""

from .basics import TERMS as BASICS
from .data_ops import TERMS as DATA_OPS
from .genai_use import TERMS as GENAI_USE
from .governance import TERMS as GOVERNANCE
from .models_tech import TERMS as MODELS_TECH

ALL_BY_CATEGORY = {
    "basics": BASICS,
    "models-tech": MODELS_TECH,
    "genai-use": GENAI_USE,
    "data-ops": DATA_OPS,
    "governance": GOVERNANCE,
}
