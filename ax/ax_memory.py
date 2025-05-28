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

    def save(self):
        with open(self.path, "w") as f:
            json.dump(self.memory, f, indent=2)

    def get(self, url):
        return self.memory.get(url)

    def update(self, url, method, success, time_taken):
        if url not in self.memory:
            self.memory[url] = defaultdict(lambda: {"count": 0, "success_count": 0, "total_time": 0.0})

        if method not in self.memory[url]:
            self.memory[url][method] = {"count": 0, "success_count": 0, "total_time": 0.0}

        entry = self.memory[url][method]
        entry["count"] += 1
        entry["success_count"] += int(success)
        entry["total_time"] += time_taken

        entry["success_rate"] = entry["success_count"] / entry["count"]
        entry["avg_time"] = entry["total_time"] / entry["count"]

        self.save()
