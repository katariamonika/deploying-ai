import os
import math
import json
from typing import List, Dict, Any


def _read_knowledge_file(path: str) -> List[str]:
    with open(path, "r", encoding="utf-8") as f:
        raw = f.read().strip()
    chunks = [c.strip() for c in raw.split("\n\n") if c.strip()]
    if not chunks:
        chunks = [line.strip() for line in raw.splitlines() if line.strip()]
    return chunks


def _tokenize(text: str) -> List[str]:
    text = text.lower()
    keep = []
    for ch in text:
        keep.append(ch if ch.isalnum() or ch.isspace() else " ")
    text = "".join(keep)
    return [t for t in text.split() if t]


def _cosine(a: Dict[str, float], b: Dict[str, float]) -> float:
    dot = 0.0
    for k, v in a.items():
        dot += v * b.get(k, 0.0)
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (na * nb)


class SemanticService:
    """
    Offline semantic-ish retrieval:
    - Builds TF-IDF vectors over your local knowledge chunks
    - Uses cosine similarity for ranking
    - Persists the index to a JSON file so it doesn't rebuild every run
    """
    def __init__(
        self,
        persist_path: str = "data/tfidf_index.json",
        knowledge_path: str = "data/ai_knowledge.txt",
    ):
        self.persist_path = persist_path
        self.knowledge_path = knowledge_path
        self._index: Dict[str, Any] = {}

    def ensure_index(self) -> Dict[str, Any]:
        if os.path.exists(self.persist_path):
            with open(self.persist_path, "r", encoding="utf-8") as f:
                self._index = json.load(f)
            return {"status": "ok", "action": "loaded", "indexed": len(self._index.get("docs", []))}

        docs = _read_knowledge_file(self.knowledge_path)
        tokenized = [_tokenize(d) for d in docs]

        df: Dict[str, int] = {}
        for toks in tokenized:
            for t in set(toks):
                df[t] = df.get(t, 0) + 1

        n = len(docs)
        idf: Dict[str, float] = {}
        for t, c in df.items():
            idf[t] = math.log((n + 1) / (c + 1)) + 1.0

        vectors: List[Dict[str, float]] = []
        for toks in tokenized:
            tf: Dict[str, int] = {}
            for t in toks:
                tf[t] = tf.get(t, 0) + 1
            vec: Dict[str, float] = {}
            for t, cnt in tf.items():
                vec[t] = (cnt / max(1, len(toks))) * idf.get(t, 0.0)
            vectors.append(vec)

        self._index = {"docs": docs, "vectors": vectors, "idf": idf}
        os.makedirs(os.path.dirname(self.persist_path), exist_ok=True)
        with open(self.persist_path, "w", encoding="utf-8") as f:
            json.dump(self._index, f)

        return {"status": "ok", "action": "indexed", "indexed": len(docs)}

    def query(self, user_query: str, k: int = 4) -> Dict[str, Any]:
        self.ensure_index()

        q_toks = _tokenize(user_query)
        tf: Dict[str, int] = {}
        for t in q_toks:
            tf[t] = tf.get(t, 0) + 1

        idf: Dict[str, float] = self._index.get("idf", {})
        q_vec: Dict[str, float] = {}
        for t, cnt in tf.items():
            q_vec[t] = (cnt / max(1, len(q_toks))) * idf.get(t, 0.0)

        docs: List[str] = self._index.get("docs", [])
        vecs: List[Dict[str, float]] = self._index.get("vectors", [])

        scored = []
        for i, dvec in enumerate(vecs):
            scored.append((i, _cosine(q_vec, dvec)))
        scored.sort(key=lambda x: x[1], reverse=True)

        results = []
        for idx, score in scored[: max(1, k)]:
            results.append({"text": docs[idx], "score": float(score)})

        return {"query": user_query, "results": results}