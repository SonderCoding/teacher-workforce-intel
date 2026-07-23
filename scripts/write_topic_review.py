import json
from pathlib import Path

from bertopic import BERTopic

OUT_DIR = Path("data/topics")


def main():
    topic_model = BERTopic.load("data/bertopic_model")
    assignments = json.loads((OUT_DIR / "assignments.json").read_text(encoding="utf-8"))
    assignments = {int(k): v for k, v in assignments.items()}
    raw_texts = json.loads((OUT_DIR / "raw_texts.json").read_text(encoding="utf-8"))
    raw_texts = {int(k): v for k, v in raw_texts.items()}

    topic_info = topic_model.get_topic_info()
    print("\n=== Topic Summary ===")
    print(topic_info.to_string())

    review_lines = []
    for _, row in topic_info.iterrows():
        topic_id = int(row["Topic"])
        if topic_id == -1:
            continue
        keywords = [w for w, _ in topic_model.get_topic(topic_id)][:8]
        example_id = next((pid for pid, tid in assignments.items() if tid == topic_id), None)
        review_lines.append(f"\nTopic {topic_id} (size {row['Count']})")
        review_lines.append(f"Keywords: {', '.join(keywords)}")
        review_lines.append(f"Example: {raw_texts.get(str(example_id), raw_texts.get(example_id, ''))}")

    review_text = "\n".join(review_lines)
    (OUT_DIR / "topic_review.txt").write_text(review_text, encoding="utf-8")
    print(f"\nWrote {OUT_DIR / 'topic_review.txt'}")


if __name__ == "__main__":
    main()