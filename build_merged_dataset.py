import csv
import os
import random
from datasets import load_dataset
from utility import compute_utilities

PCT_SEMANTIC = 0.75
PCT_LEXICAL = 0.25
MERGE_SIZES = [10, 20, 30, 40, 50, 75, 100, 150, 200]
SAMPLES_PER_MERGE_SIZE = 20
OUTPUT_DIR = "analysis_outputs"
CHUNK_UTILITIES_PATH = os.path.join(OUTPUT_DIR, "chunk_utilities.csv")
SCORE_CACHE_CHECKPOINT_INTERVAL = 5


def get_supporting_fact_pairs(example):
    """
    HotpotQA marks supporting facts by paragraph title and sentence id.
    We store those pairs so we can label exact supporting sentences.
    """
    titles = example["supporting_facts"]["title"]
    sentence_ids = example["supporting_facts"]["sent_id"]

    pairs = set()
    for title, sentence_id in zip(titles, sentence_ids):
        pairs.add((title, int(sentence_id)))

    return pairs


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


def collect_chunk_rows(merged_instances):
    rows = []

    for instance in merged_instances:
        chunk_index = 0

        for paragraph in instance["context"]:
            for chunk in paragraph["chunks"]:
                rows.append(
                    {
                        "merged_id": instance["merged_id"],
                        "merge_size": instance["merge_size"],
                        "target_example_id": instance["target_example_id"],
                        "paragraph_title": paragraph["title"],
                        "chunk_index": chunk_index,
                        "chunk_size": int(chunk["chunk_size"]),
                        "chunk_utility": float(chunk["chunk_utility"]),
                        "gold_answer": bool(chunk["gold_answer"]),
                        "text": chunk["text"],
                    }
                )
                chunk_index += 1

    return rows


def load_cached_chunk_utilities(path=CHUNK_UTILITIES_PATH):
    if not os.path.exists(path):
        return {}

    cache = {}
    with open(path, "r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            cache.setdefault(row["merged_id"], []).append(row)

    for rows in cache.values():
        rows.sort(key=lambda row: int(row["chunk_index"]))

    return cache


def chunk_refs_for_instance(instance):
    refs = []

    for paragraph in instance["context"]:
        for chunk in paragraph["chunks"]:
            refs.append((paragraph["title"], chunk))

    return refs


def cached_rows_match_instance(cached_rows, instance):
    refs = chunk_refs_for_instance(instance)
    if len(cached_rows) != len(refs):
        return False

    for chunk_index, (cached_row, (paragraph_title, chunk)) in enumerate(zip(cached_rows, refs)):
        if int(cached_row["chunk_index"]) != chunk_index:
            return False
        if cached_row["paragraph_title"] != paragraph_title:
            return False
        if int(cached_row["chunk_size"]) != int(chunk["chunk_size"]):
            return False
        if cached_row["text"] != chunk["text"]:
            return False

    return True


def apply_cached_chunk_utilities(instance, cached_rows):
    refs = chunk_refs_for_instance(instance)

    for cached_row, (_, chunk) in zip(cached_rows, refs):
        chunk["chunk_utility"] = float(cached_row["chunk_utility"])


def write_chunk_utility_cache(merged_instances, existing_cache=None, path=CHUNK_UTILITIES_PATH):
    existing_cache = existing_cache or {}
    current_rows = collect_chunk_rows(merged_instances)
    current_ids = {row["merged_id"] for row in current_rows}

    rows = current_rows[:]
    for merged_id in sorted(existing_cache):
        if merged_id not in current_ids:
            rows.extend(existing_cache[merged_id])

    output_dir = os.path.dirname(path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    fieldnames = [
        "merged_id",
        "merge_size",
        "target_example_id",
        "paragraph_title",
        "chunk_index",
        "chunk_size",
        "chunk_utility",
        "gold_answer",
        "text",
    ]

    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_merged_instances(
    source_examples,
    compute_scores=True,
    use_score_cache=True,
    score_cache_path=CHUNK_UTILITIES_PATH,
):
    # We set a seed for reproducibility.
    random.seed(42)
    merged_instances = []
    cached_utilities = {}
    reused_cached_scores = 0
    computed_new_scores = 0

    if compute_scores and use_score_cache:
        cached_utilities = load_cached_chunk_utilities(score_cache_path)
        if cached_utilities:
            print(
                f"Loaded cached utility scores for {len(cached_utilities)} merged instances."
            )

    # Here we merge several examples together but keep only one question from one example.
    # This gives us a much larger context to compress.
    # For each merge size, we create 20 samples.
    for merge_size in MERGE_SIZES:
        for sample_index in range(SAMPLES_PER_MERGE_SIZE):
            target_example = random.choice(source_examples)
            target_support_pairs = get_supporting_fact_pairs(target_example)
            merged_id = f"merge_{merge_size}_{sample_index}"

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
                    for sentence_index, sentence in enumerate(sentence_groups[i]):
                        is_gold_sentence = (
                            example["id"] == target_example["id"]
                            and (title, sentence_index) in target_support_pairs
                        )

                        for chunk in split_by_period(sentence):
                            if chunk.strip() != "":
                                chunk_data = {
                                    "text": chunk.strip(),
                                    "chunk_size": len(chunk.split()),
                                    "chunk_utility": 0.0,
                                    "gold_answer": is_gold_sentence,
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

            instance = {
                "merged_id": merged_id,
                "merge_size": merge_size,
                "target_example_id": target_example["id"],
                "question": target_example["question"],
                "answer": target_example["answer"],
                "context": context,
            }

            cached_rows = cached_utilities.get(merged_id)
            if compute_scores and cached_rows and cached_rows_match_instance(cached_rows, instance):
                apply_cached_chunk_utilities(instance, cached_rows)
                reused_cached_scores += 1
            elif compute_scores:
                utilities = compute_utilities(
                    target_example["question"],
                    chunk_texts,
                    method="hybrid",
                    pct_semantic=PCT_SEMANTIC,
                    pct_lexical=PCT_LEXICAL,
                )
                for i, utility in enumerate(utilities):
                    chunk_refs[i]["chunk_utility"] = utility
                computed_new_scores += 1
                if (
                    use_score_cache
                    and computed_new_scores % SCORE_CACHE_CHECKPOINT_INTERVAL == 0
                ):
                    write_chunk_utility_cache(
                        merged_instances + [instance],
                        existing_cache=cached_utilities,
                        path=score_cache_path,
                    )
                    print(
                        "Checkpointed utility score cache after "
                        f"{computed_new_scores} newly scored instances."
                    )

            merged_instances.append(instance)
        print(f"Built {SAMPLES_PER_MERGE_SIZE} merged instances for merge size {merge_size}.")

    if compute_scores and use_score_cache:
        print(
            "Utility score cache summary: "
            f"reused {reused_cached_scores}, computed {computed_new_scores}."
        )
        if computed_new_scores > 0:
            write_chunk_utility_cache(
                merged_instances,
                existing_cache=cached_utilities,
                path=score_cache_path,
            )
            print(f"Updated utility score cache: {score_cache_path}")

    print(f"Built {len(merged_instances)} merged instances.")
    return merged_instances


def get_merged_instances(
    compute_scores=True,
    use_score_cache=True,
    score_cache_path=CHUNK_UTILITIES_PATH,
):
    print("Loading HotpotQA examples...")
    examples = load_hotpotqa_examples()
    print("Building merged instances...")
    return build_merged_instances(
        examples,
        compute_scores=compute_scores,
        use_score_cache=use_score_cache,
        score_cache_path=score_cache_path,
    )
