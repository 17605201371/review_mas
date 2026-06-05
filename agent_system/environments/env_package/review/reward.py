import ast
import json
import math
import re
from collections import Counter
from typing import Dict, List, Optional, Tuple

SECTION_ORDER = ["summary", "strengths", "weaknesses", "suggestions", "decision", "rating"]
SECTION_PATTERNS = {
    "summary": [r"summary of reviews?", r"summary", r"overview", r"synthesis", r"paper summary", r"review summary"],
    "strengths": [r"key strengths", r"strengths", r"pros", r"positive aspects", r"main strengths"],
    "weaknesses": [r"key weaknesses", r"weaknesses", r"limitations", r"cons", r"areas for improvement", r"main weaknesses", r"concerns"],
    "suggestions": [r"questions/suggestions", r"questions", r"suggestions", r"future work", r"recommendations to authors"],
    "decision": [r"final decision", r"decision recommendation", r"decision", r"recommendation", r"overall assessment"],
    "rating": [r"rating", r"confidence", r"score"],
}
AUDIT_ID_PATTERN = re.compile(r"\b(?:claim|evidence|flaw)-[a-z0-9\-]+", re.I)
DECISION_PATTERNS = [
    re.compile(r"final\s*decision\s*[:：]\s*(accept|reject|neutral)", re.I),
    re.compile(r"decision\s*recommendation\s*[:：]\s*(accept|reject|neutral)", re.I),
    re.compile(r"overall\s*recommendation\s*[:：]\s*(accept|reject|neutral)", re.I),
    re.compile(r"recommendation\s*[:：]\s*(accept|reject|neutral)", re.I),
    re.compile(r"decision\s*[:：]\s*(accept|reject|neutral)", re.I),
]
PLACEHOLDER_PATTERNS = [
    re.compile(r"\[specific [^\]]+\]", re.I),
    re.compile(r"\[insert [^\]]+\]", re.I),
    re.compile(r"lorem ipsum", re.I),
]
STOPWORDS = {
    'the', 'a', 'an', 'and', 'or', 'of', 'to', 'for', 'in', 'on', 'with', 'by', 'is', 'are', 'was', 'were',
    'be', 'this', 'that', 'it', 'as', 'at', 'from', 'their', 'there', 'paper', 'work', 'method', 'results',
    'authors', 'author', 'review', 'reviewer', 'meta', 'section', 'study', 'approach', 'proposed', 'using',
    'can', 'could', 'should', 'would', 'these', 'those', 'into', 'than', 'such', 'also', 'more', 'most',
    'have', 'has', 'had', 'been', 'being', 'but', 'not', 'they', 'them', 'its', 'our', 'your', 'you', 'we',
    'overall', 'assessment'
}
CRITIQUE_TERMS = ['limitation', 'weakness', 'concern', 'unclear', 'missing', 'insufficient', 'lack', 'issue']
SUGGESTION_TERMS = ['suggest', 'recommend', 'could', 'should', 'improve', 'clarify', 'ablation', 'compare', 'discuss']
STANCE_POSITIVE_TERMS = ['strong', 'novel', 'effective', 'promising', 'clear', 'valuable', 'significant', 'rigorous', 'sound', 'well-executed']
STANCE_NEGATIVE_TERMS = ['weak', 'unclear', 'limited', 'insufficient', 'lack', 'flaw', 'issue', 'problem', 'concern', 'missing']


def _normalize_text(text: Optional[str]) -> str:
    if text is None:
        return ''
    return re.sub(r'\s+', ' ', str(text)).strip()


def _extract_decision(text: str) -> Optional[str]:
    lower = text.lower()
    explicit_matches = []
    for pattern in DECISION_PATTERNS:
        explicit_matches.extend(pattern.finditer(lower))
    if explicit_matches:
        return explicit_matches[-1].group(1).lower()

    tail_lines = [line.strip().lower() for line in lower.splitlines()[-8:] if line.strip()]
    for line in reversed(tail_lines):
        if line in {"accept", "reject", "neutral"}:
            return line
        if line.startswith("final decision") or line.startswith("recommendation") or line.startswith("decision"):
            for token in ("accept", "reject", "neutral"):
                if token in line:
                    return token
    return None


def _tokenize_keywords(text: str) -> List[str]:
    tokens = re.findall(r"[A-Za-z][A-Za-z\-]{2,}", text.lower())
    return [tok for tok in tokens if tok not in STOPWORDS and not tok.isdigit()]


