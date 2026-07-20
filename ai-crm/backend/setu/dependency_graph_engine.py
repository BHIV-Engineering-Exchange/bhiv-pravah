class DependencyGraphEngine:
    def __init__(self):
        self.nodes = {}
        self.dependencies = {}
        self.reverse_dependencies = {}

    def add_node(self, node):
        if not node or not node.get("id"):
            raise ValueError("Node id is required")

        existing = self.nodes.get(node["id"], {})
        normalized = {
            "id": node["id"],
            "status": node.get("status") or existing.get("status") or "pending",
            "impact_weight": node.get("impact_weight", existing.get("impact_weight", 1)),
            "tenant_id": node.get("tenant_id", existing.get("tenant_id")),
            "metadata": node.get("metadata") or existing.get("metadata") or {}
        }

        self.nodes[node["id"]] = normalized
        self.dependencies.setdefault(node["id"], set())
        self.reverse_dependencies.setdefault(node["id"], set())
        return normalized

    def add_dependency(self, prerequisite_id, dependent_id):
        self.add_node({"id": prerequisite_id})
        self.add_node({"id": dependent_id})

        self.dependencies[prerequisite_id].add(dependent_id)
        self.reverse_dependencies[dependent_id].add(prerequisite_id)

    def _get_downstream(self, start_id):
        visited = set()
        queue = [start_id]
        while queue:
            current = queue.pop(0)
            for next_id in self.dependencies.get(current, set()):
                if next_id not in visited:
                    visited.add(next_id)
                    queue.append(next_id)
        return list(visited)

    def _get_upstream(self, start_id):
        visited = set()
        queue = [start_id]
        while queue:
            current = queue.pop(0)
            for next_id in self.reverse_dependencies.get(current, set()):
                if next_id not in visited:
                    visited.add(next_id)
                    queue.append(next_id)
        return list(visited)

    def propagate_blockage(self, start_id, reason="blocked"):
        impacted = [start_id] + self._get_downstream(start_id)
        updates = []
        for node_id in impacted:
            node = self.nodes.get(node_id)
            if not node:
                continue
            node["status"] = "blocked"
            node["metadata"] = {**node.get("metadata", {}), "blocked_reason": reason}
            updates.append({"id": node_id, "status": node["status"], "reason": reason})
        return updates

    def detect_bottlenecks(self, limit=5):
        scored = []
        for node in self.nodes.values():
            downstream_count = len(self._get_downstream(node["id"]))
            upstream_count = len(self._get_upstream(node["id"]))
            score = (downstream_count + 1) * (node.get("impact_weight", 1)) + upstream_count * 0.5
            scored.append({
                "id": node["id"],
                "score": score,
                "downstreamCount": downstream_count,
                "upstreamCount": upstream_count
            })
        scored.sort(key=lambda item: item["score"], reverse=True)
        return scored[:limit]

    def analyze_dependency_chain(self, node_id):
        return {
            "node_id": node_id,
            "upstream": self._get_upstream(node_id),
            "downstream": self._get_downstream(node_id)
        }

    def calculate_operational_impact(self):
        node_scores = []
        total_score = 0
        for node in self.nodes.values():
            if node.get("status") != "blocked":
                continue
            downstream_count = len(self._get_downstream(node["id"]))
            score = (downstream_count + 1) * (node.get("impact_weight", 1))
            total_score += score
            node_scores.append({
                "id": node["id"],
                "score": score,
                "downstreamCount": downstream_count
            })
        node_scores.sort(key=lambda item: item["score"], reverse=True)
        return {"total_score": total_score, "node_scores": node_scores}

    def generate_escalation_recommendations(self, impact_report, options=None):
        options = options or {}
        high_threshold = options.get("highThreshold", 10)
        medium_threshold = options.get("mediumThreshold", 5)

        recommendations = []
        for node in impact_report.get("node_scores", []):
            recommendation = "monitor"
            if node["score"] >= high_threshold:
                recommendation = "escalate_immediately"
            elif node["score"] >= medium_threshold:
                recommendation = "escalate_within_window"
            recommendations.append({
                "node_id": node["id"],
                "score": node["score"],
                "recommendation": recommendation
            })
        return recommendations
