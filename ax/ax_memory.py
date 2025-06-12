import json
import os
from collections import defaultdict

class AXMemory:
    def __init__(self, path="results/ax_memory.json"):
        self.path = path
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.memory = self._load()

    def _load(self):
        if os.path.exists(self.path):
            with open(self.path, "r") as f:
                return json.load(f)
        return {}

    @property
    def url_log(self):
        return {k for k in self.memory if not k.startswith("_")}


    def save(self):
        with open(self.path, "w") as f:
            json.dump(self.memory, f, indent=2)

    def get(self, url):
        return self.memory.get(url)

    def update(self, url, method, success, time_taken):
        """Update individual URL-based performance metrics."""
        self.memory.setdefault(url, {})
        self.memory[url].setdefault(method, {
            "count": 0, "success_count": 0, "total_time": 0.0
        })

        stats = self.memory[url][method]
        stats["count"] += 1
        stats["success_count"] += int(success)
        stats["total_time"] += time_taken
        stats["success_rate"] = stats["success_count"] / stats["count"]
        stats["avg_time"] = stats["total_time"] / stats["count"]

    def log(self, url, method, result):
        """Unified logging for both URL and category-based memory."""
        self.update(url, method, result["success"], result["time"])

        category = result.get("category")
        if category:
            self._log_category(category, method, result["success"], result["time"])

        self.save()
    def _log_category(self, category, method, success, time_taken):
        """Update memory by content category."""
        self.memory.setdefault("_categories", {})
        self.memory["_categories"].setdefault(category, {})
        self.memory["_categories"][category].setdefault(method, {
            "count": 0, "success_count": 0, "total_time": 0.0
        })

        stats = self.memory["_categories"][category][method]
        stats["count"] += 1
        stats["success_count"] += int(success)
        stats["total_time"] += time_taken
        stats["success_rate"] = stats["success_count"] / stats["count"]
        stats["friction"] = stats["total_time"] / stats["count"]

    def get_category_stats(self, category):
        """Return success & friction stats for a content category."""
        fallback = {
            "api": {"success_rate": 0.0, "friction": 1.0},
            "dom": {"success_rate": 0.0, "friction": 1.5},
            "browser": {"success_rate": 0.0, "friction": 2.0}
        }
        return self.memory.get("_categories", {}).get(category, fallback)

    def has_url(self, url):
        return url in self.memory
