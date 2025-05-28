import asyncio
import time
import json
from agent.task_executor import TaskExecutor
from ax.ax_memory import AXMemory
from ax.ax_policy_engine import AXPolicyEngine
from ax.experience_logger import ExperienceLogger

# Load websites list
with open("websites.txt") as f:
    websites = [line.strip() for line in f if line.strip()]

# Example user config (could be replaced with per-site config in the future)
config = {
    "expect_form": True,
    "prefer_speed": False,
    "fill_forms": True
}

async def main():
    memory = AXMemory()
    policy_engine = AXPolicyEngine(memory)
    executor = TaskExecutor()
    logger = ExperienceLogger()

    for url in websites:
        print(f"\n🔗 Processing: {url}")
        method = policy_engine.decide(url, config)
        print(f"🧠 AX chose method: {method}")

        start = time.time()
        result = await executor.run(method, url, config)
        duration = round(time.time() - start, 2)

        logger.log(url, method, result["success"], duration, result["friction"])
        memory.update(url, method, result["success"], duration)

if __name__ == "__main__":
    asyncio.run(main())
