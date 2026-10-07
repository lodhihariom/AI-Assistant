"""Chhota, free document-search (RAG) module. Koi extra API ya embedding model nahi chahiye."""
from io import BytesIO

from pypdf import PdfReader
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def extract_text(name: str, data: bytes) -> str:
    if name.lower().endswith(".pdf"):
        reader = PdfReader(BytesIO(data))
        return "\n".join((page.extract_text() or "") for page in reader.pages)
    return data.decode("utf-8", errors="ignore")


def chunk_text(text: str, size: int = 900, overlap: int = 150) -> list[str]:
    text = " ".join(text.split())
    chunks, i = [], 0
    while i < len(text):
        chunks.append(text[i : i + size])
        i += size - overlap
    return chunks


class DocIndex:
    def __init__(self, chunks: list[tuple[str, str]]):
        self.chunks = chunks  # (source_name, text)
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True)
        self.matrix = self.vectorizer.fit_transform([c[1] for c in chunks])

    def search(self, query: str, k: int = 4) -> list[tuple[str, str, float]]:
        scores = cosine_similarity(self.vectorizer.transform([query]), self.matrix).ravel()
        top = scores.argsort()[::-1][:k]
        return [(self.chunks[i][0], self.chunks[i][1], float(scores[i])) for i in top if scores[i] > 0]


def build_index(files: list[tuple[str, bytes]]) -> DocIndex | None:
    chunks: list[tuple[str, str]] = []
    for name, data in files:
        for c in chunk_text(extract_text(name, data)):
            chunks.append((name, c))
    return DocIndex(chunks) if chunks else None
