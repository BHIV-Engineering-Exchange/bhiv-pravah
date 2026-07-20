from intelligence.engine.task_intelligence_engine import TaskIntelligenceEngine


engine = TaskIntelligenceEngine()


review = {
    "score": 60,
    "missing": [],
    "track": "backend"
}


print(engine.generate_next_task(review))
print(engine.generate_next_task(review))
print(engine.generate_next_task(review))