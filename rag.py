"""Chhota, free document-search (RAG) module. Koi extra API ya embedding model nahi chahiye."""
import re
from io import BytesIO
from pathlib import Path

from pypdf import PdfReader
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

KNOWLEDGE_DIRS = ["knowledge", "knowledge_cache"]


def extract_text(name: str, data: bytes) -> str:
    if name.lower().endswith(".pdf"):
        reader = PdfReader(BytesIO(data))
        return "\n".join((page.extract_text() or "") for page in reader.pages)
    return data.decode("utf-8", errors="ignore")


def chunk_text(text: str, size: int = 1000) -> list[str]:
    """Paragraph-aware chunking; markdown headings har chunk ke saath context ban kar jaate hain."""
    chunks, heading, buf = [], "", ""

    def flush():
        nonlocal buf
        if buf.strip():
            chunks.append((heading + "\n" + buf).strip() if heading else buf.strip())
        buf = ""

    for para in re.split(r"\n\s*\n", text):
        para = para.strip()
        if not para:
            continue
        if para.startswith("#"):
            first, _, rest = para.partition("\n")
            flush()
            heading = first.strip()
            para = rest.strip()
            if not para:
                continue
        while len(para) > size:  # bahut lambe paragraph ko todo
            flush()
            chunks.append((heading + "\n" + para[:size]).strip())
            para = para[size - 150 :]
        if len(buf) + len(para) > size:
            flush()
        buf += para + "\n\n"
    flush()
    return chunks


def _prep(t: str) -> str:
    """camelCase / snake_case ko bhi todo, taaki 'import bulk data' -> importBulkData match kare."""
    t = re.sub(r"[_$/]", " ", t)
    split = re.sub(r"([a-z])([A-Z])", r"\1 \2", t)
    return (t + " " + split).lower()


class DocIndex:
    def __init__(self, chunks: list[tuple[str, str]]):
        self.chunks = chunks  # (source_name, text)
        self.vectorizer = TfidfVectorizer(preprocessor=_prep, ngram_range=(1, 2), sublinear_tf=True)
        self.matrix = self.vectorizer.fit_transform([c[1] for c in chunks])

    def search(self, query: str, k: int = 4) -> list[tuple[str, str, float]]:
        scores = cosine_similarity(self.vectorizer.transform([query]), self.matrix).ravel()
        top = scores.argsort()[::-1][:k]
        return [(self.chunks[i][0], self.chunks[i][1], float(scores[i])) for i in top if scores[i] > 0]


def load_knowledge(dirs: list[str] = KNOWLEDGE_DIRS) -> list[tuple[str, str]]:
    """knowledge/*.md aur knowledge_cache/**/*.txt padho. 'SOURCE: url' pehli line source ka naam deti hai."""
    chunks: list[tuple[str, str]] = []
    for d in dirs:
        for p in sorted(Path(d).rglob("*")):
            if not p.is_file() or p.suffix.lower() not in {".md", ".txt"}:
                continue
            text = p.read_text(encoding="utf-8", errors="ignore")
            source = p.name
            if text.startswith("SOURCE:"):
                first, _, text = text.partition("\n")
                source = first.replace("SOURCE:", "").strip()
            chunks += [(source, c) for c in chunk_text(text)]
    return chunks


def chunks_from_files(files: list[tuple[str, bytes]]) -> list[tuple[str, str]]:
    return [(name, c) for name, data in files for c in chunk_text(extract_text(name, data))]


def build_index(chunks: list[tuple[str, str]]) -> DocIndex | None:
    return DocIndex(chunks) if chunks else None
