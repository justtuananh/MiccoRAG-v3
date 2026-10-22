"""Copy two live Chroma collections into an isolated evaluation server.

Reads only from source; destination must use a different port and is modified.
Run inside the isolated VPS staging context after the destination server starts.
"""
import argparse
import hashlib

import chromadb


def copy_collection(source, target, name: str, batch_size: int = 100) -> None:
    original = source.get_collection(name)
    copied = target.get_or_create_collection(name, metadata=original.metadata)
    expected = original.count()
    digest = hashlib.sha256()
    for offset in range(0, expected, batch_size):
        rows = original.get(
            limit=batch_size,
            offset=offset,
            include=["documents", "metadatas", "embeddings"],
        )
        ids = rows["ids"]
        if not ids:
            continue
        embeddings = rows["embeddings"]
        copied.upsert(
            ids=ids,
            documents=rows["documents"],
            metadatas=rows["metadatas"],
            embeddings=embeddings.tolist() if hasattr(embeddings, "tolist") else embeddings,
        )
        for row_id, content in zip(ids, rows["documents"]):
            digest.update(row_id.encode())
            digest.update((content or "").encode())
    actual = copied.count()
    if actual != expected:
        raise RuntimeError(f"{name}: expected {expected} chunks, found {actual}")
    print(f"{name}: copied {actual} chunks; source content digest {digest.hexdigest()}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-port", type=int, default=8003)
    parser.add_argument("--target-port", type=int, default=18003)
    args = parser.parse_args()
    if args.source_port == args.target_port:
        parser.error("Source and destination ports must differ")
    source = chromadb.HttpClient(host="127.0.0.1", port=args.source_port)
    target = chromadb.HttpClient(host="127.0.0.1", port=args.target_port)
    for name in ("kb_9", "kb_11"):
        copy_collection(source, target, name)


if __name__ == "__main__":
    main()
