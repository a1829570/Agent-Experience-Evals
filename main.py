# --- main.py ---
import asyncio
from agent.task_executor import TaskExecutor
from ax.ax_memory import AXMemory
from ax.ax_policy_engine import AXPolicyEngine
from ax.experience_logger import ExperienceLogger
from urllib.parse import urlparse
import matplotlib.pyplot as plt

async def main():
    with open("websites.txt", "r") as file:
        websites = [line.strip() for line in file.readlines() if line.strip()]

    memory = AXMemory()
    policy = AXPolicyEngine(memory)
    executor = TaskExecutor(memory)

    metrics = []

    for url in websites:
        print(f"\n🔗 Processing: {url}")

        config = {
            "expect_form": "form" in url,
            "prefer_speed": not ("captcha" in url),
            "fill_forms": True
        }

        try:
            url_result = memory.get(url)
            if url_result and url_result.get("result", {}).get("success"):
                method = url_result["method"]
                print(f"[INFO] Reusing previous successful method: {method} for {url}")
            else:
                category = memory.get_category_by_domain(url)
                if category:
                    print(f"[INFO] Found similar domain category: {category}")
                    method = memory.get_best_method_for_category(category)
                    print(f"[INFO] Using best method for category: {method}")
                else:
                    method = policy.decide(url, config)

            result = await executor.run(method, url, config)

            # Ensure defaults
            result.setdefault("time", 0.0)
            result.setdefault("friction", 2.0)
            result.setdefault("success", False)

            final_method = result.get("final_method", method)

            """if result["success"]:
                memory.log(url, final_method, {
                    "success": result["success"],
                    "time": result["time"],
                    "category": category
                })"""

            print(f"[LOG] {final_method.upper()} - Success: {result['success']}, Time: {result['time']}s, Friction: {result['friction']}")
            metrics.append((url, final_method, result["success"], result["time"], result["friction"]))

        except Exception as e:
            print(f"[ERROR] Failed to process {url}: {e}")
            metrics.append((url, method if 'method' in locals() else 'unknown', False, 0.0, 2.0))

    # === PLOT METRICS ===
    urls, methods, successes, times, frictions = zip(*metrics)

    import os
    os.makedirs("graphs", exist_ok=True)

    plt.figure(figsize=(10, len(urls) * 0.25))
    plt.barh(urls, times, color='skyblue')
    plt.xlabel("Execution Time (s)")
    plt.title("Execution Time per Website")
    plt.tight_layout()
    plt.savefig("graphs/execution_time.png")

    plt.figure(figsize=(15, len(urls) * 0.4))
    plt.barh(urls, frictions, color='salmon')
    plt.xlabel("Friction")
    plt.title("Friction per Website")
    plt.tight_layout()
    plt.savefig("graphs/friction.png")

    method_usage = {m: methods.count(m) for m in set(methods)}
    plt.figure(figsize=(8, 6))
    plt.bar(method_usage.keys(), method_usage.values(), color='lightgreen')
    plt.ylabel("Count")
    plt.title("Strategy Method Usage")
    plt.tight_layout()
    plt.savefig("graphs/method_usage.png")

    success_rate = sum(successes) / len(successes) if successes else 0
    print(f"\n✅ Success Rate: {success_rate * 100:.1f}%")

if __name__ == "__main__":
    asyncio.run(main())
