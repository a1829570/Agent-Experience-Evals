
from ax.ax_memory import AXMemory
from urllib.parse import urlparse
from utils.llm_categorizer import categorize_content

class AXPolicyEngine:
    def __init__(self, memory: AXMemory):
        self.memory = memory

    def decide(self, url: str, config: dict) -> str:
        domain = urlparse(url).netloc
        category = self.memory.get_category_by_domain(domain)

        # If not found, classify using LLM
        if not category:
            html = f"<html><body>{domain}</body></html>"
            category = categorize_content(html)

            if category:
                # Register new domain under inferred category
                self.memory.data["categories"].setdefault(category, {}).setdefault(domain, {})

        if category:
            best_method = self.memory.get_best_method_for_category(category)
            if best_method:
                return best_method


        try:
            dummy_html = f"<html><body>{domain}</body></html>"
            category = categorize_content(dummy_html)
            cat_stats = self.memory.get_category_stats(category)

            methods = {}
            for domain_stats in cat_stats.values():
                for method, results in domain_stats.items():
                    if method not in methods:
                        methods[method] = {"success": 0, "total": 0}
                    methods[method]["success"] += sum(1 for r in results if r.get("success"))
                    methods[method]["total"] += len(results)

            if not methods:
                raise ValueError("No historical method data")

            ranked = sorted(methods.items(), key=lambda item: (item[1]["success"] / item[1]["total"]), reverse=True)
            return ranked[0][0]
        except Exception as e:
            print(f"[WARN] Could not use category-based decision: {str(e)}")

        if config.get("expect_form", False):
            return "browser"
        elif config.get("prefer_speed", True):
            return "api"
        else:
            return "dom"
