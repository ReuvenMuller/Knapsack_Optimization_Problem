import random
from datasets import load_dataset
from utility import compute_utilities


def split_by_period(text):
    parts = text.split(".")
    chunks = []

    for part in parts:
        part = part.strip()
        if part != "":
            chunks.append(part + ".")

    return chunks


def load_hotpotqa_examples():
    dataset = load_dataset("hotpotqa/hotpot_qa", "distractor", split="validation")
    examples = []

    for row in dataset:
        examples.append(
            {
                "id": row["id"],
                "question": row["question"],
                "answer": row["answer"],
                "context": row["context"],
                "supporting_facts": row["supporting_facts"],
            }
        )

    print(f"Loaded {len(examples)} examples from HotpotQA.")
    return examples


def build_merged_instances(source_examples):
    # We set a seed for reproducibility.
    random.seed(42)
    merged_instances = []

    # Here we merge several examples together but keep only one question from one example.
    # This gives us a much larger context to compress.
    # For each merge size, we create 20 samples.
    for merge_size in [10, 20, 30, 40, 50]:
        for sample_index in range(20):
            target_example = random.choice(source_examples)

            # Create a list of all examples except the target example to ensure we don't have duplicates
            remaining_examples = source_examples.copy()
            remaining_examples.remove(target_example)

            distractors = random.sample(remaining_examples, merge_size - 1)
            merged_examples = [target_example] + distractors

            context = []
            chunk_texts = []
            chunk_refs = []

            for example in merged_examples:
                titles = example["context"]["title"]
                sentence_groups = example["context"]["sentences"]

                for i, title in enumerate(titles):
                    chunks = []
                    for sentence in sentence_groups[i]:
                        for chunk in split_by_period(sentence):
                            if chunk.strip() != "":
                                chunk_data = {
                                    "text": chunk.strip(),
                                    "chunk_size": len(chunk.split()),
                                    "chunk_utility": 0.0,
                                    "gold_answer": (
                                        example["id"] == target_example["id"]
                                        and title in target_example["supporting_facts"]["title"]
                                    ),
                                }
                                chunks.append(chunk_data)
                                chunk_texts.append(chunk_data["text"])
                                chunk_refs.append(chunk_data)

                    context.append(
                        {
                            "title": title,
                            "chunks": chunks,
                        }
                    )

            utilities = compute_utilities(target_example["question"], chunk_texts, method="hybrid")
            for i, utility in enumerate(utilities):
                chunk_refs[i]["chunk_utility"] = utility

            merged_instances.append(
                {
                    "merged_id": f"merge_{merge_size}_{sample_index}",
                    "merge_size": merge_size,
                    "target_example_id": target_example["id"],
                    "question": target_example["question"],
                    "answer": target_example["answer"],
                    "context": context,
                }
            )
        print(f"Built 20 merged instances for merge size {merge_size}.")
    print(f"Built {len(merged_instances)} merged instances.")
    return merged_instances


def get_merged_instances():
    print("Loading HotpotQA examples...")
    examples = load_hotpotqa_examples()
    print("Building merged instances...")
    return build_merged_instances(examples)
