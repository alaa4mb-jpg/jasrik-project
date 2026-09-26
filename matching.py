"""
matching.py — منطق المطابقة والفجوات
======================================
- تحميل data.json مرة واحدة (cached)
- score_match(): يحسب نسبة المطابقة + الأسباب + تفصيل الأبعاد
- build_gaps(): يستخرج فجوات المهارات
- دوال مساعدة للتوحيد والعرض بالعربية

لا يستخدم ML أو embeddings. المنطق شفاف بالكامل:
  كل رقم في النتيجة يعود إلى قاعدة واحدة واضحة في data.json.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# تحميل البيانات
# ---------------------------------------------------------------------------
DATA_PATH = Path(__file__).resolve().parent / "data.json"


@lru_cache(maxsize=1)
def load_data() -> dict[str, Any]:
    """يحمّل data.json مرة واحدة ويحفظه في الذاكرة."""
    with DATA_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def config() -> dict[str, Any]:
    return load_data()["config"]


def opportunities() -> list[dict[str, Any]]:
    return load_data()["opportunities"]


def learning_actions() -> dict[str, Any]:
    return load_data()["learning_actions"]


def demo_student() -> dict[str, Any]:
    """نسخة مستقلة من الطالب التجريبي (حتى لا نعدّل الأصل بالخطأ)."""
    return json.loads(json.dumps(load_data()["demo_student"]))


# ---------------------------------------------------------------------------
# أدوات التوحيد والعرض بالعربية
# ---------------------------------------------------------------------------
def level_label(level: int) -> str:
    """1 -> مبتدئ ... 4 -> خبير. و 0 -> 'غير متوفرة'."""
    if level <= 0:
        return "غير متوفرة"
    return config()["level_labels"].get(str(level), str(level))


def gap_label(gap: int) -> str:
    return {
        1: "مستوى واحد",
        2: "مستويان",
        3: "ثلاثة مستويات",
    }.get(gap, f"{gap} مستويات")


def normalize_skill(name: str) -> str:
    """يحوّل أي كتابة للمهارة إلى الاسم المعياري."""
    if not name:
        return ""
    key = name.strip().lower()
    return config()["skill_aliases"].get(key, name.strip())


def normalize_interest(name: str) -> str:
    """يوحّد الاهتمام عربيًا أو إنجليزيًا."""
    if not name:
        return ""
    key = name.strip().lower()
    return config()["interest_aliases"].get(key, name.strip())


def normalize_interests(names: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for n in names:
        c = normalize_interest(n)
        if c and c.lower() not in seen:
            seen.add(c.lower())
            result.append(c)
    return result


def normalize_skills(skills: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """يوحّد أسماء المهارات ويحذف المكرر (يأخذ أعلى مستوى)."""
    best: dict[str, dict[str, Any]] = {}
    for s in skills:
        name = normalize_skill(s.get("name", ""))
        if not name:
            continue
        level = int(s.get("level", 1))
        key = name.lower()
        if key not in best or level > best[key]["level"]:
            best[key] = {"name": name, "level": level}
    return list(best.values())


def score_band(score: float) -> tuple[str, str]:
    """يرجع (المسمى، اللون) لدرجة المطابقة."""
    for band in config()["score_bands"]:
        if score >= band["min"]:
            return band["label"], band["color"]

    last = config()["score_bands"][-1]
    return last["label"], last["color"]


# ---------------------------------------------------------------------------
# مساعدات المهارات
# ---------------------------------------------------------------------------
def _student_skill_map(student: dict[str, Any]) -> dict[str, int]:
    """{اسم_المهارة_منخفض: المستوى}."""
    return {s["name"].lower(): s["level"] for s in normalize_skills(student["skills"])}


def _opp_skill_map(opp_skills: list[dict[str, Any]]) -> dict[str, int]:
    return {normalize_skill(s["name"]).lower(): s["level"] for s in opp_skills}


# ---------------------------------------------------------------------------
# فجوات المهارات | Skill Gaps
# ---------------------------------------------------------------------------
def build_gaps(student: dict[str, Any], opp: dict[str, Any]) -> list[dict[str, Any]]:
    """يقارن مهارات الطالب بالمهارات المطلوبة ويُرجع قائمة الفجوات.

    كل فجوة:
      {skill, student_level, required_level, gap, is_missing, label_ar}
    """
    smap = _student_skill_map(student)
    gaps: list[dict[str, Any]] = []

    for req in opp["required_skills"]:
        name = normalize_skill(req["name"])
        required = int(req["level"])
        current = smap.get(name.lower(), 0)

        if current < required:
            gap = required - current
            gaps.append({
                "skill": name,
                "student_level": current,
                "required_level": required,
                "gap": gap,
                "is_missing": current == 0,
                "is_preferred": False,
                "student_label": level_label(current),
                "required_label": level_label(required),
                "gap_label": gap_label(gap),
            })

    # المهارات المفضلة الناقصة (تُعرض كمعلومة، بلا خصم كبير)
    for pref in opp["preferred_skills"]:
        name = normalize_skill(pref["name"])
        required = int(pref["level"])
        current = smap.get(name.lower(), 0)
        if current < required:
            gap = required - current
            gaps.append({
                "skill": name,
                "student_level": current,
                "required_level": required,
                "gap": gap,
                "is_missing": current == 0,
                "is_preferred": True,
                "student_label": level_label(current),
                "required_label": level_label(required),
                "gap_label": gap_label(gap),
            })

    # الأولوية: الفجوات المطلوبة أولًا، ثم الأكبر فجوةً
    gaps.sort(key=lambda g: (g["is_preferred"], -g["gap"]))
    return gaps


# ---------------------------------------------------------------------------
# حساب المطابقة | Match Score
# ---------------------------------------------------------------------------
def _score_skills(student: dict[str, Any], opp: dict[str, Any]) -> tuple[float, list[str]]:
    """درجة المهارات 0-100 مع الأسباب."""
    cfg = config()["scoring"]
    smap = _student_skill_map(student)
    reasons: list[str] = []

    required = opp["required_skills"]
    if not required:
        return 100.0, ["لا توجد مهارات مطلوبة محددة لهذه الفرصة"]

    score = 100.0

    # خصم عن كل فجوة في المهارات المطلوبة
    for req in required:
        name = normalize_skill(req["name"])
        required_level = int(req["level"])
        current = smap.get(name.lower(), 0)

        if current >= required_level:
            reasons.append(
                f"لديك {name} بمستوى {level_label(current)} "
                f"(المطلوب: {level_label(required_level)})"
            )
        else:
            gap = required_level - current
            penalty = gap * cfg["skill_gap_penalty_per_level"]
            score -= penalty
            if current == 0:
                reasons.append(
                    f"المهارة {name} غير متوفرة لديك، والمطلوب مستوى "
                    f"{level_label(required_level)}"
                )
            else:
                reasons.append(
                    f"تحتاج إلى رفع {name} من {level_label(current)} "
                    f"إلى {level_label(required_level)}"
                )

    # مكافأة صغيرة للمهارات المفضلة المتحققة
    bonus = 0.0
    for pref in opp["preferred_skills"]:
        name = normalize_skill(pref["name"])
        required_level = int(pref["level"])
        current = smap.get(name.lower(), 0)
        if current >= required_level:
            bonus += cfg["preferred_bonus_per_skill"]
    score += min(bonus, cfg["preferred_bonus_cap"])

    return max(0.0, min(100.0, score)), reasons


def _score_major(student: dict[str, Any], opp: dict[str, Any]) -> tuple[float, list[str]]:
    """درجة التخصص — مطابقة مباشرة أو قريبة أو مختلفة."""
    cfg = config()["scoring"]
    student_major = student["major"]
    required_major = opp["required_major"]

    if student_major == required_major:
        return cfg["major_score_exact"], [
            f"تخصصك ({student_major}) مطابق للتخصص المطلوب"
        ]

    for family in config()["related_major_families"]:
        if student_major in family and required_major in family:
            return cfg["major_score_related"], [
                f"تخصصك ({student_major}) قريب من التخصص المطلوب ({required_major})"
            ]

    return cfg["major_score_none"], [
        f"التخصص المطلوب ({required_major}) مختلف عن تخصصك ({student_major})"
    ]


def _score_interests(student: dict[str, Any], opp: dict[str, Any]) -> tuple[float, list[str]]:
    """درجة الاهتمامات — نسبة التقاطع."""
    cfg = config()["scoring"]
    s_interests = {normalize_interest(i).lower() for i in student.get("interests", [])}
    o_interests = {normalize_interest(i).lower() for i in opp.get("interests", [])}

    if not o_interests:
        return cfg["interest_neutral_score"], ["الفرصة لا تحدد اهتمامات معينة"]

    matched = s_interests & o_interests
    score = (len(matched) / len(o_interests)) * 100.0

    if matched:
        # عرض الأسماء المعيارية
        names = [normalize_interest(i) for i in matched]
        reasons = [f"اهتمامك بـ{', '.join(names)} يتوافق مع الفرصة"]
    else:
        reasons = ["لا توجد اهتمامات مشتركة مع هذه الفرصة"]

    return score, reasons


def _score_experience(student: dict[str, Any], opp: dict[str, Any]) -> tuple[float, list[str]]:
    """درجة الخبرة — مقارنة مستوى الطالب (0-5) بالمتطلب."""
    cfg = config()["scoring"]
    student_exp = int(student.get("experience_level", 0))
    required_exp = int(opp.get("min_experience_level", 0))

    if student_exp >= required_exp:
        return cfg["experience_overqualified_score"], [
            "مستوى خبرتك يلبي متطلبات الفرصة"
        ]

    missing = required_exp - student_exp
    penalty = missing * cfg["experience_per_level_penalty"]
    score = max(0.0, 100.0 - penalty)

    exp_labels = config()["experience_labels"]
    return score, [
        f"مستوى خبرتك الحالي ({exp_labels[str(student_exp)]}) "
        f"أقل من المطلوب ({exp_labels[str(required_exp)]})"
    ]


def score_match(student: dict[str, Any], opp: dict[str, Any]) -> dict[str, Any]:
    """يحسب نسبة المطابقة الكاملة مع التفصيل والأسباب.

    النتيجة:
      {
        final_score, band_label, band_color,
        dimensions: [{dimension, label, score, weight, reasons}, ...],
        matched_skills, gaps, missing_skills, reasons
      }
    """
    weights = config()["weights"]
    scoring = config()["scoring"]

    skill_score, skill_reasons = _score_skills(student, opp)
    major_score, major_reasons = _score_major(student, opp)
    interest_score, interest_reasons = _score_interests(student, opp)
    exp_score, exp_reasons = _score_experience(student, opp)

    dimensions = [
        {
            "dimension": "skills",
            "label": "المهارات",
            "score": round(skill_score, 1),
            "weight": weights["skills"],
            "reasons": skill_reasons,
        },
        {
            "dimension": "major",
            "label": "التخصص",
            "score": round(major_score, 1),
            "weight": weights["major"],
            "reasons": major_reasons,
        },
        {
            "dimension": "interests",
            "label": "الاهتمامات",
            "score": round(interest_score, 1),
            "weight": weights["interests"],
            "reasons": interest_reasons,
        },
        {
            "dimension": "experience",
            "label": "الخبرة",
            "score": round(exp_score, 1),
            "weight": weights["experience"],
            "reasons": exp_reasons,
        },
    ]

    final = sum(d["score"] * d["weight"] for d in dimensions)
    final = round(max(0.0, min(100.0, final)), 1)
    band_label, band_color = score_band(final)

    gaps = build_gaps(student, opp)

    # المهارات المتوافقة (للعرض)
    smap = _student_skill_map(student)
    matched_skills = [
        normalize_skill(req["name"])
        for req in opp["required_skills"]
        if smap.get(normalize_skill(req["name"]).lower(), 0) >= int(req["level"])
    ]

    # كل الأسباب في قائمة واحدة (مع رمز واضح)
    all_reasons: list[str] = []
    for d in dimensions:
        for r in d["reasons"]:
            all_reasons.append(f"{d['label']}: {r}")

    return {
        "final_score": final,
        "band_label": band_label,
        "band_color": band_color,
        "dimensions": dimensions,
        "matched_skills": matched_skills,
        "gaps": gaps,
        "missing_skills": [g for g in gaps if g["is_missing"] and not g["is_preferred"]],
        "reasons": all_reasons,
    }


def rank_opportunities(student: dict[str, Any]) -> list[dict[str, Any]]:
    """يرتّب كل الفرص تنازليًا حسب نسبة المطابقة."""
    results = []
    for opp in opportunities():
        result = score_match(student, opp)
        results.append({"opportunity": opp, "match": result})
    results.sort(key=lambda x: x["match"]["final_score"], reverse=True)
    return results