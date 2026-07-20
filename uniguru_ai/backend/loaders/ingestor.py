import os
import json
import re
import sys
import time
from typing import List, Dict, Any

script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

from file_parser import FileParser


class KnowledgeIngestor:
    """
    Ingests files and builds a keyword-based runtime index.
    Saves artifacts under backend/knowledge/index/ by default.
    """

    def __init__(self, index_dir: str = "knowledge/index"):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if not os.path.isabs(index_dir):
            index_dir = os.path.join(base_dir, index_dir)

        self.index_dir = os.path.normpath(index_dir)
        self.parser = FileParser()
        self.index: Dict[str, List[Dict[str, Any]]] = {}
        self.ingestion_log: List[Dict[str, Any]] = []
        self._seen_content = set()

        if not os.path.exists(self.index_dir):
            os.makedirs(self.index_dir)

    def _clean_text(self, text: str) -> str:
        return re.sub(r"[^\w\s]", " ", text.lower())

    def _normalize_text(self, text: str) -> str:
        return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", text.lower())).strip()

    def _extract_keywords(self, text: str) -> List[str]:
        words = self._clean_text(text).split()
        return sorted({w for w in words if len(w) > 3})[:5]

    @staticmethod
    def _extract_frontmatter_value(content: str, key: str) -> str:
        match = re.search(r"---\s*(.*?)\s*---", content, flags=re.DOTALL)
        if not match:
            return ""
        header = match.group(1)
        for line in header.strip().splitlines():
            if ":" not in line:
                continue
            k, v = line.split(":", 1)
            if k.strip().lower() == key.lower():
                return v.strip()
        return ""

    @staticmethod
    def _normalize_path(path: str) -> str:
        normalized = os.path.normpath(path)
        return normalized.replace("\\", "/")

    def ingest_directory(self, directory: str, category: str = "general"):
        """Walks through a directory and ingests all supported files."""
        if not os.path.exists(directory):
            print(f"Directory {directory} does not exist. Skipping.")
            return

        print(f"Ingesting directory: {directory} (Category: {category})")

        for root, _, files in os.walk(directory):
            for file_name in files:
                file_path = os.path.join(root, file_name)
                result = self.parser.parse(file_path)
                if not result or not result.get("content"):
                    continue

                content = result["content"]
                metadata = result["metadata"]
                metadata["category"] = category
                status = str(
                    metadata.get("verification_status")
                    or self._extract_frontmatter_value(content, "verification_status")
                    or "UNSPECIFIED"
                ).upper()

                if status == "UNSPECIFIED" and category in ["jain", "swaminarayan", "gurukul"]:
                    status = "VERIFIED"

                base_keyword = os.path.splitext(file_name)[0].lower().replace("_", " ")
                metadata["verification_status"] = status
                metadata["title"] = str(metadata.get("title") or base_keyword.replace("_", " ").title()).strip()
                normalized_path = self._normalize_path(file_path)
                metadata["path"] = normalized_path
                metadata["source_lineage"] = {"original_path": normalized_path}
                metadata["ingested_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

                normalized_content = self._normalize_text(content)
                if not normalized_content or normalized_content in self._seen_content:
                    continue
                self._seen_content.add(normalized_content)

                self._add_to_index(base_keyword, content, metadata)

                dynamic_keywords = self._extract_keywords(base_keyword + " " + metadata["title"])
                for keyword in dynamic_keywords:
                    self._add_to_index(keyword, content, metadata)

                self.ingestion_log.append(
                    {
                        "path": normalized_path,
                        "category": category,
                        "verification_status": metadata.get("verification_status"),
                    }
                )

    def _add_to_index(self, keyword: str, content: str, metadata: Dict[str, Any]):
        if keyword not in self.index:
            self.index[keyword] = []

        normalized_content = self._normalize_text(content)
        existing_paths = [entry["metadata"]["path"] for entry in self.index[keyword]]
        existing_contents = {
            self._normalize_text(entry.get("content", ""))
            for entry in self.index[keyword]
        }

        if metadata["path"] in existing_paths or normalized_content in existing_contents:
            return

        self.index[keyword].append({"content": content, "metadata": metadata})

    def _build_runtime_summary(self) -> Dict[str, Any]:
        summary: Dict[str, Any] = {
            "documents_total": len(self.ingestion_log),
            "keywords_total": len(self.index),
            "categories": {},
            "verification_status": {},
        }

        for record in self.ingestion_log:
            category = record["category"]
            status = record["verification_status"]
            summary["categories"][category] = summary["categories"].get(category, 0) + 1
            summary["verification_status"][status] = summary["verification_status"].get(status, 0) + 1

        return summary

    def save_index(self):
        """Saves runtime index and ingestion manifest to disk."""
        index_file = os.path.join(self.index_dir, "master_index.json")
        with open(index_file, "w", encoding="utf-8") as f:
            json.dump(self.index, f, indent=2)

        manifest = {
            "summary": self._build_runtime_summary(),
            "ingestion_log": self.ingestion_log,
        }
        manifest_file = os.path.join(self.index_dir, "runtime_manifest.json")
        with open(manifest_file, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

        print(
            f"Index saved to {index_file} ({len(self.index)} keywords indexed). "
            f"Manifest saved to {manifest_file}."
        )


if __name__ == "__main__":
    ingestor = KnowledgeIngestor()

    ingestor.ingest_directory("backend/knowledge/quantum", category="quantum")
    ingestor.ingest_directory("backend/knowledge/gurukul", category="gurukul")
    ingestor.ingest_directory("backend/knowledge/jain", category="jain")
    ingestor.ingest_directory("backend/knowledge/swaminarayan", category="swaminarayan")
    ingestor.ingest_directory("backend/knowledge/programming", category="programming")
