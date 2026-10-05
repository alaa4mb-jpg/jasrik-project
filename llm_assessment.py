"""

llm_assessment.py — تقييم إجابات الطالب باستخدام LLM

====================================================

طبقة مستقلة عن matching.py حتى يبقى حساب Match Score شفافًا وثابتًا.



الإعداد:

LLM_API_KEY=...

LLM_BASE_URL=https://api.deepseek.com

LLM_MODEL=deepseek-chat



يمكن تغيير مزود الـLLM طالما أن الـendpoint يدعم OpenAI-compatible

Chat Completions API.

"""



from __future__ import annotations



import json

import os

import re

from typing import Any



import requests

from dotenv import load_dotenv



load_dotenv()





ASSESSMENT_QUESTIONS: dict[str, list[dict[str, str]]] = {

    "opp_001": [

        {"skill": "Python", "question": "لديك ملف بيانات وتحتاج إلى تنظيفه قبل التحليل. كيف ستستخدم Python للتحقق من جودة البيانات ومعالجة المشكلات؟"},

        {"skill": "SQL", "question": "لديك جدول للطلاب وجدول للتدريب. كيف تستخدم SQL لعرض الطلاب المسجلين في تدريب معين؟ وما نوع JOIN الذي قد تستخدمه؟"},

        {"skill": "Data Analysis", "question": "لاحظت أن قيمة أحد المتغيرات أعلى بكثير من بقية القيم. كيف تتحقق مما إذا كانت هذه القيمة شاذة فعلًا؟"},

    ],

    "opp_002": [

        {"skill": "HTML/CSS", "question": "كيف تبني صفحة ويب متجاوبة تعمل بشكل جيد على الجوال والحاسب؟ اذكر أهم ما ستستخدمه في HTML وCSS."},

        {"skill": "JavaScript", "question": "كيف تجعل زرًا في صفحة الويب ينفذ إجراءً عند النقر عليه ويحدّث جزءًا من الصفحة دون إعادة تحميلها بالكامل؟"},

        {"skill": "React", "question": "ما الفكرة الأساسية من Components في React؟ ومتى قد تستخدم State داخل أحد المكونات؟"},

    ],

    "opp_003": [

        {"skill": "Python", "question": "كيف تجهز بيانات خام باستخدام Python قبل إدخالها إلى نموذج تعلم آلة؟"},

        {"skill": "Machine Learning", "question": "إذا كان نموذجك يعطي نتائج ممتازة على بيانات التدريب ونتائج ضعيفة على بيانات الاختبار، ما المشكلة المحتملة وكيف تتحقق منها؟"},

        {"skill": "SQL", "question": "كيف تستخرج من قاعدة بيانات مجموعة البيانات التي تحتاجها لبناء نموذج تعلم آلة؟ اذكر مثالًا على استخدام SELECT وWHERE أو JOIN."},

    ],

    "opp_004": [

        {"skill": "Cybersecurity Fundamentals", "question": "لاحظت محاولات تسجيل دخول متكررة وفاشلة على حسابات متعددة. ما الخطوات التي ستتخذها للتحقق من النشاط والتعامل معه؟"},

        {"skill": "Python", "question": "كيف يمكن استخدام Python لأتمتة مهمة بسيطة في تحليل سجلات النظام؟"},

        {"skill": "SQL", "question": "لديك سجلات أمنية محفوظة في قاعدة بيانات. كيف تبحث عن السجلات التي تتجاوز قيمة أو وقتًا معينًا؟"},

    ],

    "opp_005": [

        {"skill": "Docker", "question": "لديك تطبيق Python وتريد تشغيله بشكل متسق على أجهزة مختلفة. كيف يمكن أن يساعدك Docker؟ وما الذي تضعه عادة في Dockerfile؟"},

        {"skill": "Cloud (AWS)", "question": "ما الذي تفكر فيه عند نشر تطبيق على AWS من ناحية الخدمة المناسبة، الوصول، والأمان؟"},

        {"skill": "Git", "question": "أنت تعمل ضمن فريق وتريد تطوير ميزة جديدة دون التأثير مباشرة على النسخة الرئيسية. كيف تستخدم Git لتحقيق ذلك؟"},

    ],

    "opp_006": [

        {"skill": "Mobile Development (Flutter)", "question": "كيف تشرح طريقة بناء واجهة بسيطة في Flutter باستخدام Widgets؟ وما دور StatefulWidget عندما تتغير البيانات؟"},

        {"skill": "JavaScript", "question": "كيف تتعامل مع حدث تفاعلي في تطبيق أو واجهة باستخدام JavaScript؟"},

        {"skill": "Git", "question": "كيف تستخدم Git للعمل على ميزة جديدة ثم دمجها مع فرع المشروع الرئيسي بشكل منظم؟"},

    ],

    "opp_007": [

        {"skill": "Python", "question": "كيف تستخدم Python لتحويل بيانات خام إلى بيانات مناسبة للتحليل؟ اذكر خطوات عملية."},

        {"skill": "SQL", "question": "كيف تستخدم SQL لتجميع البيانات حسب فئة معينة وحساب متوسط أو مجموع لكل فئة؟"},

        {"skill": "Data Analysis", "question": "كيف تنتقل من سؤال تحليلي إلى استنتاج مدعوم بالبيانات؟ اذكر خطواتك الأساسية."},

    ],

    "opp_008": [

        {"skill": "UI/UX Design", "question": "كيف تبدأ تصميم واجهة لتطبيق جديد إذا كان المستخدم المستهدف غير واضح احتياجه بعد؟"},

        {"skill": "HTML/CSS", "question": "كيف تحول تصميمًا بصريًا إلى صفحة ويب منظمة ومتجاوبة باستخدام HTML وCSS؟"},

        {"skill": "Communication", "question": "كيف تشرح قرارًا في تصميم واجهة لفريق غير متخصص في التصميم عندما يختلفون معك؟"},

    ],

    "opp_009": [

        {"skill": "Cloud (AWS)", "question": "ما العوامل التي تراجعها قبل اختيار خدمة AWS لاستضافة تطبيق؟"},

        {"skill": "Docker", "question": "ما المشكلة التي يحلها Docker عند نشر التطبيقات، وكيف تربطه بعملية النشر؟"},

        {"skill": "Git", "question": "كيف تنظم فروع Git في مشروع يعمل عليه أكثر من مطور قبل دمج التغييرات؟"},

    ],

    "opp_010": [

        {"skill": "Python", "question": "كيف تستخدم Python لتجهيز البيانات قبل تدريب نموذج تعلم آلة؟"},

        {"skill": "Machine Learning", "question": "كيف تقيّم نموذج تصنيف، وما الفرق بين Accuracy وPrecision وRecall؟"},

        {"skill": "Deep Learning", "question": "متى قد تختار شبكة عصبية عميقة بدل نموذج تعلم آلة أبسط؟ وما الذي تنتبه له لتجنب Overfitting؟"},

    ],

}





