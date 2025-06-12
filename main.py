import asyncio
from agent.task_executor import TaskExecutor
from ax.ax_memory import AXMemory
from ax.ax_policy_engine import AXPolicyEngine
from ax.experience_logger import ExperienceLogger

import matplotlib.pyplot as plt

async def main():
    with open("websites.txt", "r") as file:
        websites = [line.strip() for line in file.readlines() if line.strip()]

    memory = AXMemory()
    policy = AXPolicyEngine(memory)
    executor = TaskExecutor(memory)

    metrics = []  # Store tuples of (url, method, success, time, friction)

    for url in websites:
        print(f"\n🔗 Processing: {url}")

        config = {
            "expect_form": "form" in url,
            "prefer_speed": not ("captcha" in url),
            "fill_forms": True
        }

        try:
            method = policy.decide(url, config)
            result = await executor.run(method, url, config)

            result.setdefault("time", 0.0)
            result.setdefault("friction", 2.0)
            result.setdefault("success", False)

            print(f"[LOG] {method.upper()} - Success: {result['success']}, Time: {result['time']}s, Friction: {result['friction']}")
            metrics.append((url, method, result["success"], result["time"], result["friction"]))

        except Exception as e:
            print(f"[ERROR] Failed to process {url}: {e}")
            metrics.append((url, method, False, 0.0, 2.0))

    # === PLOT METRICS ===
    urls, methods, successes, times, frictions = zip(*metrics)

    plt.figure()
    plt.barh(urls, times)
    plt.xlabel("Execution Time (s)")
    plt.title("Execution Time per Website")
    plt.tight_layout()
    plt.show()

    plt.figure()
    plt.barh(urls, frictions)
    plt.xlabel("Friction")
    plt.title("Friction per Website")
    plt.tight_layout()
    plt.show()

    method_usage = {m: methods.count(m) for m in set(methods)}
    plt.figure()
    plt.bar(method_usage.keys(), method_usage.values())
    plt.ylabel("Count")
    plt.title("Strategy Method Usage")
    plt.tight_layout()
    plt.show()

    success_rate = sum(successes) / len(successes) if successes else 0
    print(f"\n✅ Success Rate: {success_rate * 100:.1f}%")

if __name__ == "__main__":
    asyncio.run(main())
