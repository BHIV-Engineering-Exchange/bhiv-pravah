import json
import hashlib
from typing import List, Dict, Any
import divergence_engine as de
import truth_classifier as tc

def deterministic_cluster(signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Clusters signals deterministically based on their topic_id.
    Includes structural divergence and truth level mapping (Day 2).
    """
    clusters_map = {}
    
    # Group signals by topic_id
    for signal in signals:
        topic_id = signal.get("topic_id")
        if not topic_id:
            continue
            
        if topic_id not in clusters_map:
            clusters_map[topic_id] = []
        clusters_map[topic_id].append(signal)
    
    output_clusters = []
    sorted_topics = sorted(clusters_map.keys())
    
    for topic_id in sorted_topics:
        cluster_signals = clusters_map[topic_id]
        
        # Sort signals by signal_id for byte-for-byte identity
        cluster_signals.sort(key=lambda s: s.get("signal_id", ""))
        
        # Day 2: Compute Divergence and Truth Level
        div_score = de.compute_divergence(cluster_signals)
        truth_level = tc.classify_truth_level(cluster_signals, div_score)
        contra_map = de.generate_contradiction_map(cluster_signals)
        
        cluster_data = {
            "cluster_id": f"cluster-{topic_id}",
            "topic_id": topic_id,
            "signals": cluster_signals,
            "divergence_score": div_score,
            "truth_level": truth_level,
            "contradiction_map": contra_map,
            "registry_reference": f"bhiv://registry/cluster/{topic_id}"
        }
        
        # Day 3 Requirement: Deterministic Hash (Calculated from final structured data)
        cluster_json = json.dumps(cluster_data, sort_keys=True)
        cluster_data["deterministic_hash"] = hashlib.sha256(cluster_json.encode('utf-8')).hexdigest()
        
        output_clusters.append(cluster_data)
        
    return output_clusters

if __name__ == "__main__":
    with open("example_input.json", "r") as f:
        data = json.load(f)
        
    clusters = deterministic_cluster(data.get("signals", []))
    print(json.dumps(clusters, indent=2))
