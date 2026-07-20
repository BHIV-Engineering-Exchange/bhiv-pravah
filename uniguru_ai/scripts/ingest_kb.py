import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from uniguru.loaders.ingestor import KnowledgeIngestor


def main() -> None:
    ingestor = KnowledgeIngestor(index_dir="backend/uniguru/knowledge/index")
    ingestor.ingest_directory("backend/uniguru/knowledge/quantum", category="quantum")
    ingestor.ingest_directory("backend/uniguru/knowledge/gurukul", category="gurukul")
    ingestor.ingest_directory("backend/uniguru/knowledge/jain", category="jain")
    ingestor.ingest_directory("backend/uniguru/knowledge/swaminarayan", category="swaminarayan")
    ingestor.save_index()


if __name__ == "__main__":
    main()
