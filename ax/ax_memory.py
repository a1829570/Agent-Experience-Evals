import json
from pathlib import Path
from urllib.parse import urlparse

class AXMemory:
    def __init__(self, filepath='ax_memory.json'):
        self.filepath = Path(filepath)
        if self.filepath.exists():
            with self.filepath.open() as f:
                self.data = json.load(f)
        else:
            self.data = {"urls": {}, "categories": {}}
        self.url_log = self.data["urls"]

    def get(self, url):
        return self.url_log.get(url.lower(), {})

    def get_category_by_domain(self, url):
        domain = urlparse(url.lower()).netloc
        for category, domains in self.data["categories"].items():
            for known_domain in domains:
                if domain == known_domain:
                    return category
        return None

    def get_categories(self):
        return self.data["categories"]

    def get_domain_list_for_category(self, category):
        return list(self.data["categories"].get(category, {}).keys())

    def get_best_method_for_category(self, category):
        stats = self.data["categories"].get(category, {})
        if not stats:
            return None
        methods = {}
        for domain_stats in stats.values():
            for method, results in domain_stats.items():
                if method not in methods:
                    methods[method] = {"success": 0, "total": 0}
                methods[method]["success"] += sum(1 for r in results if r["success"])
                methods[method]["total"] += len(results)
        if not methods:
            return None
        return max(methods.items(), key=lambda x: x[1]["success"] / x[1]["total"])[0]

    def get_category_stats(self, category: str):
        return self.data["categories"].get(category, {})

    def log(self, url, method, result):
        if not result.get("success"):
            return  # Only log successful runs

        url = url.lower()
        domain = urlparse(url).netloc

        # Use provided category or infer
        category = result.get("category") or self.get_category_by_domain(url) or "uncategorized"
        result["category"] = category  # Ensure category is saved in the result

        # Log under URL index
        self.data["urls"][url] = {
            "method": method,
            "result": result
        }

        # Log under category-method-domain index
        self.data["categories"].setdefault(category, {}).setdefault(domain, {}).setdefault(method, []).append(result)

        with self.filepath.open("w") as f:
            json.dump(self.data, f, indent=2)
