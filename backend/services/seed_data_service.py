import asyncio
import hashlib
import logging
import random
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Tuple

from database import supabase

logger = logging.getLogger(__name__)

DEMO_PRODUCT_NAME = "Sentinel Demo Earbuds"
PLATFORMS = ["amazon", "youtube", "reddit", "twitter"]
ASPECTS = ["Price", "Quality", "Delivery", "Support", "Battery", "Sound"]
EMOTION_BY_LABEL = {
    "POSITIVE": "joy",
    "NEGATIVE": "anger",
    "NEUTRAL": "neutral",
}

POSITIVE_TEMPLATES = [
    "Great {aspect} overall. I have used it for a week and it keeps performing well.",
    "Excellent value for money. The {aspect} exceeded my expectations.",
    "Really happy with this purchase. Strong {aspect} and smooth daily usage.",
    "Impressed so far. {aspect} is better than other products in this range.",
]

NEGATIVE_TEMPLATES = [
    "Disappointed with the {aspect}. It feels inconsistent and needs improvement.",
    "The {aspect} is weak compared to what was advertised.",
    "Not satisfied. The {aspect} caused repeated frustration during normal use.",
    "I expected better. {aspect} quality dropped after a short period.",
]

NEUTRAL_TEMPLATES = [
    "Average experience so far. The {aspect} is acceptable but nothing special.",
    "The product works, but {aspect} could be improved in future updates.",
    "Decent for regular use. {aspect} is okay for the price segment.",
    "Mixed feelings. {aspect} is manageable, though not consistently good.",
]


def _build_review_text(label: str, aspect: str, index: int, rng: random.Random) -> str:
    if label == "POSITIVE":
        template = rng.choice(POSITIVE_TEMPLATES)
    elif label == "NEGATIVE":
        template = rng.choice(NEGATIVE_TEMPLATES)
    else:
        template = rng.choice(NEUTRAL_TEMPLATES)

    return f"{template.format(aspect=aspect)} [seed-{index}]"


def _pick_label(rng: random.Random) -> str:
    roll = rng.random()
    if roll < 0.56:
        return "POSITIVE"
    if roll < 0.78:
        return "NEUTRAL"
    return "NEGATIVE"


def _score_for_label(label: str, rng: random.Random) -> float:
    if label == "POSITIVE":
        return round(rng.uniform(0.72, 0.97), 4)
    if label == "NEGATIVE":
        return round(rng.uniform(0.08, 0.36), 4)
    return round(rng.uniform(0.45, 0.62), 4)


def _credibility_for_label(label: str, rng: random.Random) -> float:
    if label == "POSITIVE":
        return round(rng.uniform(0.78, 0.96), 4)
    if label == "NEGATIVE":
        return round(rng.uniform(0.55, 0.88), 4)
    return round(rng.uniform(0.64, 0.9), 4)


def _build_seed_payload(product_id: str, count: int) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    rng = random.Random(42)
    now = datetime.now(timezone.utc)
    reviews: List[Dict[str, Any]] = []
    analyses: List[Dict[str, Any]] = []

    for i in range(count):
        label = _pick_label(rng)
        aspect = rng.choice(ASPECTS)
        score = _score_for_label(label, rng)
        credibility = _credibility_for_label(label, rng)
        content = _build_review_text(label, aspect, i + 1, rng)

        created_at = now - timedelta(hours=(i % (24 * 30)), minutes=(i * 7) % 59)
        text_hash = hashlib.md5(f"{content}|{created_at.isoformat()}|{i}".encode("utf-8")).hexdigest()

        reviews.append(
            {
                "product_id": product_id,
                "platform": PLATFORMS[i % len(PLATFORMS)],
                "source_url": f"https://example.com/review/{i + 1}",
                "created_at": created_at.isoformat(),
                "text_hash": text_hash,
                "content": content,
                "username": f"DemoUser{(i % 100) + 1}",
            }
        )

        analyses.append(
            {
                "label": label,
                "score": score,
                "credibility": credibility,
                "emotions": [{"name": EMOTION_BY_LABEL[label], "score": int(score * 100)}],
                "credibility_reasons": ["seeded-demo-data"],
                "aspects": [{"name": aspect, "aspect": aspect.lower(), "sentiment": label.lower(), "score": score}],
            }
        )

    return reviews, analyses


