import re
from urllib.parse import urlparse
from utils.llm_categorizer import categorize_content

class AXPolicyEngine:
    def __init__(self, memory):
        self.memory = memory

    def decide(self, url: str, config: dict) -> str:
        print(f"[DEBUG] 🔍 Entering AXPolicyEngine.decide for URL: {url}")

        # STEP 1: Exact URL match
        if url.lower() in self.memory.url_log:
            method = self.memory.url_log[url.lower()]["method"]
            print(f"[DEBUG] ✅ Step 1 - Exact URL match found: {method}")
            return method

        # Extract domain
        domain = urlparse(url).netloc
        print(f"[DEBUG] 🌐 Extracted domain: {domain}")

        # STEP 2: Check for domain match
        category = self.memory.get_category_by_domain(domain)
        if category:
            best_method = self.memory.get_best_method_for_category(category)
            print(f"[DEBUG] ✅ Step 2 - Domain match: category='{category}', method='{best_method}'")
            if best_method:
                return best_method

        # STEP 3: Use LLM to infer similar category based on domain
        print(f"[DEBUG] 🤖 Step 3 - No exact domain match. Attempting LLM similarity on domain")
        html = f"<html><body>{domain}</body></html>"
        category = categorize_content(html)
        best_method = self.memory.get_best_method_for_category(category)
        if best_method:
            print(f"[DEBUG] ✅ Step 3 - LLM-inferred category='{category}', method='{best_method}'")
            return best_method

        # STEP 4: No match found, full pipeline fallback
        print(f"[DEBUG] ❌ Step 4 - No prior memory match. Proceed with full pipeline")
        return "pipeline"