def _cosine_similarity(text_a: str, text_b: str) -> float:
    toks_a = _tokenize_keywords(text_a)
    toks_b = _tokenize_keywords(text_b)
    if not toks_a or not toks_b:
        return 0.0
    vec_a = Counter(toks_a)
    vec_b = Counter(toks_b)
    common = set(vec_a) & set(vec_b)
    dot = sum(vec_a[t] * vec_b[t] for t in common)
    norm_a = math.sqrt(sum(v * v for v in vec_a.values()))
    norm_b = math.sqrt(sum(v * v for v in vec_b.values()))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return max(0.0, min(1.0, dot / (norm_a * norm_b)))


def _keyword_recall(prediction: str, reference_text: str, top_k: int = 20) -> float:
    ref_tokens = _tokenize_keywords(reference_text)
    pred_tokens = set(_tokenize_keywords(prediction))
    if not ref_tokens or not pred_tokens:
        return 0.0
    top_ref = [tok for tok, _ in Counter(ref_tokens).most_common(top_k)]
    hits = sum(1 for tok in top_ref if tok in pred_tokens)
    return hits / max(1, min(top_k, len(top_ref)))


def _idf_weighted_precision(prediction: str, reference_text: str, *, min_doc_freq: int = 2) -> float:
    """How much of the prediction's content tokens are present in the reference, IDF-weighted.

    Pred-centric (precision-like) so it's stable when reference is much longer than prediction.
    Stopwords + low-IDF tokens (count >= min_doc_freq in pred only) are downweighted.
    """
    pred_tokens = _tokenize_keywords(prediction)
    if not pred_tokens:
        return 0.0
    ref_tokens = _tokenize_keywords(reference_text)
    if not ref_tokens:
        return 0.0
    ref_set = set(ref_tokens)
    pred_counter = Counter(pred_tokens)
    # Higher weight for content words that appear less frequently in prediction itself (rough IDF proxy)
    weighted_total = 0.0
    weighted_hit = 0.0
    for tok, count in pred_counter.items():
        weight = 1.0 / math.sqrt(count) if count >= 1 else 0.0
        weighted_total += weight
        if tok in ref_set:
            weighted_hit += weight
    if weighted_total <= 0.0:
        return 0.0
    return max(0.0, min(1.0, weighted_hit / weighted_total))


def _alignment_score(prediction: str, reference_text: str) -> float:
    """Combined alignment: max of length-robust precision and cosine."""
    if not prediction or not reference_text:
        return 0.0
    return max(
        _idf_weighted_precision(prediction, reference_text),
        _cosine_similarity(prediction, reference_text),
    )


def _extract_reference_text(raw: str) -> str:
    """Reference often comes as JSON message list (assistant/user thinking trace).

    Extract the longest assistant content block (the actual review) and strip search passages.
    Falls back to raw if not parseable.
    """
    if not raw:
        return ''
    text = raw.strip()
    if not (text.startswith('[') or text.startswith('{')):
        return raw
    try:
        parsed = json.loads(text)
    except Exception:
        try:
            parsed = ast.literal_eval(text)
        except Exception:
            return raw
    if isinstance(parsed, dict):
        return str(parsed.get('content', raw))
    if not isinstance(parsed, list):
        return raw
    # Pick the longest assistant message; assistant messages contain the actual review content.
    assistant_blobs = []
    for item in parsed:
        if not isinstance(item, dict):
            continue
        if str(item.get('role', '')).lower() == 'assistant':
            assistant_blobs.append(str(item.get('content', '')))
    if assistant_blobs:
        return max(assistant_blobs, key=len)
    # Fallback: concatenate all content fields
    return ' '.join(str(item.get('content', '')) for item in parsed if isinstance(item, dict))


def _extract_numeric_rating(prediction: str) -> Optional[float]:
    for pattern in [re.compile(r"rating\s*[:：]\s*(\d+(?:\.\d+)?)", re.I), re.compile(r"score\s*[:：]\s*(\d+(?:\.\d+)?)", re.I)]:
        match = pattern.search(prediction)
        if match:
            return float(match.group(1))
    return None


def _parse_reference_ratings(reference_ratings) -> List[float]:
    if reference_ratings is None:
        return []
    if isinstance(reference_ratings, (list, tuple)):
        return [float(x) for x in reference_ratings if str(x).strip()]
    if isinstance(reference_ratings, str):
        try:
            parsed = ast.literal_eval(reference_ratings)
            if isinstance(parsed, (list, tuple)):
                return [float(x) for x in parsed if str(x).strip()]
        except Exception:
            pass
        nums = re.findall(r"\d+(?:\.\d+)?", reference_ratings)
        return [float(x) for x in nums]
    return []


