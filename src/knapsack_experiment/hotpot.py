from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any

from .chunking import estimate_token_count, split_by_period
from .model import Chunk, MergedInstance


@dataclass
class SourceParagraph:
    title: str
    sentences: list[str]
    paragraph_index: int


@dataclass
class SourceExample:
    example_id: str
    question: str
    answer: str
    paragraphs: list[SourceParagraph]
    supporting_pairs: set[tuple[str, int]]


def load_hotpotqa_examples(config: str, split: str) -> list[SourceExample]:
    """
    Load HotpotQA examples through Hugging Face datasets.
    """
    try:
        from datasets import load_dataset
    except ImportError as exc:
        raise RuntimeError(
            "Missing dependency 'datasets'. Install with: pip install -r requirements.txt"
        ) from exc

    dataset = load_dataset("hotpotqa/hotpot_qa", config, split=split)
    examples: list[SourceExample] = []
    for row in dataset:
        context = row["context"]
        titles = list(context["title"])
        sentence_groups = list(context["sentences"])
        paragraphs: list[SourceParagraph] = []
        for idx, title in enumerate(titles):
            sentences = [str(s) for s in sentence_groups[idx]]
            paragraphs.append(
                SourceParagraph(title=str(title), sentences=sentences, paragraph_index=idx)
            )

        supporting_facts = row["supporting_facts"]
        pairs = set(
            (str(title), int(sent_idx))
            for title, sent_idx in zip(supporting_facts["title"], supporting_facts["sent_id"])
        )
        examples.append(
            SourceExample(
                example_id=str(row["id"]),
                question=str(row["question"]),
                answer=str(row["answer"]),
                paragraphs=paragraphs,
                supporting_pairs=pairs,
            )
        )
    return examples


def _chunk_sentence(sentence: str, chunking_mode: str) -> list[str]:
    if chunking_mode == "period":
        return split_by_period(sentence)
    if chunking_mode == "as_is":
        text = sentence.strip()
        return [text] if text else []
    raise ValueError(f"Unsupported chunking_mode='{chunking_mode}'")


def build_merged_instances(
    source_examples: list[SourceExample],
    merge_sizes: list[int],
    samples_per_size: int,
    seed: int = 42,
    chunking_mode: str = "period",
    shuffle_chunks: bool = True,
) -> list[MergedInstance]:
    """
    Build merged instances:
    - keep 1 target QA pair
    - add contexts from (merge_size - 1) other examples as distractors
    - chunk by sentence (with optional split on periods)
    """
    if not source_examples:
        raise ValueError("source_examples is empty")

    max_size = max(merge_sizes)
    if max_size > len(source_examples):
        raise ValueError(
            f"Cannot merge size {max_size}; source split has only {len(source_examples)} examples."
        )

    rng = random.Random(seed)
    all_indices = list(range(len(source_examples)))
    merged: list[MergedInstance] = []

    for merge_size in merge_sizes:
        for sample_idx in range(samples_per_size):
            target_idx = rng.choice(all_indices)
            target_example = source_examples[target_idx]

            distractor_pool = [idx for idx in all_indices if idx != target_idx]
            distractor_indices = rng.sample(distractor_pool, merge_size - 1)
            selected_indices = [target_idx] + distractor_indices
            source_ids = [source_examples[idx].example_id for idx in selected_indices]

            chunks: list[Chunk] = []
            chunk_id = 0
            for idx in selected_indices:
                source = source_examples[idx]
                is_target = source.example_id == target_example.example_id
                for paragraph in source.paragraphs:
                    for sent_idx, sentence in enumerate(paragraph.sentences):
                        sentence_pieces = _chunk_sentence(sentence, chunking_mode)
                        for piece in sentence_pieces:
                            text = piece.strip()
                            if not text:
                                continue
                            is_gold_support = is_target and (
                                paragraph.title,
                                sent_idx,
                            ) in target_example.supporting_pairs
                            chunks.append(
                                Chunk(
                                    chunk_id=chunk_id,
                                    text=text,
                                    source_example_id=source.example_id,
                                    title=paragraph.title,
                                    paragraph_index=paragraph.paragraph_index,
                                    source_sentence_index=sent_idx,
                                    token_cost=estimate_token_count(text),
                                    is_gold_support=is_gold_support,
                                )
                            )
                            chunk_id += 1

            if shuffle_chunks:
                rng.shuffle(chunks)
                # Re-sequence chunk ids after shuffling for consistency.
                for idx, chunk in enumerate(chunks):
                    chunk.chunk_id = idx

            merged_id = f"merge_{merge_size:02d}_sample_{sample_idx:03d}"
            merged.append(
                MergedInstance(
                    merged_id=merged_id,
                    merge_size=merge_size,
                    target_example_id=target_example.example_id,
                    question=target_example.question,
                    answer=target_example.answer,
                    chunks=chunks,
                    source_example_ids=source_ids,
                )
            )
    return merged


def export_merged_jsonl(instances: list[MergedInstance], output_path: str) -> None:
    import json
    import os

    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as handle:
        for instance in instances:
            handle.write(json.dumps(instance.to_dict(), ensure_ascii=False) + "\n")


def load_merged_jsonl(path: str) -> list[MergedInstance]:
    import json

    instances: list[MergedInstance] = []
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            payload: dict[str, Any] = json.loads(line)
            instances.append(MergedInstance.from_dict(payload))
    return instances
