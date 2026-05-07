"""
scenarios/*.json のスキーマ定義。

使い方:
  scenario = Scenario.model_validate_json(path.read_text())
  # または
  scenario = Scenario.model_validate(json.loads(path.read_text()))
"""

from typing import Any, Optional
from pydantic import BaseModel, Field


class CharacterAppearance(BaseModel):
    hair: str = Field(description="髪の色・長さ・スタイル")
    eyes: str = Field(description="瞳の色")
    build: str = Field(description="体型・体格")
    age: str = Field(description="年齢（または見た目年齢）")


class Character(BaseModel):
    name: str = Field(description="キャラクター名（日本語）")
    name_en: str = Field(description="キャラクター名（英語・ローマ字）")
    series: str = Field(description="原作シリーズ名")
    base_tags: str = Field(
        description="キャラ同定タグ。ComfyUI プロンプトの先頭に付く（例: 'nami, one piece'）"
    )
    appearance_tags: str = Field(
        description="外見タグ文字列。ComfyUI プロンプトに直接使われる（例: 'orange hair, long hair, brown eyes'）"
    )
    appearance: CharacterAppearance = Field(
        description="外見の自然言語記述。planner が scene の tags/description を生成するときに参照する"
    )
    outfits: list[str] = Field(
        description="衣装リスト。シーンごとにどの衣装を着るかの判断に使われる"
    )
    personality: str = Field(
        description="性格・特徴の一行要約。planner がセリフや表情を生成するときに参照する"
    )
    notes: list[str] = Field(
        default_factory=list,
        description="補足情報（描写上の注意点、NGポーズ、特記事項など）",
    )


class Scenario(BaseModel):
    idea: Optional[str] = Field(
        None,
        description="シナリオの発想メモ（任意・pipeline には未使用）",
    )
    character: Character = Field(description="キャラクター定義")
    story: str = Field(
        description="ストーリー本文。plan_scenes(story, character) にそのまま渡される"
    )
    scenes: Optional[list[Any]] = Field(
        None,
        description="plan_scenes() の出力。pipeline 実行後に書き戻される。初回は None",
    )