def _try_parse_json_text(text: str) -> str:
    text = _normalize_text(text)
    if not text:
        return ''
    try:
        parsed = json.loads(text)
    except Exception:
        return text
    if isinstance(parsed, list):
        chunks = []
        for item in parsed:
            if isinstance(item, dict):
                content = item.get('content', '')
                if isinstance(content, dict):
                    chunks.append(json.dumps(content, ensure_ascii=False))
                else:
                    chunks.append(str(content))
            else:
                chunks.append(str(item))
        return '\n'.join(chunks)
    if isinstance(parsed, dict):
        return json.dumps(parsed, ensure_ascii=False)
    return str(parsed)


def _extract_sections(text: str) -> Dict[str, str]:
    raw = str(text or '').strip()
    if '\n' in raw and not raw.startswith('[') and not raw.startswith('{'):
        source = raw
    else:
        source = _try_parse_json_text(text)
    lines = [line.strip() for line in source.splitlines() if line.strip()]
    sections: Dict[str, List[str]] = {name: [] for name in SECTION_ORDER}
    current = None

    for line in lines:
        # Normalize numbered/bulleted headers like "1. Summary of Reviews" -> "summary of reviews"
        cleaned = re.sub(r'^[#\-*\d\.\)\s]+', '', line.lower()).strip()
        # Drop trailing colon for matching
        header_candidate = cleaned.rstrip(':：').strip()
        matched = None
        if cleaned.startswith("reason for"):
            pass
        else:
            for name, patterns in SECTION_PATTERNS.items():
                # Match either the cleaned line as a header (full match) or contains the pattern as header prefix
                if any(re.fullmatch(pat, header_candidate, re.I) for pat in patterns):
                    matched = name
                    break
                if any(re.search(rf"(^|[*#\-\d\.\s]){pat}(\b|[:：])", cleaned) for pat in patterns):
                    matched = name
                    break
        if matched is not None:
            current = matched
            content = re.sub(r'^[^:：]*[:：]\s*', '', line, count=1).strip()
            if content and content.lower() != cleaned:
                sections[current].append(content)
            continue
        if current is not None:
            sections[current].append(line)

    merged = {name: _normalize_text(' '.join(parts)) for name, parts in sections.items()}
    if not merged['decision']:
        decision = _extract_decision(source)
        if decision:
            merged['decision'] = decision
    return merged


def _contains_placeholders(text: str) -> bool:
    return any(pattern.search(text) for pattern in PLACEHOLDER_PATTERNS)


def _stance_signal(text: str) -> float:
    lower = text.lower()
    pos = sum(lower.count(term) for term in STANCE_POSITIVE_TERMS)
    neg = sum(lower.count(term) for term in STANCE_NEGATIVE_TERMS)
    total = pos + neg
    if total == 0:
        return 0.0
    return (pos - neg) / total


def _section_critique_density(weaknesses_text: str) -> float:
    """Density of critique/concern terms specifically in the weaknesses section, normalized by length.

    Returns 0..1. Replaces the trivial whole-text count which always saturates to 1.0.
    """
    if not weaknesses_text:
        return 0.0
    words = weaknesses_text.split()
    if len(words) < 10:
        return 0.0
    lower = weaknesses_text.lower()
    hits = sum(lower.count(term) for term in CRITIQUE_TERMS)
    # Target density ~ 1 hit per 30 words; saturate at ~3x that
    density = hits / max(1, len(words))
    return max(0.0, min(1.0, density * 30.0))


def _audit_id_leak_ratio(prediction: str) -> float:
    """Fraction of words that look like audit ids (claim-1, evidence-2, flaw-x)."""
    words = prediction.split()
    if not words:
        return 0.0
    hits = len(AUDIT_ID_PATTERN.findall(prediction))
    return min(1.0, hits / max(1, len(words)))


