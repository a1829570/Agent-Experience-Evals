from agent.api_extractor import APIExtractor
from agent.dom_scraper import DOMScraper
from agent.browser_controller import BrowserController

class TaskExecutor:
    def __init__(self):
        self.api = APIExtractor()
        self.dom = DOMScraper()
        self.browser = BrowserController()

    async def run(self, method: str, url: str, config: dict) -> dict:
        result = {"success": False, "data": None, "friction": 0.0}

        try:
            if method == "api":
                result["data"] = await self.api.extract(url)
                result["success"] = result["data"] is not None
                result["friction"] = 0.2 if result["success"] else 1.0

            elif method == "dom":
                result["data"] = self.dom.scrape(url)
                result["success"] = result["data"] is not None
                result["friction"] = 0.5 if result["success"] else 1.5

            elif method == "browser":
                result["data"] = await self.browser.open(url, fill_forms=config.get("fill_forms", False))
                result["success"] = result["data"] is not None
                result["friction"] = 1.0 if result["success"] else 2.0

        except Exception as e:
            print(f"[ERROR] Method {method} failed on {url}: {str(e)}")

        return result