def llm_is_configured() -> bool:

    return bool(os.getenv("LLM_API_KEY", "").strip())





def get_assessment_questions(opportunity: dict[str, Any]) -> list[dict[str, str]]:

    """يعيد 3 أسئلة ثابتة ومناسبة للفرصة، لتجنب استدعاء LLM إضافي لتوليد الأسئلة."""

    return ASSESSMENT_QUESTIONS.get(

        opportunity["opportunity_id"],

        [

            {

                "skill": opportunity["required_skills"][0]["name"],

                "question": f"اشرح كيف ستطبق مهارة {opportunity['required_skills'][0]['name']} في هذه الفرصة.",

            },

            {

                "skill": opportunity["required_skills"][1]["name"],

                "question": f"اذكر مثالًا عمليًا يوضح استخدامك لمهارة {opportunity['required_skills'][1]['name']}.",

            },

            {

                "skill": opportunity["required_skills"][2]["name"],

                "question": f"كيف تتحقق من جودة عملك عند استخدام مهارة {opportunity['required_skills'][2]['name']}؟",

            },

        ],

    )





def _extract_json(text: str) -> dict[str, Any]:

    """يتعامل مع JSON مباشر أو JSON داخل markdown code fence."""

    cleaned = text.strip()

    cleaned = re.sub(r"^```(?:json)?\s\*", "", cleaned, flags=re.IGNORECASE)

    cleaned = re.sub(r"\s\*```$", "", cleaned)

    try:

        return json.loads(cleaned)

    except json.JSONDecodeError:

        start = cleaned.find("{")

        end = cleaned.rfind("}")

        if start >= 0 and end > start:

            return json.loads(cleaned[start : end + 1])

        raise ValueError("لم يُرجع النموذج نتيجة JSON صالحة.")





