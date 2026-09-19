"""Confidence-aware scoring: 1 is a guess, 5 is an asserted mastery claim."""
from collections import defaultdict
from typing import Iterable


def answer_score(correct: bool, confidence: int) -> float:
    """Return 0..100 mastery evidence for one response.

    Correct low-confidence answers yield 60%, avoiding a lucky-guess overclaim.
    Wrong high-confidence answers yield a 30-point misconception penalty.
    """
    confidence = max(1, min(5, confidence))
    if correct:
        return 50 + 10 * confidence
    return max(0, 50 - 10 * confidence)


def score_submission(questions: Iterable[dict], answers: Iterable[dict], previous: dict[str, float] | None = None) -> dict:
    question_map = {q["id"]: q for q in questions}
    grouped: dict[str, list[float]] = defaultdict(list)
    details = []
    for answer in answers:
        question = question_map.get(answer["question_id"])
        if not question:
            continue
        correct = answer["selected_index"] == question["answer_index"]
        evidence = answer_score(correct, answer["confidence"])
        grouped[question["topic"]].append(evidence)
        details.append({"question_id": question["id"], "topic": question["topic"], "correct": correct, "evidence": evidence})
    previous = previous or {}
    topic_scores = {}
    for topic, values in grouped.items():
        current = round(sum(values) / len(values), 1)
        topic_scores[topic] = round(0.6 * current + 0.4 * float(previous.get(topic, current)), 1)
    overall = round(sum(topic_scores.values()) / max(1, len(topic_scores)), 1)
    return {"overall": overall, "topic_scores": topic_scores, "details": details}
