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

    def get_category_by_domain(self, domain):
        """Returns the best-matching domain category for reuse."""
        # domain is the netloc (e.g. 'seek.com.au')
        for recorded_url in self.memory:
            recorded_domain = recorded_url.split('/')[2] if recorded_url.startswith("http") else recorded_url
            if domain in recorded_domain or recorded_domain in domain:
                return recorded_domain
        return None


    def get_best_method_for_category(self, category):
        from collections import defaultdict
        method_scores = defaultdict(lambda: {"success": 0, "total": 0, "friction": 0.0})

        for domain, data in self.memory.items():
            if data.get("category") != category:
                continue
            for method, attempts in data.get("methods", {}).items():
                for att in attempts:
                    method_scores[method]["total"] += 1
                    method_scores[method]["friction"] += att.get("friction", 0)
                    if att.get("success"):
                        method_scores[method]["success"] += 1

        if not method_scores:
            return "api"  # fallback

        # Choose method with highest success rate, break ties with lowest friction
        def method_rank(m):
            s = method_scores[m]
            return (s["success"] / s["total"], -s["friction"] / s["total"])

        return sorted(method_scores.keys(), key=method_rank, reverse=True)[0]

    
    """def get_best_method_for_category(self, domain):
        #Returns best method (based on success rate and lowest friction) for the matched domain.
        methods = self.memory.get(f"https://{domain}", {})
        best_method = None
        best_score = -1

        for method, stats in methods.items():
            count = stats.get("count", 1)
            success_count = stats.get("success_count", 0)
            total_time = stats.get("total_time", 1.0)

            success_rate = success_count / count
            friction = total_time / count
            score = success_rate - 0.1 * friction

            if score > best_score:
                best_score = score
                best_method = method

        return best_method or "api"
    """
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
