import argparse
import os
import json
from datasets import load_dataset
from verl.utils.hdfs_io import copy, makedirs


def make_map_fn(split, data_source):
    def process_fn(example, idx):
        inputs = example.get('inputs')
        if isinstance(inputs, str):
            try:
                inputs = json.loads(inputs)
            except Exception:
                pass

        paper_content = ""
        if isinstance(inputs, list):
            for msg in inputs:
                if msg.get('role') == 'user':
                    paper_content = msg.get('content', '')
                    break

        if not paper_content:
            paper_content = str(inputs)

        rating = example.get('rating', [])
        decision = example.get('decision', 'N/A')
        outputs = example.get('outputs', '')
        reviewer_comments = example.get('reviewer_comments', '')

        return {
            "data_source": data_source,
            "ability": "review",
            "reward_model": {
                "style": "rule",
                "rating": rating,
                "decision": decision,
            },
            "prompt": [
                {
                    "role": "user",
                    "content": f"Please review the following academic paper:\n\n{paper_content}",
                }
            ],
            "extra_info": {
                "split": split,
                "index": idx,
                "id": example.get('id'),
                "year": example.get('year'),
                "reference_review": outputs,
            },
            "env_kwargs": {
                "paper_id": example.get('id'),
                "paper_text": paper_content,
                "question": paper_content,
                "user_goal": "Review the paper, track claims and supporting evidence, surface major flaws, and end with an accept or reject recommendation.",
                "data_source": data_source,
                "ground_truth_decision": decision,
                "reference_review": outputs,
                "reference_ratings": rating,
                "reviewer_comments": reviewer_comments,
            },
        }

    return process_fn


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--local_dir", default="~/data/drmas_review")
    parser.add_argument("--hdfs_dir", default=None)
    parser.add_argument("--subset_ratio", type=float, default=1.0, help="Percentage of dataset to process (0-1.0)")
    args = parser.parse_args()

    try:
        data_files = {
            "train": [
                "/reviewF/datasets/WestLakeNLP___deep_review-13_k/default/0.0.0/3db597e1e789ce04af98c5eae9e9430341face23/deep_review-13_k-train-00000-of-00005.arrow",
                "/reviewF/datasets/WestLakeNLP___deep_review-13_k/default/0.0.0/3db597e1e789ce04af98c5eae9e9430341face23/deep_review-13_k-train-00001-of-00005.arrow",
                "/reviewF/datasets/WestLakeNLP___deep_review-13_k/default/0.0.0/3db597e1e789ce04af98c5eae9e9430341face23/deep_review-13_k-train-00002-of-00005.arrow",
                "/reviewF/datasets/WestLakeNLP___deep_review-13_k/default/0.0.0/3db597e1e789ce04af98c5eae9e9430341face23/deep_review-13_k-train-00003-of-00005.arrow",
                "/reviewF/datasets/WestLakeNLP___deep_review-13_k/default/0.0.0/3db597e1e789ce04af98c5eae9e9430341face23/deep_review-13_k-train-00004-of-00005.arrow",
            ],
            "test": "/reviewF/datasets/WestLakeNLP___deep_review-13_k/default/0.0.0/3db597e1e789ce04af98c5eae9e9430341face23/deep_review-13_k-test.arrow",
        }
        dataset = load_dataset("arrow", data_files=data_files)
        train_ds = dataset["train"]
        test_ds = dataset["test"]
    except Exception as e:
        print(f"Error loading dataset: {e}")
        raise SystemExit(1)

    if args.subset_ratio < 1.0:
        n_train = max(1, int(len(train_ds) * args.subset_ratio))
        n_test = max(1, int(len(test_ds) * args.subset_ratio))
        train_ds = train_ds.shuffle(seed=42).select(range(n_train))
        test_ds = test_ds.shuffle(seed=42).select(range(n_test))
        print(f"Sampled {n_train} train examples and {n_test} test examples ({args.subset_ratio * 100}%)")

    train_ds = train_ds.map(function=make_map_fn("train", "deepreview13k"), with_indices=True)
    test_ds = test_ds.map(function=make_map_fn("test", "deepreview13k"), with_indices=True)

    local_dir = os.path.expanduser(args.local_dir)
    os.makedirs(local_dir, exist_ok=True)
    train_ds.to_parquet(os.path.join(local_dir, "train.parquet"))
    test_ds.to_parquet(os.path.join(local_dir, "test.parquet"))
    print(f"Dataset processed and saved to {local_dir}")

    if args.hdfs_dir is not None:
        makedirs(args.hdfs_dir)
        copy(src=local_dir, dst=args.hdfs_dir)
