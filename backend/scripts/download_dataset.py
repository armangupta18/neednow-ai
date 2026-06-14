from datasets import load_dataset

dataset = load_dataset(
    "McAuley-Lab/Amazon-Reviews-2023",
    "raw_review_Health_and_Personal_Care",
    split="train[:5000]"
)

dataset.to_json(
    "../datasets/products/health_reviews.jsonl"
)

print("Downloaded 5000 reviews")