def _evidence_support_score(review_state: Optional[Dict]) -> Tuple[float, Dict[str, float]]:
    """Compute evidence/support quality score in 0..1 from review_state.state_audit.decision_hygiene.

    Returns (score, breakdown). When review_state is missing or has no claims, returns (0.0, {}).
    """
    if not isinstance(review_state, dict):
        return 0.0, {}
    sa = review_state.get('state_audit') or {}
    dh = sa.get('decision_hygiene') or {}
    if not isinstance(dh, dict):
        return 0.0, {}

    # Claim count: prefer paper_extracted; fallback to total claims
    claims = review_state.get('claims') or []
    paper_claims = [c for c in claims if isinstance(c, dict) and str(c.get('claim_kind', '')).lower() == 'paper_extracted']
    total_claims = len(paper_claims) if paper_claims else len(claims)
    if total_claims <= 0:
        return 0.0, {}

    real_strong = float(dh.get('real_strong_support_total') or 0)
    claims_with_real = float(dh.get('claims_with_real_strong_support') or 0)
    claims_with_2plus = float(dh.get('claims_with_2plus_independent_support') or 0)
    claims_with_empirical = float(dh.get('claims_with_empirical_real_strong_support') or 0)
    deep = float((dh.get('claim_support_depth_counts') or {}).get('deep') or 0)
    moderate = float((dh.get('claim_support_depth_counts') or {}).get('moderate') or 0)
    grounded_flaws = float(dh.get('grounded_active_flaw_count') or 0)

    # Sub-scores all in 0..1
    coverage = min(1.0, claims_with_real / total_claims)
    independent = min(1.0, claims_with_2plus / max(1.0, total_claims))
    empirical = min(1.0, claims_with_empirical / max(1.0, total_claims))
    depth = min(1.0, (deep * 1.0 + moderate * 0.5) / max(1.0, total_claims))
    flaw_density = min(1.0, grounded_flaws / 3.0)  # 3+ grounded flaws saturates
    support_volume = min(1.0, real_strong / max(1.0, 2.0 * total_claims))

    score = (
        0.30 * coverage +
        0.20 * depth +
        0.15 * empirical +
        0.10 * independent +
        0.15 * flaw_density +
        0.10 * support_volume
    )
    breakdown = {
        'es_coverage': round(coverage, 4),
        'es_depth': round(depth, 4),
        'es_empirical': round(empirical, 4),
        'es_independent': round(independent, 4),
        'es_flaw_density': round(flaw_density, 4),
        'es_support_volume': round(support_volume, 4),
        'evidence_support_score': round(score, 4),
    }
    return score, breakdown


