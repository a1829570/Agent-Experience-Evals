import json
import os
from datetime import datetime

class ExperienceLogger:
    def __init__(self, log_path="results/experience_log.json"):
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        self.log_path = log_path

    def log(self, url, method, success, time_taken, friction):
        record = {
            "timestamp": datetime.now().isoformat(),
            "url": url,
            "method": method,
            "success": success,
            "time_taken": time_taken,
            "friction": friction,
        }

        if not os.path.exists(self.log_path):
            with open(self.log_path, "w") as f:
                json.dump([record], f, indent=2)
        else:
            with open(self.log_path, "r+") as f:
                data = json.load(f)
                data.append(record)
                f.seek(0)
                json.dump(data, f, indent=2)

        print(f"[LOG] {method.upper()} - Success: {success}, Time: {time_taken}s, Friction: {friction}")
