# tests/performance/run_performance_tests.py
"""
Performance test runner with SLA reporting.
"""

import sys
import subprocess
import time
from pathlib import Path


def run_performance_tests():
    """Run all performance tests with timing"""
    
    test_dir = Path(__file__).parent
    
    print("=== InsightFlow Performance Test Suite ===\n")
    print("Testing SLA compliance:")
    print("- Routing P50 latency < 30ms")
    print("- Routing P99 latency < 100ms") 
    print("- Throughput > 1000 req/s")
    print("- Logging latency < 10ms")
    print("- Dashboard metrics < 100ms")
    print()
    
    start_time = time.time()
    
    # Run pytest with performance-specific options
    cmd = [
        sys.executable, "-m", "pytest",
        str(test_dir),
        "-v",
        "--tb=short",
        "--durations=10",  # Show 10 slowest tests
        "-x"  # Stop on first failure
    ]
    
    try:
        result = subprocess.run(cmd, check=False, capture_output=False)
        
        total_time = time.time() - start_time
        
        print(f"\n=== Performance Test Results ===")
        print(f"Total execution time: {total_time:.2f}s")
        
        if result.returncode == 0:
            print("✅ All performance SLAs met!")
        else:
            print("❌ Some performance SLAs failed!")
            print("Check output above for details.")
        
        return result.returncode
    
    except Exception as e:
        print(f"Error running performance tests: {e}")
        return 1


def run_benchmark():
    """Run performance benchmark"""
    
    print("=== Performance Benchmark ===\n")
    
    # Import here to avoid import issues
    from app.ml.weighted_scoring import WeightedScoringEngine
    import tempfile
    
    # Create temp config
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("""
scoring_weights:
  rule_based: 0.4
  feedback_based: 0.4
  availability: 0.2
""")
        config_path = f.name
    
    try:
        engine = WeightedScoringEngine(config_path)
        
        # Warmup
        for i in range(10):
            engine.calculate_confidence("agent-1", 0.8, 0.9, 0.85)
        
        # Benchmark
        iterations = 10000
        start = time.perf_counter()
        
        for i in range(iterations):
            engine.calculate_confidence(
                f"agent-{i % 10}",
                0.80 + (i % 20) / 100,
                0.85,
                0.90
            )
        
        total_time = time.perf_counter() - start
        avg_latency_ms = (total_time / iterations) * 1000
        throughput = iterations / total_time
        
        print(f"Benchmark Results:")
        print(f"- Iterations: {iterations}")
        print(f"- Total time: {total_time:.3f}s")
        print(f"- Average latency: {avg_latency_ms:.3f}ms")
        print(f"- Throughput: {throughput:.0f} req/s")
        
        # Check SLAs
        if avg_latency_ms < 1.0:
            print("✅ Average latency SLA met")
        else:
            print("❌ Average latency SLA failed")
        
        if throughput > 5000:
            print("✅ Throughput SLA met")
        else:
            print("❌ Throughput SLA failed")
    
    finally:
        import os
        os.unlink(config_path)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "benchmark":
        run_benchmark()
    else:
        exit_code = run_performance_tests()
        sys.exit(exit_code)