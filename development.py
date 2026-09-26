"""
development.py — خطة التطوير وإعادة التقييم
=============================================
يحوّل فجوات المهارات إلى خطة تطوير عملية:
  Skill Gap → Practical Action → Evidence → Target Level

ويعيد تقييم الجاهزية بعد إكمال المهام، مع الحفاظ على مهارات الطالب الأصلية.
"""

from __future__ import annotations

from typing import Any

from matching import (
    config,
    learning_actions,
    level_label,
    normalize_skill,
    score_match,
)


def _target_level_for(skill: str, required_level: int) -> int:
    """المستوى المستهدف = المستوى المطلوب (لا نتجاوزه)."""
    return max(1, min(required_level, 4))


def build_plan(
    student: dict[str, Any],
    opp: dict[str, Any],
    gaps: list[dict[str, Any]],
    baseline_score: float,
) -> dict[str, Any]:
    """يبني خطة تطوير من الفجوات المطلوبة فقط.

    النتيجة:
      {tasks: [...], baseline_score, total_hours, opportunity_id}
    """
    max_tasks = config()["scoring"]["plan_max_tasks"]
    actions = learning_actions()

    # نأخذ الفجوات المطلوبة (لا المفضلة) — المفضلة تحسينية فقط
    required_gaps = [g for g in gaps if not g["is_preferred"]]
    required_gaps = required_gaps[:max_tasks]

    tasks: list[dict[str, Any]] = []
    for i, gap in enumerate(required_gaps, start=1):
        skill = gap["skill"]
        target = _target_level_for(skill, gap["required_level"])
        meta = actions.get(normalize_skill(skill), {})

        tasks.append({
            "priority": i,
            "skill": skill,
            "current_level": gap["student_level"],
            "current_label": level_label(gap["student_level"]),
            "target_level": target,
            "target_label": level_label(target),
            "gap": gap["gap"],
            "gap_label": gap["gap_label"],
            "action": meta.get("action", f"طوّر مهارة {skill} عمليًا"),
            "evidence": meta.get("evidence", "نفّذ مشروعًا تطبيقيًا يثبت المهارة"),
            "resource": meta.get("resource", ""),
            "resource_url": meta.get("resource_url", ""),
            "estimated_hours": int(meta.get("estimated_hours", 20)),
            "completed": False,
        })

    return {
        "student_id": student.get("student_id", "student_001"),
        "opportunity_id": opp["opportunity_id"],
        "baseline_score": baseline_score,
        "tasks": tasks,
        "total_hours": sum(t["estimated_hours"] for t in tasks),
    }


def apply_completed_tasks(
    student: dict[str, Any],
    plan: dict[str, Any],
) -> dict[str, Any]:
    """يطبّق المهام المكتملة على مهارات الطالب.

    مهم: نبدأ من مهارات الطالب الأصلية، ثم نرفع مستوى المهارات
    التي أُكملت مهامها فقط. بقية المهارات تبقى كما هي.
    """
    # خريطة المهارات الأصلية (اسم معياري -> {name, level})
    merged: dict[str, dict[str, Any]] = {}
    for s in student.get("skills", []):
        name = normalize_skill(s["name"])
        key = name.lower()
        merged[key] = {"name": name, "level": int(s["level"])}

    # رفع المستوى للمهام المكتملة فقط
    for task in plan["tasks"]:
        if not task.get("completed"):
            continue
        key = normalize_skill(task["skill"]).lower()
        if key in merged:
            if task["target_level"] > merged[key]["level"]:
                merged[key]["level"] = task["target_level"]
        else:
            merged[key] = {
                "name": normalize_skill(task["skill"]),
                "level": task["target_level"],
            }

    updated = dict(student)
    updated["skills"] = list(merged.values())
    return updated


def reevaluate(
    student: dict[str, Any],
    opp: dict[str, Any],
    plan: dict[str, Any],
) -> dict[str, Any]:
    """يعيد حساب المطابقة بعد تطبيق المهام المكتملة.

    يرجع:
      {before, after, improvement, updated_student, applied_tasks}
    """
    updated_student = apply_completed_tasks(student, plan)
    before = score_match(student, opp)
    after = score_match(updated_student, opp)

    applied = [
        f"{t['skill']}: {t['current_label']} → {t['target_label']}"
        for t in plan["tasks"] if t.get("completed")
    ]

    return {
        "before": before["final_score"],
        "after": after["final_score"],
        "improvement": round(after["final_score"] - before["final_score"], 1),
        "before_band": before["band_label"],
        "after_band": after["band_label"],
        "updated_student": updated_student,
        "updated_match": after,
        "applied_tasks": applied,
    }


def skill_summary_ar(student: dict[str, Any]) -> list[str]:
    """عرض مهارات الطالب بصيغة 'Python — متمكن'."""
    from matching import normalize_skills

    return [
        f"{s['name']} — {level_label(s['level'])}"
        for s in normalize_skills(student.get("skills", []))
    ]