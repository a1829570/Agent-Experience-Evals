import json
import pandas as pd
import matplotlib.pyplot as plt
import os

# Load ground truth
ground_truth = pd.read_csv("ground_truth.csv")
ground_truth.set_index("url", inplace=True)

# Load AX memory results
with open("ax_memory.json", "r") as f:
    memory_data = json.load(f)

# Prepare lists for plotting
urls = []
successes = []
times = []
frictions = []
methods = []
memory_hits = []
method_sources = []
form_detections = []
categories_pred = []
categories_true = []
expected_methods = []
has_form_truth = []

for url, data in memory_data.get("results", {}).items():
    urls.append(url)
    methods.append(data.get("method"))
    result = data.get("result", {})
    successes.append(result.get("success", False))
    times.append(result.get("time", 0.0))
    frictions.append(result.get("friction", 2.0))
    memory_hits.append(result.get("memory_hit", False))
    method_sources.append(result.get("method_source", "unknown"))
    form_detections.append(result.get("form_detected", False))
    categories_pred.append(result.get("category", "unknown"))

    # Compare with ground truth
    gt = ground_truth.loc.get(url)
    if gt is not None:
        categories_true.append(gt["true_category"])
        expected_methods.append(gt["expected_method"])
        has_form_truth.append(gt["has_form"])
    else:
        categories_true.append("missing")
        expected_methods.append("unknown")
        has_form_truth.append(False)

# Plot output folder
os.makedirs("ax_graphs", exist_ok=True)

# Execution time per website
if urls:
    plt.figure(figsize=(10, len(urls)*0.25))
    plt.barh(urls, times, color='skyblue')
    plt.xlabel("Execution Time (s)")
    plt.title("Execution Time per Website")
    plt.tight_layout()
    plt.savefig("ax_graphs/execution_time.png")
    plt.close()

    # Friction per website
    plt.figure(figsize=(10, len(urls)*0.25))
    plt.barh(urls, frictions, color='salmon')
    plt.xlabel("Friction")
    plt.title("Friction per Website")
    plt.tight_layout()
    plt.savefig("ax_graphs/friction.png")
    plt.close()

# Method usage
method_counts = pd.Series(methods).value_counts()
if not method_counts.empty:
    method_counts.plot(kind='bar', color='lightgreen')
    plt.ylabel("Count")
    plt.title("Strategy Method Usage")
    plt.tight_layout()
    plt.savefig("ax_graphs/method_usage.png")
    plt.close()

# Success rate
success_rate = sum(successes) / len(successes) if successes else 0
print(f"✅ Success Rate: {success_rate * 100:.2f}%")

# Memory hit rate
memory_hit_rate = sum(memory_hits) / len(memory_hits) if memory_hits else 0
print(f"🧠 Memory Hit Rate: {memory_hit_rate * 100:.2f}%")

# Category classification accuracy
category_match = [pred == true for pred, true in zip(categories_pred, categories_true)]
cat_accuracy = sum(category_match) / len(category_match) if category_match else 0
print(f"📚 Category Accuracy: {cat_accuracy * 100:.2f}%")

# Method accuracy
method_match = [m == t for m, t in zip(methods, expected_methods)]
method_accuracy = sum(method_match) / len(method_match) if method_match else 0
print(f"🧪 Method Accuracy: {method_accuracy * 100:.2f}%")

# Form detection accuracy
form_match = [det == exp for det, exp in zip(form_detections, has_form_truth)]
form_accuracy = sum(form_match) / len(form_match) if form_match else 0
print(f"📝 Form Detection Accuracy: {form_accuracy * 100:.2f}%")

# Method latency by type
df = pd.DataFrame({"method": methods, "time": times})
if not df.empty:
    avg_times = df.groupby("method")["time"].mean()
    avg_times.plot(kind='bar', color='orange')
    plt.ylabel("Avg Time (s)")
    plt.title("Method Latency by Type")
    plt.tight_layout()
    plt.savefig("ax_graphs/method_latency.png")
    plt.close()