def compute_review_reward(
    prediction: str,
    ground_truth: str,
    reference_review: Optional[str] = None,
    reviewer_comments: Optional[str] = None,
    reference_ratings=None,
    review_state: Optional[Dict] = None,
) -> Tuple[float, Dict[str, float]]:
    """Reward function v2 (no decision dependency, evidence-aware).

    Composition:
      - Content alignment (length-robust IDF-weighted precision):  0.30
      - Evidence/support quality (from review_state hygiene):       0.40 (or redistributed if missing)
      - Structural quality (sections + length appropriateness):     0.10
      - Critique density (in weaknesses section):                   0.10
      - Stance alignment:                                            0.10
      - Penalties: placeholder, short text, audit_id leakage
    """
    # Preserve newlines for section extraction; only collapse whitespace later for token-level alignment.
    raw_prediction = prediction or ''
    raw_reference = _extract_reference_text(reference_review or '')

    prediction = _normalize_text(raw_prediction)
    reference_review = _normalize_text(raw_reference)
    reviewer_comments = _normalize_text(reviewer_comments)
    ground_truth = _normalize_text(ground_truth).lower()

    if not prediction:
        breakdown = {k: 0.0 for k in [
            'decision', 'section_presence', 'summary_align', 'strength_align', 'weakness_align',
            'suggestion_align', 'global_align', 'critique', 'rating_align',
            'evidence_support_score', 'audit_id_leak_penalty', 'penalty', 'total'
        ]}
        return 0.0, breakdown

    # Extract sections from raw (newline-preserving) text so headers can be detected.
    pred_sections = _extract_sections(raw_prediction)
    global_reference = reference_review or reviewer_comments
    ref_sections = _extract_sections(raw_reference or reviewer_comments or '')

    predicted_decision = _extract_decision(prediction)
    decision_score = 0.0  # kept for breakdown logging only, no weight

    section_presence = sum(
        1 for key in ['summary', 'strengths', 'weaknesses', 'suggestions']
        if pred_sections.get(key)
    ) / 4.0

    pred_summary = pred_sections.get('summary', '') or prediction
    pred_strengths = pred_sections.get('strengths', '') or prediction
    pred_weaknesses = pred_sections.get('weaknesses', '') or prediction
    pred_suggestions = pred_sections.get('suggestions', '') or prediction
    ref_summary = ref_sections.get('summary', '') or global_reference
    ref_strengths = ref_sections.get('strengths', '') or global_reference
    ref_weaknesses = ref_sections.get('weaknesses', '') or global_reference
    ref_suggestions = ref_sections.get('suggestions', '') or global_reference

    summary_align = _alignment_score(pred_summary, ref_summary)
    strength_align = _alignment_score(pred_strengths, ref_strengths)
    weakness_align = _alignment_score(pred_weaknesses, ref_weaknesses)
    suggestion_align = _alignment_score(pred_suggestions, ref_suggestions)
    global_align = _alignment_score(prediction, global_reference) if global_reference else 0.0

    # Critique density measured inside the weaknesses section, not whole report (avoids saturation)
    critique_score = _section_critique_density(pred_sections.get('weaknesses', '') or prediction)

    pred_stance = _stance_signal(prediction)
    ref_stance = _stance_signal(global_reference) if global_reference else 0.0
    stance_align = 0.0
    if global_reference:
        stance_align = max(0.0, 1.0 - abs(pred_stance - ref_stance) / 2.0)

    rating_align = 0.0
    target_ratings = _parse_reference_ratings(reference_ratings)
    pred_rating = _extract_numeric_rating(prediction)
    if target_ratings and pred_rating is not None:
        target = sum(target_ratings) / len(target_ratings)
        rating_align = max(0.0, 1.0 - abs(pred_rating - target) / 6.0)

    decision_line_bonus = 0.0  # deprecated, kept for breakdown compat

    # Evidence/support quality from system's structured outputs
    evidence_support_score, es_breakdown = _evidence_support_score(review_state)
    has_review_state = bool(es_breakdown)

    # Length appropriateness: 200..800 words is ideal, taper outside
    word_count = len(prediction.split())
    if 200 <= word_count <= 800:
        length_score = 1.0
    elif word_count < 200:
        length_score = max(0.0, word_count / 200.0)
    else:
        length_score = max(0.0, 1.0 - (word_count - 800) / 1200.0)

    # Penalties
    penalty = 0.0
    if _contains_placeholders(prediction):
        penalty += 0.2
    if word_count < 80:
        penalty += 0.1

    audit_id_leak = _audit_id_leak_ratio(prediction)
    audit_id_leak_penalty = min(0.10, audit_id_leak * 5.0)  # 2% of words = 0.1 penalty
    penalty += audit_id_leak_penalty

    # Weights
    # When review_state is unavailable (e.g. reward unit tests with raw text only),
    # redistribute the 0.40 evidence weight back to content alignment to keep total scale.
    w_content_summary  = 0.05
    w_content_strength = 0.05
    w_content_weakness = 0.10
    w_content_suggest  = 0.05
    w_content_global   = 0.05
    w_evidence        = 0.40
    w_section         = 0.06
    w_length          = 0.04
    w_critique        = 0.10
    w_stance          = 0.10
    if not has_review_state:
        # Redistribute evidence weight proportionally to content alignment + critique
        scale = 1.0 / (1.0 - w_evidence)  # = 1/0.6 ≈ 1.667
        w_content_summary  *= scale
        w_content_strength *= scale
        w_content_weakness *= scale
        w_content_suggest  *= scale
        w_content_global   *= scale
        w_section          *= scale
        w_length           *= scale
        w_critique         *= scale
        w_stance           *= scale
        w_evidence = 0.0

    total = (
        w_content_summary  * summary_align +
        w_content_strength * strength_align +
        w_content_weakness * weakness_align +
        w_content_suggest  * suggestion_align +
        w_content_global   * global_align +
        w_evidence         * evidence_support_score +
        w_section          * section_presence +
        w_length           * length_score +
        w_critique         * critique_score +
        w_stance           * stance_align -
        penalty
    )
    total = max(0.0, min(1.0, total))

    breakdown = {
        'decision': round(decision_score, 4),
        'section_presence': round(section_presence, 4),
        'length_score': round(length_score, 4),
        'summary_align': round(summary_align, 4),
        'strength_align': round(strength_align, 4),
        'weakness_align': round(weakness_align, 4),
        'suggestion_align': round(suggestion_align, 4),
        'global_align': round(global_align, 4),
        'critique': round(critique_score, 4),
        'stance_align': round(stance_align, 4),
        'rating_align': round(rating_align, 4),
        'decision_line_bonus': round(decision_line_bonus, 4),
        'audit_id_leak_penalty': round(audit_id_leak_penalty, 4),
        'penalty': round(penalty, 4),
        'total': round(total, 4),
    }
    breakdown.update(es_breakdown)
    return total, breakdown


from typing import List


def review_projection(actions: List[str]):
    """Keep raw review text and mark non-empty outputs as valid."""
    results = [str(action).strip() for action in actions]
    valids = [1 if result else 0 for result in results]
    return results, valids
