export class DependencyGraphEngine {
  constructor() {
    this.nodes = new Map();
    this.dependencies = new Map();
    this.reverseDependencies = new Map();
  }

  addNode(node) {
    if (!node?.id) {
      throw new Error('Node id is required');
    }

    const existing = this.nodes.get(node.id) || {};
    const normalized = {
      id: node.id,
      status: node.status || existing.status || 'pending',
      impact_weight: node.impact_weight ?? existing.impact_weight ?? 1,
      tenant_id: node.tenant_id || existing.tenant_id || null,
      metadata: node.metadata || existing.metadata || {}
    };

    this.nodes.set(node.id, normalized);
    if (!this.dependencies.has(node.id)) {
      this.dependencies.set(node.id, new Set());
    }
    if (!this.reverseDependencies.has(node.id)) {
      this.reverseDependencies.set(node.id, new Set());
    }
    return normalized;
  }

  addDependency(prerequisiteId, dependentId) {
    this.addNode({ id: prerequisiteId });
    this.addNode({ id: dependentId });

    this.dependencies.get(prerequisiteId).add(dependentId);
    this.reverseDependencies.get(dependentId).add(prerequisiteId);
  }

  getDownstream(startId) {
    const visited = new Set();
    const queue = [startId];
    while (queue.length > 0) {
      const current = queue.shift();
      const downstream = this.dependencies.get(current) || new Set();
      downstream.forEach((next) => {
        if (!visited.has(next)) {
          visited.add(next);
          queue.push(next);
        }
      });
    }
    return Array.from(visited);
  }

  getUpstream(startId) {
    const visited = new Set();
    const queue = [startId];
    while (queue.length > 0) {
      const current = queue.shift();
      const upstream = this.reverseDependencies.get(current) || new Set();
      upstream.forEach((next) => {
        if (!visited.has(next)) {
          visited.add(next);
          queue.push(next);
        }
      });
    }
    return Array.from(visited);
  }

  propagateBlockage(startId, reason = 'blocked') {
    const impacted = [startId, ...this.getDownstream(startId)];
    const updates = [];

    impacted.forEach((nodeId) => {
      const node = this.nodes.get(nodeId);
      if (!node) {
        return;
      }
      node.status = 'blocked';
      node.metadata = { ...node.metadata, blocked_reason: reason };
      updates.push({ id: nodeId, status: node.status, reason });
    });

    return updates;
  }

  detectBottlenecks(limit = 5) {
    const scored = Array.from(this.nodes.values()).map((node) => {
      const downstreamCount = this.getDownstream(node.id).length;
      const upstreamCount = this.getUpstream(node.id).length;
      const score = (downstreamCount + 1) * (node.impact_weight || 1) + upstreamCount * 0.5;
      return { id: node.id, score, downstreamCount, upstreamCount };
    });

    return scored.sort((a, b) => b.score - a.score).slice(0, limit);
  }

  analyzeDependencyChain(nodeId) {
    return {
      node_id: nodeId,
      upstream: this.getUpstream(nodeId),
      downstream: this.getDownstream(nodeId)
    };
  }

  calculateOperationalImpact() {
    const nodeScores = [];
    let totalScore = 0;

    this.nodes.forEach((node) => {
      if (node.status !== 'blocked') {
        return;
      }
      const downstreamCount = this.getDownstream(node.id).length;
      const score = (downstreamCount + 1) * (node.impact_weight || 1);
      totalScore += score;
      nodeScores.push({ id: node.id, score, downstreamCount });
    });

    nodeScores.sort((a, b) => b.score - a.score);

    return {
      total_score: totalScore,
      node_scores: nodeScores
    };
  }

  generateEscalationRecommendations(impactReport, options = {}) {
    const highThreshold = options.highThreshold || 10;
    const mediumThreshold = options.mediumThreshold || 5;

    return impactReport.node_scores.map((node) => {
      let recommendation = 'monitor';
      if (node.score >= highThreshold) {
        recommendation = 'escalate_immediately';
      } else if (node.score >= mediumThreshold) {
        recommendation = 'escalate_within_window';
      }

      return {
        node_id: node.id,
        score: node.score,
        recommendation
      };
    });
  }
}
