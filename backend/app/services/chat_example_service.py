import json
import re
from functools import lru_cache
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parents[1] / "data" / "chat_examples.json"


@lru_cache(maxsize=1)
def load_chat_examples() -> list[dict]:
    if not DATA_FILE.exists():
        return []
    payload = json.loads(DATA_FILE.read_text(encoding="utf-8-sig"))
    return payload.get("examples", [])


def chat_example_stats() -> dict:
    examples = load_chat_examples()
    by_source: dict[str, int] = {}
    by_type: dict[str, int] = {}
    for example in examples:
        source = example.get("source_file") or "unknown"
        source_type = example.get("source_type") or "unknown"
        by_source[source] = by_source.get(source, 0) + 1
        by_type[source_type] = by_type.get(source_type, 0) + 1
    return {"total": len(examples), "by_source": by_source, "by_type": by_type}


def retrieve_chat_examples(question: str, context: str, limit: int = 4) -> list[dict]:
    examples = load_chat_examples()
    if not examples:
        return []

    query_tokens = _tokens(f"{question} {context}")
    ranked = []
    for example in examples:
        text = _example_text(example)
        score = _score(query_tokens, text)
        if score > 0:
            ranked.append((score, example))

    if not ranked:
        return examples[:limit]
    return [example for _, example in sorted(ranked, key=lambda item: item[0], reverse=True)[:limit]]


def format_chat_examples(examples: list[dict]) -> str:
    blocks = []
    for index, example in enumerate(examples, start=1):
        category = example.get("category") or "general"
        if example.get("messages"):
            turns = "\n".join(
                f"{message.get('role', 'user')}: {message.get('content', '')}"
                for message in example["messages"]
            )
        else:
            turns = example.get("dialogue") or ""
        suggestion = example.get("suggestion")
        if suggestion:
            turns = f"{turns}\nPreferred correction: {suggestion}"
        blocks.append(f"Example {index} ({category}):\n{turns}")
    return "\n\n".join(blocks)


def _example_text(example: dict) -> str:
    parts = [example.get("category") or "", example.get("dialogue") or "", example.get("suggestion") or ""]
    for message in example.get("messages") or []:
        parts.append(message.get("content") or "")
    return " ".join(parts)


def _tokens(text: str) -> set[str]:
    lowered = text.lower()
    word_tokens = set(re.findall(r"[\w\u4e00-\u9fff]{2,}", lowered))
    chinese_chars = [char for char in lowered if "\u4e00" <= char <= "\u9fff"]
    bigrams = {a + b for a, b in zip(chinese_chars, chinese_chars[1:])}
    return word_tokens | bigrams


def _score(query_tokens: set[str], text: str) -> int:
    haystack = text.lower()
    return sum(1 for token in query_tokens if token in haystack)
