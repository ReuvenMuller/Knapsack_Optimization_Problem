from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class Chunk:
    chunk_id: int
    text: str
    source_example_id: str
    title: str
    paragraph_index: int
    source_sentence_index: int
    token_cost: int
    is_gold_support: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "text": self.text,
            "source_example_id": self.source_example_id,
            "title": self.title,
            "paragraph_index": self.paragraph_index,
            "source_sentence_index": self.source_sentence_index,
            "token_cost": self.token_cost,
            "is_gold_support": self.is_gold_support,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Chunk":
        return cls(
            chunk_id=int(data["chunk_id"]),
            text=str(data["text"]),
            source_example_id=str(data["source_example_id"]),
            title=str(data["title"]),
            paragraph_index=int(data["paragraph_index"]),
            source_sentence_index=int(data["source_sentence_index"]),
            token_cost=int(data["token_cost"]),
            is_gold_support=bool(data["is_gold_support"]),
        )


@dataclass
class MergedInstance:
    merged_id: str
    merge_size: int
    target_example_id: str
    question: str
    answer: str
    chunks: list[Chunk]
    source_example_ids: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "merged_id": self.merged_id,
            "merge_size": self.merge_size,
            "target_example_id": self.target_example_id,
            "question": self.question,
            "answer": self.answer,
            "source_example_ids": self.source_example_ids,
            "chunks": [chunk.to_dict() for chunk in self.chunks],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MergedInstance":
        return cls(
            merged_id=str(data["merged_id"]),
            merge_size=int(data["merge_size"]),
            target_example_id=str(data["target_example_id"]),
            question=str(data["question"]),
            answer=str(data["answer"]),
            source_example_ids=[str(x) for x in data["source_example_ids"]],
            chunks=[Chunk.from_dict(x) for x in data["chunks"]],
        )
