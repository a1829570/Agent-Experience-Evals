from ax.ax_memory import AXMemory
from urllib.parse import urlparse


class AXPolicyEngine:
    def __init__(self, memory: AXMemory):
        self.memory = memory

    def decide(self, url: str, config: dict) -> str:
        # Step 1: Check if URL has past data
        past = self.memory.get(url)
        if past:
            sorted_methods = sorted(past.items(), key=lambda item: item[1]["success_rate"], reverse=True)
            return sorted_methods[0][0]

        # Step 2: Category-level decision
        try:
            domain = urlparse(url).netloc
            dummy_html = f"<html><body>{domain}</body></html>"
            category = categorize_content(dummy_html)
            cat_stats = self.memory.get_category_stats(category)

            ranked = sorted(cat_stats.items(), key=lambda item: (item[1]["friction"], -item[1]["success_rate"]))
            return ranked[0][0]
        except Exception as e:
            print(f"[WARN] Could not use category-based decision: {str(e)}")

        # Step 3: Heuristic fallback
        if config.get("expect_form", False):
            return "browser"
        elif config.get("prefer_speed", True):
            return "api"
        else:
            return "dom"