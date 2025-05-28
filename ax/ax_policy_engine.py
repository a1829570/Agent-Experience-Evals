from ax.ax_memory import AXMemory

class AXPolicyEngine:
    def __init__(self, memory: AXMemory):
        self.memory = memory

    def decide(self, url: str, config: dict) -> str:
        """
        Return 'api', 'dom', or 'browser' based on past performance or default heuristic.
        """
        past = self.memory.get(url)

        if past:
            # Choose the method with highest average success rate
            sorted_methods = sorted(past.items(), key=lambda item: item[1]["success_rate"], reverse=True)
            return sorted_methods[0][0]  # method name

        # Heuristic fallback for unseen URLs
        if config.get("expect_form", False):
            return "browser"
        elif config.get("prefer_speed", True):
            return "api"
        else:
            return "dom"
