from agent.api_extractor import APIExtractor
from agent.dom_scraper import DOMScraper
from agent.browser_controller import BrowserController
from utils.llm_categorizer import categorize_content
from utils.llm_processor import process_web_content
from urllib.parse import urlparse
import time
import json

class TaskExecutor:
    def __init__(self, memory):
        self.api = APIExtractor()
        self.dom = DOMScraper()
        self.browser = BrowserController()
        self.memory = memory

    async def run(self, method: str, url: str, config: dict, tried=None) -> dict:
        if tried is None:
            tried = set()
        tried.add(method)

        result = {"success": False, "data": None, "friction": 1.0, "time": 0.0}
        start_time = time.time()

        try:
            if method == "api":
                result["data"] = await self.api.extract(url)
                result["success"] = result["data"] is not None
                result["friction"] = 0.2 if result["success"] else 1.0

            elif method == "dom":
                scraped_data = await self.dom.scrape(url)
                if isinstance(scraped_data, str):
                    result["data"] = scraped_data
                    result["success"] = True
                    result["friction"] = 0.5
                else:
                    result["data"] = None
                    result["success"] = False
                    result["friction"] = 1.5

            elif method == "browser":
                result["data"] = await self.browser.open(url, fill_forms=config.get("fill_forms", False))
                result["success"] = result["data"].get("success", False)
                result["friction"] = 1.0 if result["success"] else 2.0

        except Exception as e:
            print(f"[ERROR] Method {method} failed on {url}: {str(e)}")
            result["success"] = False

        end_time = time.time()
        result["time"] = round(end_time - start_time, 2)

        category = None
        strategy_from = "new"
        if result["success"] and result["data"]:
            try:
                data_str = result["data"]
                if isinstance(data_str, dict):
                    data_str = json.dumps(data_str)

                category = categorize_content(data_str)

                print("[INFO] Summarizing content via LLM...")
                summary = process_web_content(data_str)
                print(f"[SUMMARY]\n{summary}\n")

            except Exception as e:
                print(f"[WARN] Categorization or summary failed: {e}")

        if url in self.memory.url_log:
            strategy_from = "memory (exact URL)"
        elif category:
            stats = self.memory.get_category_stats(category)
            if stats:
                strategy_from = f"memory (category: {category})"

        print(f"[INFO] Using strategy: {method.upper()} — {strategy_from}")

        self.memory.log(url, method, {
            "success": result["success"],
            "friction": result["friction"],
            "time": result["time"],
            "category": category
        })

        if not result["success"]:
            fallback_methods = self.get_ranked_fallbacks(url, category, tried)
            for fallback in fallback_methods:
                print(f"[INFO] Trying fallback method: {fallback}")
                alt_result = await self.run(fallback, url, config, tried)
                if alt_result["success"]:
                    return alt_result

        return result

    def get_ranked_fallbacks(self, url, category, tried):
        methods = ["api", "dom", "browser"]
        if category:
            stats = self.memory.get_category_stats(category)
            return [m for m in sorted(stats, key=lambda m: (stats[m]["friction"], -stats[m]["success_rate"])) if m not in tried]
        return [m for m in methods if m not in tried]