async def _get_reviews_count() -> int:
    response = await asyncio.to_thread(lambda: supabase.table("reviews").select("id", count="exact").limit(1).execute())
    return int(response.count or 0)


async def _get_or_create_demo_product() -> str:
    existing = await asyncio.to_thread(
        lambda: supabase.table("products").select("id").eq("name", DEMO_PRODUCT_NAME).limit(1).execute()
    )
    if existing.data:
        return existing.data[0]["id"]

    payload = {"name": DEMO_PRODUCT_NAME, "keywords": ["demo", "seed", "sentiment"]}
    try:
        created = await asyncio.to_thread(lambda: supabase.table("products").insert(payload).execute())
    except Exception:
        # Fallback for older schemas without keywords array support
        created = await asyncio.to_thread(lambda: supabase.table("products").insert({"name": DEMO_PRODUCT_NAME}).execute())

    if not created.data:
        raise RuntimeError("Failed to create demo product for seed data")

    return created.data[0]["id"]


def _insert_reviews_chunk(rows: List[Dict[str, Any]], text_field: str, author_field: str):
    payload = []
    for row in rows:
        item = dict(row)
        content = item.pop("content")
        username = item.pop("username")
        item[text_field] = content
        item[author_field] = username
        payload.append(item)

    return supabase.table("reviews").insert(payload).execute()


async def _insert_reviews_with_fallback(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    try:
        response = await asyncio.to_thread(_insert_reviews_chunk, rows, "content", "username")
    except Exception:
        response = await asyncio.to_thread(_insert_reviews_chunk, rows, "text", "author")

    return response.data or []


async def ensure_demo_seed_data(min_reviews: int = 500) -> Dict[str, Any]:
    if not supabase:
        logger.warning("Skipping seed data: Supabase client unavailable")
        return {"seeded": 0, "skipped": True, "reason": "no_supabase"}

    current_count = await _get_reviews_count()
    if current_count >= min_reviews:
        return {"seeded": 0, "skipped": True, "reason": "already_seeded", "total_reviews": current_count}

    product_id = await _get_or_create_demo_product()
    missing = min_reviews - current_count
    reviews, analyses = _build_seed_payload(product_id, missing)

    inserted_total = 0
    chunk_size = 100

    for start in range(0, len(reviews), chunk_size):
        review_chunk = reviews[start:start + chunk_size]
        analysis_chunk = analyses[start:start + chunk_size]

        inserted_reviews = await _insert_reviews_with_fallback(review_chunk)
        if not inserted_reviews:
            continue

        sentiment_payload = []
        for inserted_review, analysis in zip(inserted_reviews, analysis_chunk):
            review_id = inserted_review.get("id")
            if not review_id:
                continue

            sentiment_payload.append(
                {
                    "review_id": review_id,
                    "product_id": product_id,
                    "label": analysis["label"],
                    "score": analysis["score"],
                    "emotions": analysis["emotions"],
                    "credibility": analysis["credibility"],
                    "credibility_reasons": analysis["credibility_reasons"],
                    "aspects": analysis["aspects"],
                }
            )

        if sentiment_payload:
            try:
                await asyncio.to_thread(lambda: supabase.table("sentiment_analysis").insert(sentiment_payload).execute())
            except Exception as exc:
                logger.warning("Seed sentiment insert warning: %s", exc)

        inserted_total += len(inserted_reviews)

    logger.info("Demo seed complete: inserted %s reviews", inserted_total)
    return {"seeded": inserted_total, "skipped": False, "total_reviews": current_count + inserted_total}