def evaluate_assessment(

    student: dict[str, Any],

    opportunity: dict[str, Any],

    questions: list[dict[str, str]],

    answers: list[str],

) -> dict[str, Any]:

    """يقيّم الإجابات ويعيد نتيجة منظمة يمكن عرضها مباشرة في Streamlit."""

    base_url = os.getenv("LLM_BASE_URL", "https://api.deepseek.com").rstrip("/")

    model = os.getenv("LLM_MODEL", "deepseek-chat")

    api_key = os.getenv("LLM_API_KEY", "").strip()



    if not api_key:

        raise RuntimeError("LLM_API_KEY غير موجود في ملف .env.")



    required = [

        f"{s['name']} — المستوى المطلوب {s['level']}"

        for s in opportunity.get("required_skills", [])

    ]



    qa_text = "\n\n".join(

        f"السؤال {i}: {q['question']}\nالمهارة: {q['skill']}\nإجابة الطالب: {a}"

        for i, (q, a) in enumerate(zip(questions, answers), start=1)

    )



    system_prompt = """أنت مقيّم مهني للجاهزية للتدريب التعاوني.

قيّم إجابات الطالب بناءً على السؤال والمهارة المطلوبة فقط.

لا تفترض مهارات أو خبرات لم يذكرها الطالب.

لا تعتمد على جودة اللغة العربية أو الإنجليزية كبديل عن المعرفة التقنية.

أعد JSON فقط، دون markdown أو شرح خارج JSON.



القواعد:

- question_scores: درجة كل إجابة من 0 إلى 100، ومع كل درجة reason عربية محددة تشرح سبب الدرجة.

- assessment_score: متوسط درجات الأسئلة، من 0 إلى 100.

- strengths: أعِد 3 نقاط قدر الإمكان. كل نقطة يجب أن تكون جملة قصيرة بصيغة "اسم المهارة: أبرز ما يفهمه أو يطبقه الطالب جيدًا". ممنوع إرجاع اسم المهارة وحده.

- gaps: أعِد 3 نقاط قدر الإمكان. كل نقطة يجب أن تكون جملة قصيرة بصيغة "اسم المهارة: جانب تقني محدد يحتاج إلى تطوير". ممنوع إرجاع اسم المهارة وحده.

- لا تكرر نفس العبارة في strengths وgaps. يمكن أن تظهر المهارة في الاثنين فقط إذا ذكرت في كل منهما جانبًا مختلفًا ومحددًا.

- اجعل كل نقطة في strengths وgaps بين 5 و12 كلمة تقريبًا، وركّز على مفهوم تقني واحد فقط.

- feedback: اكتب جملة عربية واحدة قصيرة تلخص المستوى العام وأهم أولوية تطوير، بحد أقصى 25 كلمة.

- حافظ على مستوى طالب جامعي/متدرب؛ لا تبالغ في وصف الإجابة بأنها احترافية إذا لم تدعم ذلك.

"""



    user_prompt = f"""بيانات الطالب:

التخصص: {student.get('major', '')}

المستوى الأكاديمي: {student.get('academic_level', '')}

المهارات المسجلة: {', '.join(s['name'] + ' (' + str(s['level']) + ')' for s in student.get('skills', []))}



الفرصة:

المسمى: {opportunity.get('position', '')}

الوصف: {opportunity.get('description', '')}

المهارات المطلوبة: {', '.join(required)}



إجابات التقييم:

{qa_text}



أعد JSON بهذا الشكل:

{{

  "assessment_score": 0,

  "question_scores": [

    {{"question": 1, "score": 0, "reason": "..."}},

    {{"question": 2, "score": 0, "reason": "..."}},

    {{"question": 3, "score": 0, "reason": "..."}}

  ],

  "strengths": ["..."],

  "gaps": ["..."],

  "feedback": "..."

}}"""



    response = requests.post(

        f"{base_url}/chat/completions",

        headers={

            "Authorization": f"Bearer {api_key}",

            "Content-Type": "application/json",

        },

        json={

            "model": model,

            "temperature": 0.2,

            "messages": [

                {"role": "system", "content": system_prompt},

                {"role": "user", "content": user_prompt},

            ],

        },

        timeout=60,

    )

    response.raise_for_status()

    payload = response.json()



    try:

        content = payload["choices"][0]["message"]["content"]

    except (KeyError, IndexError, TypeError):

        raise ValueError("استجابة مزود الـLLM غير متوقعة.")



    result = _extract_json(content)



    score = float(result.get("assessment_score", 0))

    result["assessment_score"] = max(0.0, min(100.0, score))

    result["strengths"] = [str(x) for x in result.get("strengths", [])][:3]

    result["gaps"] = [str(x) for x in result.get("gaps", [])][:3]

    result["feedback"] = str(result.get("feedback", "")).strip()



    return result
