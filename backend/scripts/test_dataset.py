import json

path = "datasets/products/meta_Health_and_Personal_Care.jsonl"

count = 0

with open(path, "r") as f:
    for line in f:
        obj = json.loads(line)
        print(obj.keys())
        print(obj)
        break

print("Dataset loaded successfully")