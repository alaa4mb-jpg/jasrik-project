from __future__ import annotations
import base64

import os
import streamlit as st
import streamlit.components.v1 as components

from matching import (
    config,
    level_label,
    normalize_interest,
    normalize_skill,
    opportunities,
    rank_opportunities,
    score_match,
)

from development import build_plan, reevaluate, skill_summary_ar
from llm_assessment import get_assessment_questions, evaluate_assessment, llm_is_configured

# ---------------------------------------------------------------------------
# إعداد الصفحة وتطبيق الهوية البصرية الرسمية لمنصة جِسرك (Jisrak)
# الألوان الأربعة المعتمدة:
# 1. Primary Blue:  #31516B (الثقة والاستقرار)
# 2. Teal Green:   #2E8B7F (الابتكار والتطوير والتقدم)
# 3. Beige:        #D7C9B1 (النمو والإبداع والدعم)
# 4. Off-White:    #F6F5F1 (الوضوح والبدايات الجديدة والخلفيات)
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="جِسرك | Jisrak — منصة مطابقة فرص التدريب التعاوني",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed",
)

CFG = config()
WEIGHTS = CFG["weights"]
LEVELS = CFG["level_labels"]

LEVEL_MAP = {
    "مبتدئ": 1,
    "متمكن": 2,
    "متقدم": 3,
    "خبير": 4,
}
REV_LEVEL_MAP = {v: k for k, v in LEVEL_MAP.items()}

# حقن كود التنسيق CSS المتطور والمبني حصرياً على الألوان الرسمية الأربعة
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"], .stMarkdown, .stText, p, span, h1, h2, h3, h4, h5, h6, input, button, select {
        direction: rtl !important;
        text-align: right !important;
        font-family: 'IBM Plex Sans Arabic', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* الخلفية العامة للمنصة: Off-White #F6F5F1 */
    .stApp {
        background-color: #F6F5F1 !important;
    }

    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 3.5rem !important;
        max-width: 1240px !important;
        width: calc(100% - 2rem) !important;
    }

    @media (max-width: 768px) {
        .block-container {
            width: calc(100% - 1rem) !important;
            padding-left: 0.5rem !important;
            padding-right: 0.5rem !important;
        }
    }

    /* لوحة الألوان الرسمية الدقيقة لمنصة جِسرك */
    :root {
        --jisrak-blue: #31516B;
        --jisrak-teal: #2E8B7F;
        --jisrak-beige: #D7C9B1;
        --jisrak-offwhite: #F6F5F1;
        --surface-white: #FFFFFF;
        --text-dark: #203342;
        --text-muted: #5B6D7A;
        --border-subtle: #E2DDD5;
    }

    /* رأس الصفحة والشعار (Navbar / Brand Header) */
    .brand-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 1.25rem 1.75rem;
        background: #FFFFFF;
        border: 1px solid var(--border-subtle);
        border-radius: 12px;
        margin-bottom: 1.25rem;
        box-shadow: 0 1px 3px rgba(59, 94, 122, 0.04);
    }
    .brand-logo-wrap {
        display: flex;
        align-items: center;
        gap: 1rem;
    }
    .brand-logo-icon {
        width: 48px;
        height: 48px;
        background: #31516B;
        color: #F6F5F1;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.45rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        box-shadow: 0 2px 5px rgba(59, 94, 122, 0.15);
    }
    .brand-title {
        font-size: 1.45rem;
        font-weight: 700;
        color: #31516B;
        margin: 0;
        line-height: 1.2;
    }
    .brand-tagline {
        font-size: 0.86rem;
        color: #5B6D7A;
        margin-top: 0.2rem;
    }
    .student-badge {
        background: #F6F5F1;
        padding: 0.45rem 0.95rem;
        border-radius: 8px;
        border: 1px solid var(--jisrak-beige);
        font-size: 0.82rem;
        color: #31516B;
    }

    /* بطاقات المحتوى (Cards) */
    .ui-card {
        background: #FFFFFF;
        border: 1px solid var(--border-subtle);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.15rem;
        box-shadow: 0 1px 2px rgba(59, 94, 122, 0.03);
    }
    .ui-card-subtle {
        background: #FFFFFF;
        border: 1px solid var(--border-subtle);
        border-radius: 10px;
        padding: 1.15rem;
        margin-bottom: 0.85rem;
    }
    .ui-card-highlight {
        background: rgba(215, 201, 177, 0.18);
        border: 1px solid var(--jisrak-beige);
        border-radius: 10px;
        padding: 1.15rem;
        margin-bottom: 0.85rem;
    }

    /* الشارات والتصنيفات (Badges) */
    .badge {
        display: inline-block;
        padding: 0.25rem 0.65rem;
        border-radius: 6px;
        font-size: 0.78rem;
        font-weight: 600;
    }
    .badge-blue    { background: rgba(59, 94, 122, 0.09); color: #31516B; border: 1px solid rgba(59, 94, 122, 0.22); }
    .badge-teal    { background: rgba(46, 139, 127, 0.10); color: #2E8B7F; border: 1px solid rgba(46, 139, 127, 0.25); }
    .badge-beige   { background: rgba(215, 201, 177, 0.35); color: #4A4031; border: 1px solid #D7C9B1; }
    .badge-neutral { background: #F6F5F1; color: #5B6D7A; border: 1px solid var(--border-subtle); }

    /* تفاصيل الفرص وبطاقة النتيجة الرئيسية (Match Score) */
    .match-hero-card {
        background: #FFFFFF;
        border: 1px solid var(--border-subtle);
        border-radius: 14px;
        padding: 1.75rem 2rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1.5rem;
        box-shadow: 0 1px 3px rgba(59, 94, 122, 0.04);
    }
    .match-score-box {
        text-align: center;
        min-width: 135px;
        padding: 1rem 1.25rem;
        border-radius: 12px;
        background: #F6F5F1;
        border: 1.5px solid var(--jisrak-teal);
    }
    .match-score-num {
        font-size: 2.3rem;
        font-weight: 800;
        line-height: 1;
        color: #2E8B7F;
        letter-spacing: -0.03em;
    }

    /* تحسين أزرار Streamlit لتتوافق مع الهوية */
    div.stButton > button[kind="primary"], div.stButton > button[data-testid="baseButton-primary"] {
        background-color: #31516B !important;
        color: #FFFFFF !important;
        border: 1px solid #31516B !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        padding: 0.55rem 1.2rem !important;
        box-shadow: 0 1px 2px rgba(59, 94, 122, 0.12) !important;
        transition: all 0.15s ease-in-out !important;
    }
    div.stButton > button[kind="primary"]:hover, div.stButton > button[data-testid="baseButton-primary"]:hover {
        background-color: #2E8B7F !important;
        border-color: #2E8B7F !important;
        color: #FFFFFF !important;
        transform: translateY(-1px);
        box-shadow: 0 3px 6px rgba(46, 139, 127, 0.18) !important;
    }
    div.stButton > button[kind="secondary"], div.stButton > button[data-testid="baseButton-secondary"] {
        background-color: #FFFFFF !important;
        color: #31516B !important;
        border: 1px solid var(--border-subtle) !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
        font-size: 0.9rem !important;
        padding: 0.55rem 1.2rem !important;
        transition: all 0.15s ease-in-out !important;
    }
    div.stButton > button[kind="secondary"]:hover, div.stButton > button[data-testid="baseButton-secondary"]:hover {
        border-color: #2E8B7F !important;
        color: #2E8B7F !important;
        background-color: #F6F5F1 !important;
    }

    /* حقول الإدخال والقوائم */
    .stTextInput input, .stTextArea textarea, .stSelectbox select {
        border-radius: 8px !important;
        border-color: var(--border-subtle) !important;
        background-color: #FFFFFF !important;
    }
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: #2E8B7F !important;
        box-shadow: 0 0 0 1px #2E8B7F !important;
    }

    /* إبقاء حقول الاختيار والقوائم المنسدلة باللون الأبيض */
    div[data-baseweb="select"] > div,
    .stSelectbox div[data-baseweb="select"] > div,
    .stMultiSelect div[data-baseweb="select"] > div,
    [data-testid="stSelectbox"] [role="group"],
    [data-testid="stSelectbox"] input[role="combobox"],
    [data-testid="stSelectbox"] button[aria-haspopup="listbox"],
    [data-testid="stMultiSelect"] [role="group"],
    [data-testid="stMultiSelect"] [data-testid="stMultiSelectTagsContainer"],
    [data-testid="stMultiSelect"] input[role="combobox"],
    [data-testid="stMultiSelect"] button[aria-haspopup="listbox"] {
        background-color: #FFFFFF !important;
        border-color: var(--border-subtle) !important;
        color: var(--text-dark) !important;
    }
    div[data-baseweb="popover"],
    div[data-baseweb="popover"] > div,
    ul[data-testid="stSelectboxVirtualDropdown"],
    ul[role="listbox"],
    li[role="option"] {
        background-color: #FFFFFF !important;
        color: var(--text-dark) !important;
    }

    /* شريط التقدم */
    .stProgress > div > div > div > div {
        background-color: #2E8B7F !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# إدارة الحالة (Session State)
# ---------------------------------------------------------------------------
def init_state() -> None:
    if "student" not in st.session_state:
        st.session_state.student = None
    if "selected_opp_id" not in st.session_state:
        st.session_state.selected_opp_id = None
    if "plan" not in st.session_state:
        st.session_state.plan = None
    if "step" not in st.session_state:
        st.session_state.step = "profile"
    if "reeval_result" not in st.session_state:
        st.session_state.reeval_result = None
    if "assessment_result" not in st.session_state:
        st.session_state.assessment_result = None

init_state()


def navigate_to(step: str) -> None:
    """انتقل إلى خطوة أخرى، ثم ابدأ عرضها من أعلى الصفحة."""
    st.session_state.step = step
    st.session_state.scroll_to_top = True
    st.rerun()


def scroll_to_top_if_requested() -> None:
    if not st.session_state.pop("scroll_to_top", False):
        return

    # Streamlit يغيّر حاوية التمرير حسب الإصدار. نجرّب الحاويات
    # الحالية والقديمة، ثم نعيد المحاولة بعد اكتمال الـDOM.
    components.html(
        """
        <script>
        (() => {
            const scrollTop = () => {
                try {
                    const doc = window.parent.document;
                    const selectors = [
                        '[data-testid="stAppViewContainer"]',
                        '[data-testid="stMain"]',
                        'section[data-testid="stMain"]',
                        '[data-testid="stMainBlockContainer"]',
                        '.main',
                        'section.main',
                        'main'
                    ];

                    selectors.forEach((selector) => {
                        doc.querySelectorAll(selector).forEach((el) => {
                            el.scrollTop = 0;
                            el.scrollLeft = 0;
                            if (typeof el.scrollTo === 'function') {
                                el.scrollTo({top: 0, left: 0, behavior: 'auto'});
                            }
                        });
                    });

                    doc.documentElement.scrollTop = 0;
                    doc.body.scrollTop = 0;
                    window.parent.scrollTo(0, 0);
                } catch (e) {
                    // بعض إصدارات Streamlit تعزل الـiframe؛ المحاولات الأخرى تكفي.
                }
            };

            scrollTop();
            requestAnimationFrame(scrollTop);
            setTimeout(scrollTop, 50);
            setTimeout(scrollTop, 150);
            setTimeout(scrollTop, 350);
            setTimeout(scrollTop, 700);
        })();
        </script>
        """,
        height=0,
    )


STEPS = [
    ("profile", "١. الملف الشخصي"),
    ("opportunities", "٢. فرص التدريب"),
    ("match", "٣. تفاصيل المطابقة"),
    ("assessment", "٤. التقييم الذكي"),
    ("plan", "٥. خطة التطوير"),
    ("reeval", "٦. إعادة التقييم"),
]

# ---------------------------------------------------------------------------
# المكونات الإضافية المساعدة
# ---------------------------------------------------------------------------
def get_selected_opportunity() -> dict | None:
    oid = st.session_state.selected_opp_id
    if not oid:
        return None
    for o in opportunities():
        if o["opportunity_id"] == oid:
            return o
    return None

def render_top_header() -> None:
    student_info_html = ""
    if st.session_state.student:
        s = st.session_state.student
        student_info_html = (
            f'<div class="student-badge">'
            f'<span>الطالب: <strong>{s["name"]}</strong></span> • '
            f'<span>{s["major"]}</span> • '
            f'<span>{s["academic_level"]}</span>'
            f'</div>'
        )
    else:
        student_info_html = '<div class="student-badge" style="color:#5B6D7A;">يرجى إكمال الملف الشخصي لبدء المطابقة</div>'

    # شعار جِسرك الرسمي الملون مع العبارة وبدون خلفية
    logo_candidates = [
        "jasrak_logo_transparent.png",
        "jasrak_logo_web.png",
        "logo.png",
        "assets/jasrak_logo_transparent.png",
        "assets/logo.png",
    ]
    logo_src = "data:image/png;base64,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"
    for cand in logo_candidates:
        if os.path.exists(cand):
            try:
                with open(cand, "rb") as lf:
                    b64_local = base64.b64encode(lf.read()).decode("utf-8")
                    logo_src = f"data:image/png;base64,{b64_local}"
                    break
            except Exception:
                pass

    st.markdown(
        f"""
        <div class="brand-header">
            <div class="brand-logo-wrap" style="align-items: center;">
                <img src="{logo_src}" alt="شعار جِسرك — مسارك .. من الفجوة إلى الفرصة" style="height: 68px; width: auto; object-fit: contain; filter: drop-shadow(0 2px 4px rgba(59, 94, 122, 0.08));">
                <div style="display: flex; flex-direction: column; justify-content: center; margin-right: 0.5rem;">
                    <div style="font-size: 0.88rem; font-weight: 600; color: #31516B; letter-spacing: -0.01em;"> منظومة ذكية لمطابقة الطلاب بفرص التدريب التعاوني <br>وسد الفجوات المهارية </div>
                </div>
            </div>
            {student_info_html}
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_stepper() -> None:
    step_keys = [k for k, _ in STEPS]
    current_idx = step_keys.index(st.session_state.step)
    has_student = st.session_state.student is not None
    has_opp = st.session_state.selected_opp_id is not None
    has_plan = st.session_state.plan is not None

    cols = st.columns(len(STEPS))
    for i, (key, label) in enumerate(STEPS):
        is_disabled = False
        if key in ("opportunities", "match", "assessment", "plan", "reeval") and not has_student:
            is_disabled = True
        elif key in ("match", "assessment", "plan", "reeval") and not has_opp:
            is_disabled = True
        elif key in ("plan", "reeval") and not has_plan and key != "plan":
            is_disabled = True

        with cols[i]:
            btn_type = "primary" if key == st.session_state.step else "secondary"
            # إذا كانت الخطوة منجزة وسابقة، نعطيها تلميح الإنجاز
            step_tag = label
            if i < current_idx and not is_disabled:
                step_tag = f"✓ {label}"

            if st.button(
                step_tag,
                key=f"stepper_btn_{key}",
                disabled=is_disabled,
                type=btn_type,
                use_container_width=True,
            ):
                navigate_to(key)

    st.markdown("<div style='margin-bottom: 1.25rem;'></div>", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# الصفحة 1: الملف الشخصي (Profile)
# ---------------------------------------------------------------------------
def page_profile() -> None:
    current = st.session_state.student or {}

    col_title, col_actions = st.columns([2.2, 1])
    with col_title:
        st.markdown("<h2 style='font-size:1.35rem; font-weight:700; color:#31516B; margin-bottom:0.25rem;'>الملف الشخصي للطالب</h2>", unsafe_allow_html=True)
        st.markdown("<p style='font-size:0.88rem; color:#5B6D7A; margin-top:0;'>أدخل بياناتك الأكاديمية ومهاراتك بدقة لحساب نسبة المطابقة التلقائية مع فرص التدريب.</p>", unsafe_allow_html=True)
    with col_actions:
        if st.session_state.student and st.button("مسح البيانات", use_container_width=True):
            st.session_state.student = None
            st.session_state.plan = None
            st.session_state.selected_opp_id = None
            st.session_state.reeval_result = None
            st.session_state.assessment_result = None
            st.rerun()

    st.markdown("<hr style='border:none; border-top:1px solid #E2DDD5; margin:1rem 0;'>", unsafe_allow_html=True)

    # قسم 1: البيانات الأكاديمية
    st.markdown("<h3 style='font-size:1.05rem; font-weight:600; color:#31516B; margin-bottom:0.75rem;'>١. البيانات الأكاديمية</h3>", unsafe_allow_html=True)
    
    col_name, col_major, col_level = st.columns([1.2, 1.2, 1])
    with col_name:
        name = st.text_input("اسم الطالب الثلاثي", value=current.get("name", ""))
    with col_major:
        major_options = ["اختر تخصصك"] + CFG["majors"]
        current_major = current.get("major", "")
        major_index = major_options.index(current_major) if current_major in major_options else 0
        major = st.selectbox("التخصص الأكاديمي", major_options, index=major_index)
    with col_level:
        academic_options = ["اختر مستواك الدراسي"] + CFG["academic_levels"]
        current_academic = current.get("academic_level", "")
        academic_index = academic_options.index(current_academic) if current_academic in academic_options else 0
        academic = st.selectbox("المستوى الدراسي", academic_options, index=academic_index)

    st.markdown("<div style='margin-bottom:1.5rem;'></div>", unsafe_allow_html=True)

    # قسم 2: المهارات ومستوى الإتقان (مبتدئ / متمكن / متقدم / خبير) دون أرقام
    st.markdown("<h3 style='font-size:1.05rem; font-weight:600; color:#31516B; margin-bottom:0.25rem;'>٢. المهارات ومستوى الإتقان</h3>", unsafe_allow_html=True)
    st.markdown("<p style='font-size:0.84rem; color:#5B6D7A; margin-bottom:0.75rem;'>اختر مهاراتك من القائمة، ثم حدد مستوى إتقانك لكل مهارة (مبتدئ / متمكن / متقدم / خبير).</p>", unsafe_allow_html=True)

    all_skills = sorted(set(CFG["skill_aliases"].values()))
    current_skill_dict = {
        normalize_skill(s["name"]): s["level"]
        for s in current.get("skills", [])
    }

    selected_skills = st.multiselect(
        "اختر المهارات التقنية والعملية",
        all_skills,
        default=[s for s in current_skill_dict.keys() if s in all_skills],
        placeholder="انقر لاختيار مهاراتك...",
    )

    skill_levels: dict[str, int] = {}
    if selected_skills:
        st.markdown("<div style='margin-top:0.5rem; margin-bottom:0.5rem;'>", unsafe_allow_html=True)
        for skill in selected_skills:
            existing_lvl = current_skill_dict.get(skill, 2)
            default_label = REV_LEVEL_MAP.get(existing_lvl, "متمكن")
            level_keys = list(LEVEL_MAP.keys())
            def_idx = level_keys.index(default_label) if default_label in level_keys else 1

            col_s_name, col_s_choice = st.columns([1, 2])
            with col_s_name:
                st.markdown(f"<div style='padding-top:0.4rem; font-weight:600; color:#203342;'>• {skill}</div>", unsafe_allow_html=True)
            with col_s_choice:
                chosen = st.radio(
                    f"مستوى {skill}",
                    options=level_keys,
                    index=def_idx,
                    horizontal=True,
                    key=f"skill_level_radio_{skill}",
                    label_visibility="collapsed",
                )
                skill_levels[skill] = LEVEL_MAP[chosen]
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("لم تقم باختيار أي مهارات بعد. اختر مهارة واحدة على الأقل للمتابعة.")

    st.markdown("<div style='margin-bottom:1.5rem;'></div>", unsafe_allow_html=True)

    # قسم 3: الاهتمامات والخبرة
    col_int, col_exp = st.columns([1.5, 1])
    with col_int:
        st.markdown("<h3 style='font-size:1.05rem; font-weight:600; color:#31516B; margin-bottom:0.25rem;'>٣. مجالات الاهتمام</h3>", unsafe_allow_html=True)
        st.markdown("<p style='font-size:0.84rem; color:#5B6D7A; margin-bottom:0.75rem;'>المجالات الوظيفية والتقنية التي ترغب بالتدرب فيها.</p>", unsafe_allow_html=True)
        current_interests = [normalize_interest(i) for i in current.get("interests", [])]
        interests = st.multiselect(
            "المجالات والاهتمامات",
            CFG["interests"],
            default=[i for i in current_interests if i in CFG["interests"]],
            label_visibility="collapsed",
            placeholder="اختر مجالات اهتمامك...",
        )
    with col_exp:
        st.markdown("<h3 style='font-size:1.05rem; font-weight:600; color:#31516B; margin-bottom:0.25rem;'>٤. مستوى الخبرة السابقة</h3>", unsafe_allow_html=True)
        st.markdown("<p style='font-size:0.84rem; color:#5B6D7A; margin-bottom:0.75rem;'>المشاريع أو التدريب السابق إن وجد.</p>", unsafe_allow_html=True)
        exp_labels_dict = CFG["experience_labels"]
        exp_options = {v: int(k) for k, v in exp_labels_dict.items()}
        current_exp_num = int(current.get("experience_level", 1))
        current_exp_str = exp_labels_dict.get(str(current_exp_num), list(exp_options.keys())[0])
        exp_choice = st.selectbox(
            "مستوى الخبرة",
            list(exp_options.keys()),
            index=list(exp_options.keys()).index(current_exp_str) if current_exp_str in exp_options else 0,
            label_visibility="collapsed",
        )
        experience_level = exp_options[exp_choice]

    st.markdown("<div style='margin-bottom:1.5rem;'></div>", unsafe_allow_html=True)

    # قسم 4: الشهادات الإضافية
    st.markdown("<h3 style='font-size:1.05rem; font-weight:600; color:#31516B; margin-bottom:0.25rem;'>٥. الشهادات المهنية (اختياري)</h3>", unsafe_allow_html=True)
    certs_text = st.text_input(
        "اكتب الشهادات التي حصلت عليها مفصولة بفواصل (مثال: Google Data Analytics, AWS Cloud Practitioner)",
        value=", ".join(current.get("certifications", [])),
    )

    st.markdown("<div style='margin-bottom:1.75rem;'></div>", unsafe_allow_html=True)

    # زر الحفظ والانتقال (Primary Blue #31516B)
    col_save, _ = st.columns([1.2, 1])
    with col_save:
        if st.button("حفظ الملف والانتقال للفرص ←", type="primary", use_container_width=True):
            if major == "اختر تخصصك":
                st.error("يرجى تحديد تخصصك الأكاديمي أولاً.")
                return
            if academic == "اختر مستواك الدراسي":
                st.error("يرجى تحديد مستواك الدراسي أولاً.")
                return
            if not skill_levels:
                st.error("يرجى إضافة مهارة واحدة على الأقل.")
                return

            certs = [c.strip() for c in certs_text.split(",") if c.strip()]

            st.session_state.student = {
                "student_id": current.get("student_id", "student_001"),
                "name": name.strip() or "طالب",
                "major": major,
                "academic_level": academic,
                "skills": [{"name": k, "level": v} for k, v in skill_levels.items()],
                "interests": interests,
                "experience_level": experience_level,
                "experience_note": current.get("experience_note", ""),
                "certifications": certs,
            }

            st.session_state.plan = None
            st.session_state.reeval_result = None
            navigate_to("opportunities")


# ---------------------------------------------------------------------------
# الصفحة 2: فرص التدريب (Opportunities)
# ---------------------------------------------------------------------------
def page_opportunities() -> None:
    student = st.session_state.student
    if not student:
        st.warning("يرجى تعبئة ملفك الشخصي أولاً للبدء بمطابقة الفرص.")
        if st.button("الذهاب إلى الملف الشخصي"):
            navigate_to("profile")
        return

    ranked = rank_opportunities(student)

    st.markdown("<h2 style='font-size:1.35rem; font-weight:700; color:#31516B; margin-bottom:0.25rem;'>فرص التدريب المتاحة</h2>", unsafe_allow_html=True)
    st.markdown(f"<p style='font-size:0.88rem; color:#5B6D7A; margin-bottom:1.5rem;'>الفرص مرتبة آلياً وفقاً لنسبة المطابقة مع ملف <strong>{student['name']}</strong> ({student['major']}).</p>", unsafe_allow_html=True)

    for item in ranked:
        opp = item["opportunity"]
        match = item["match"]
        score = match["final_score"]
        band_label = match["band_label"]

        req_skills_html = "".join(
            f'<span class="badge badge-neutral" style="margin-left:0.35rem; margin-top:0.35rem;">{s["name"]} ({REV_LEVEL_MAP.get(s["level"], "متمكن")})</span>'
            for s in opp.get("required_skills", [])
        )
        paid_badge = '<span class="badge badge-teal">مدفوع</span>' if opp.get("is_paid") else '<span class="badge badge-neutral">غير مدفوع</span>'

        with st.container():
            st.markdown(
                f"""
                <div class="ui-card">
                    <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:0.75rem;">
                        <div>
                            <div style="font-size:1.15rem; font-weight:700; color:#31516B;">{opp['position']}</div>
                            <div style="font-size:0.9rem; color:#5B6D7A; margin-top:0.25rem; font-weight:500;">
                                🏢 <strong>{opp['company']}</strong> • 📍 {opp['location']} • ⏱️ {opp['duration_months']} أشهر • {paid_badge}
                            </div>
                        </div>
                        <div style="text-align:center; min-width:115px; background:#F6F5F1; padding:0.55rem 0.9rem; border-radius:10px; border:1px solid #D7C9B1;">
                            <div style="font-size:1.55rem; font-weight:800; color:#2E8B7F; line-height:1;">{score:.0f}%</div>
                            <div style="font-size:0.75rem; font-weight:600; color:#31516B; margin-top:0.25rem;">{band_label}</div>
                        </div>
                    </div>
                    <div style="font-size:0.86rem; color:#5B6D7A; margin-bottom:0.85rem; line-height:1.5;">{opp.get('description', '')}</div>
                    <div style="display:flex; align-items:center; flex-wrap:wrap; gap:0.35rem; margin-bottom:0.75rem;">
                        <span style="font-size:0.8rem; font-weight:600; color:#31516B; margin-left:0.25rem;">المهارات المطلوبة:</span>
                        {req_skills_html}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            col_btn, _ = st.columns([1.5, 3])
            with col_btn:
                if st.button("عرض تفاصيل المطابقة ←", key=f"opp_view_{opp['opportunity_id']}", use_container_width=True):
                    st.session_state.selected_opp_id = opp["opportunity_id"]
                    st.session_state.plan = None
                    st.session_state.reeval_result = None
                    st.session_state.assessment_result = None
                    navigate_to("match")

            st.markdown("<div style='margin-bottom:0.75rem;'></div>", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# الصفحة 3: تفاصيل المطابقة (Match Details)
# ---------------------------------------------------------------------------
def page_match() -> None:
    opp = get_selected_opportunity()
    student = st.session_state.student

    if not opp or not student:
        st.warning("لم يتم اختيار فرصة بعد. يرجى اختيار فرصة من القائمة.")
        if st.button("العودة إلى قائمة الفرص"):
            navigate_to("opportunities")
        return

    match = score_match(student, opp)
    score = match["final_score"]
    band_label = match["band_label"]

    # رأس تفاصيل المطابقة بالألوان الرسمية (Hero Score Card)
    st.markdown(
        f"""
        <div class="match-hero-card">
            <div>
                <div style="font-size:1.35rem; font-weight:700; color:#31516B;">{opp['position']}</div>
                <div style="font-size:0.95rem; color:#5B6D7A; margin-top:0.25rem;">
                    🏢 <strong>{opp['company']}</strong> • {opp['location']} • {opp['duration_months']} أشهر
                </div>
                <div style="font-size:0.86rem; color:#5B6D7A; margin-top:0.5rem; max-width:620px;">
                    {opp.get('description', '')}
                </div>
            </div>
            <div class="match-score-box">
                <div class="match-score-num">{score:.0f}%</div>
                <div style="font-size:0.84rem; font-weight:700; color:#31516B; margin-top:0.35rem;">{band_label}</div>
                <div style="font-size:0.75rem; color:#5B6D7A; margin-top:0.2rem;">Match Score</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # تفصيل محاور التقييم الأربعة (Dimensions)
    st.markdown("<h3 style='font-size:1.1rem; font-weight:700; color:#31516B; margin-bottom:0.75rem;'>تحليل أبعاد المطابقة</h3>", unsafe_allow_html=True)
    dim_cols = st.columns(4)
    for i, d in enumerate(match["dimensions"]):
        with dim_cols[i]:
            st.markdown(
                f"""
                <div class="ui-card-subtle" style="text-align:center; padding:1rem; border-top: 3px solid #31516B;">
                    <div style="font-size:0.84rem; font-weight:600; color:#5B6D7A;">{d['label']}</div>
                    <div style="font-size:1.4rem; font-weight:700; color:#2E8B7F; margin:0.35rem 0;">{d['score']:.0f}%</div>
                    <div style="font-size:0.75rem; color:#5B6D7A;">الوزن: {int(d['weight']*100)}%</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("<div style='margin-bottom:1.5rem;'></div>", unsafe_allow_html=True)

    # أسباب وتبريرات المطابقة
    st.markdown("<h3 style='font-size:1.1rem; font-weight:700; color:#31516B; margin-bottom:0.75rem;'>لماذا تناسبك هذه الفرصة؟</h3>", unsafe_allow_html=True)
    with st.container():
        reasons_list = []
        for d in match["dimensions"]:
            for r in d.get("reasons", []):
                reasons_list.append(f"• {r}")

        st.markdown(
            f"""
            <div class="ui-card" style="padding:1.25rem 1.5rem;">
                <div style="font-size:0.88rem; color:#203342; line-height:1.7;">
                    {"<br>".join(reasons_list)}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='margin-bottom:1.5rem;'></div>", unsafe_allow_html=True)

    # فجوات المهارات (Skill Gaps) مع تمثيل ألوان الهوية: الأزرق للحالي، التيل للمطلوب، البيج للإبراز
    st.markdown("<h3 style='font-size:1.1rem; font-weight:700; color:#31516B; margin-bottom:0.75rem;'>فجوات المهارات (Skill Gaps)</h3>", unsafe_allow_html=True)
    
    required_gaps = [g for g in match["gaps"] if not g["is_preferred"]]
    preferred_gaps = [g for g in match["gaps"] if g["is_preferred"]]

    col_req_gaps, col_pref_gaps = st.columns(2)

    with col_req_gaps:
        st.markdown("<div style='font-weight:600; font-size:0.92rem; color:#31516B; margin-bottom:0.5rem;'>المهارات الأساسية المطلوبة:</div>", unsafe_allow_html=True)
        if not required_gaps:
            st.markdown('<div class="ui-card-subtle" style="color:#2E8B7F; font-size:0.86rem; border-color:#2E8B7F;">✓ مهاراتك تغطي كافة المتطلبات الأساسية لهذه الفرصة.</div>', unsafe_allow_html=True)
        else:
            for g in required_gaps:
                if g["is_missing"]:
                    st.markdown(
                        f"""
                        <div class="ui-card-subtle" style="border-right:3.5px solid #5B6D7A; margin-bottom:0.5rem;">
                            <div style="font-weight:700; color:#31516B; font-size:0.92rem;">{g['skill']}</div>
                            <div style="font-size:0.82rem; color:#5B6D7A; margin-top:0.2rem;">الحالة: غير متوفرة حالياً في ملفك</div>
                            <div style="font-size:0.82rem; color:#2E8B7F; margin-top:0.15rem;">المستوى المطلوب: <strong>{g['required_label']}</strong></div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        f"""
                        <div class="ui-card-subtle" style="border-right:3.5px solid #D7C9B1; margin-bottom:0.5rem;">
                            <div style="font-weight:700; color:#31516B; font-size:0.92rem;">{g['skill']}</div>
                            <div style="font-size:0.82rem; color:#5B6D7A; margin-top:0.2rem;">
                                مستواك الحالي: <strong style="color:#31516B;">{g['student_label']}</strong> ← المطلوب: <strong style="color:#2E8B7F;">{g['required_label']}</strong>
                            </div>
                            <div style="font-size:0.8rem; color:#5B6D7A; margin-top:0.15rem;">الفجوة: {g['gap_label']}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

    with col_pref_gaps:
        st.markdown("<div style='font-weight:600; font-size:0.92rem; color:#2E8B7F; margin-bottom:0.5rem;'>مهارات إضافية مفضلة (تحسينية):</div>", unsafe_allow_html=True)
        if not preferred_gaps:
            st.markdown('<div class="ui-card-subtle" style="color:#5B6D7A; font-size:0.86rem;">لا توجد مهارات مفضلة إضافية مطلوبة.</div>', unsafe_allow_html=True)
        else:
            for g in preferred_gaps:
                st.markdown(
                    f"""
                    <div class="ui-card-subtle" style="border-right:3.5px solid #2E8B7F; margin-bottom:0.5rem;">
                        <div style="font-weight:700; color:#31516B; font-size:0.92rem;">{g['skill']}</div>
                        <div style="font-size:0.82rem; color:#5B6D7A; margin-top:0.2rem;">
                            مستواك: <strong style="color:#31516B;">{g['student_label']}</strong> • المطلوب: <strong style="color:#2E8B7F;">{g['required_label']}</strong>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    if match.get("matched_skills"):
        st.markdown("<div style='margin-top:1rem;'></div>", unsafe_allow_html=True)
        st.markdown("<span style='font-weight:600; font-size:0.88rem; color:#31516B;'>المهارات المتوافقة تماماً: </span>", unsafe_allow_html=True)
        matched_html = " ".join([f'<span class="badge badge-teal">{s}</span>' for s in match["matched_skills"]])
        st.markdown(matched_html, unsafe_allow_html=True)

    st.markdown("<div style='margin-bottom:2rem;'></div>", unsafe_allow_html=True)

    col_next, col_back = st.columns([1.5, 1])
    with col_next:
        if st.button("بدء التقييم الذكي ←", type="primary", use_container_width=True):
            st.session_state.assessment_result = None
            navigate_to("assessment")
    with col_back:
        if st.button("← العودة لقائمة الفرص", use_container_width=True):
            navigate_to("opportunities")


# ---------------------------------------------------------------------------
# الصفحة 4: التقييم الذكي (LLM Assessment)
# ---------------------------------------------------------------------------
def page_assessment() -> None:
    opp = get_selected_opportunity()
    student = st.session_state.student

    if not opp or not student:
        st.warning("لم يتم اختيار فرصة بعد. يرجى اختيار فرصة من القائمة.")
        if st.button("العودة إلى قائمة الفرص"):
            navigate_to("opportunities")
        return

    result = st.session_state.assessment_result

    st.markdown(
        "<h2 style='font-size:1.35rem; font-weight:700; color:#31516B; margin-bottom:0.25rem;'>التقييم الذكي</h2>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<p style='font-size:0.88rem; color:#5B6D7A; margin-bottom:1.25rem;'>"
        f"أجب عن 3 أسئلة قصيرة مرتبطة بمتطلبات فرصة <strong>{opp['position']}</strong>. "
        f"سيحلل النموذج إجاباتك ويحدد نقاط القوة والجوانب التي تحتاج إلى تطوير.</p>",
        unsafe_allow_html=True,
    )

    if not llm_is_configured():
        st.error(
            "لم يتم إعداد مفتاح نموذج اللغة بعد. أضف LLM_API_KEY في ملف .env ثم أعد تشغيل التطبيق."
        )
        st.code(
            "LLM_API_KEY=your_api_key\n"
            "LLM_BASE_URL=https://api.deepseek.com\n"
            "LLM_MODEL=deepseek-chat",
            language="text",
        )
        return

    questions = get_assessment_questions(opp)

    answers = []
    for i, question in enumerate(questions, start=1):
        st.markdown(
            f"<div class='ui-card-subtle' style='margin-bottom:0.45rem;'>"
            f"<div style='font-size:0.82rem; color:#2E8B7F; font-weight:700;'>السؤال {i}</div>"
            f"<div style='font-size:0.95rem; color:#203342; font-weight:600; margin-top:0.25rem;'>{question['question']}</div>"
            f"<div style='font-size:0.76rem; color:#5B6D7A; margin-top:0.3rem;'>المهارة: {question['skill']}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )
        answers.append(
            st.text_area(
                f"إجابتك عن السؤال {i}",
                key=f"assessment_answer_{opp['opportunity_id']}_{i}",
                height=120,
                placeholder="اكتب إجابتك باختصار ووضوح...",
                label_visibility="collapsed",
            )
        )
        st.markdown("<div style='margin-bottom:0.6rem;'></div>", unsafe_allow_html=True)

    col_submit, col_back = st.columns([1.5, 1])
    with col_submit:
        if st.button("تحليل الإجابات بالذكاء الاصطناعي ←", type="primary", use_container_width=True):
            if any(not a.strip() for a in answers):
                st.warning("يرجى الإجابة عن الأسئلة الثلاثة قبل بدء التقييم.")
            else:
                with st.spinner("يجري تحليل إجاباتك..."):
                    try:
                        st.session_state.assessment_result = evaluate_assessment(
                            student=student,
                            opportunity=opp,
                            questions=questions,
                            answers=answers,
                        )
                        st.rerun()
                    except Exception as exc:
                        st.error(f"تعذر إكمال التقييم: {exc}")

    with col_back:
        if st.button("← العودة لتفاصيل المطابقة", use_container_width=True):
            navigate_to("match")

    result = st.session_state.assessment_result
    if result:
        st.markdown("<div style='margin-top:1.5rem;'></div>", unsafe_allow_html=True)
        st.markdown(
            f"""
            <div class="match-hero-card">
                <div>
                    <div style="font-size:1.05rem; font-weight:700; color:#31516B;">نتيجة التقييم الذكي</div>
                    <div style="font-size:0.84rem; color:#5B6D7A; margin-top:0.3rem;">
                        التقييم مبني على إجاباتك عن المهارات المرتبطة بهذه الفرصة.
                    </div>
                </div>
                <div class="match-score-box">
                    <div class="match-score-num">{result['assessment_score']:.0f}%</div>
                    <div style="font-size:0.75rem; color:#5B6D7A; margin-top:0.2rem;">AI Assessment</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("<h3 style='font-size:1.05rem; color:#31516B;'>نقاط القوة</h3>", unsafe_allow_html=True)
            if result.get("strengths"):
                for item in result["strengths"]:
                    st.markdown(f"- {item}")
            else:
                st.markdown("لم تُحدد نقاط قوة واضحة ضمن الإجابات.")

        with c2:
            st.markdown("<h3 style='font-size:1.05rem; color:#31516B;'>جوانب تحتاج إلى تطوير</h3>", unsafe_allow_html=True)
            if result.get("gaps"):
                for item in result["gaps"]:
                    st.markdown(f"- {item}")
            else:
                st.markdown("لم تُحدد فجوات واضحة ضمن الإجابات.")

        st.markdown("<div class='ui-card' style='margin-top:0.75rem;'>"
                    "<div style='font-size:0.9rem; font-weight:700; color:#31516B;'>ملاحظات النموذج</div>"
                    f"<div style='font-size:0.88rem; color:#203342; line-height:1.8; margin-top:0.4rem;'>{result.get('feedback','')}</div>"
                    "</div>", unsafe_allow_html=True)

        if st.button("الانتقال إلى خطة التطوير المقترحة ←", type="primary", use_container_width=True):
            match = score_match(student, opp)
            st.session_state.plan = build_plan(
                student, opp, match["gaps"], match["final_score"]
            )
            navigate_to("plan")


# ---------------------------------------------------------------------------
# الصفحة 5: خطة التطوير (Personalized Development Plan)
# ---------------------------------------------------------------------------
def page_plan() -> None:
    opp = get_selected_opportunity()
    plan = st.session_state.plan

    if not opp or not plan:
        st.warning("لا توجد خطة تطوير حالية. يرجى اختيار فرصة تدريب أولاً.")
        if st.button("العودة إلى الفرص"):
            navigate_to("opportunities")
        return

    tasks = plan.get("tasks", [])
    completed_count = sum(1 for t in tasks if t.get("completed", False))

    # بطاقة ملخص الخطة بالألوان الرسمية: الأزرق، التيل، البيج
    st.markdown(
        f"""
        <div class="ui-card" style="display:flex; justify-content:space-between; align-items:center;">
            <div>
                <h2 style="font-size:1.3rem; font-weight:700; color:#31516B; margin:0;">خطة التطوير المقترحة</h2>
                <div style="font-size:0.88rem; color:#5B6D7A; margin-top:0.25rem;">
                    الفرصة: <strong>{opp['position']}</strong> لدى <strong>{opp['company']}</strong>
                </div>
            </div>
            <div style="display:flex; gap:1.5rem; text-align:center;">
                <div>
                    <div style="font-size:1.35rem; font-weight:700; color:#31516B;">{plan['baseline_score']:.0f}%</div>
                    <div style="font-size:0.75rem; color:#5B6D7A;">النتيجة الحالية</div>
                </div>
                <div>
                    <div style="font-size:1.35rem; font-weight:700; color:#2E8B7F;">{plan['total_hours']} س</div>
                    <div style="font-size:0.75rem; color:#5B6D7A;">إجمالي الساعات</div>
                </div>
                <div>
                    <div style="font-size:1.35rem; font-weight:700; color:#31516B;">{completed_count} / {len(tasks)}</div>
                    <div style="font-size:0.75rem; color:#5B6D7A;">المهام المنجزة</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not tasks:
        st.success("تهانينا! لا توجد فجوات مهارية تتطلب خطة تطوير لهذه الفرصة، فأنت مؤهل لها بالكامل.")
        if st.button("العودة إلى الفرص"):
            navigate_to("opportunities")
        return

    st.markdown("<p style='font-size:0.88rem; color:#5B6D7A;'>أكمل الخطوات التالية لسد الفجوة بين مستواك الحالي والمتطلبات، وحدد المهام المنجزة لتجربة إعادة التقييم.</p>", unsafe_allow_html=True)

    changed = False
    for i, task in enumerate(tasks):
        is_done = task.get("completed", False)
        border_accent = "#2E8B7F" if is_done else "#D7C9B1"

        with st.container():
            st.markdown(
                f"""
                <div class="ui-card" style="border-right: 4.5px solid {border_accent}; padding:1.25rem 1.5rem; margin-bottom:0.75rem;">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.5rem;">
                        <div style="font-size:1.05rem; font-weight:700; color:#31516B;">
                            #{task['priority']} • مهارة: {task['skill']}
                        </div>
                        <span class="badge badge-teal">المدة المقدرة: {task['estimated_hours']} ساعة</span>
                    </div>
                    <div style="font-size:0.84rem; color:#5B6D7A; margin-bottom:0.6rem;">
                        المستوى الحالي: <strong style="color:#31516B;">{task['current_label']}</strong> ← المستوى المستهدف: <strong style="color:#2E8B7F;">{task['target_label']}</strong>
                    </div>
                    <div style="background:#F6F5F1; border-radius:8px; border:1px solid #E2DDD5; padding:0.85rem; font-size:0.85rem; line-height:1.6; margin-bottom:0.6rem;">
                        <div><strong style="color:#31516B;">📌 الإجراء المقترح:</strong> {task['action']}</div>
                        <div style="margin-top:0.3rem;"><strong style="color:#2E8B7F;">🎯 الدليل العملي المطلوب:</strong> {task['evidence']}</div>
                        {f'<div style="margin-top:0.3rem; color:#31516B;"><strong>🔗 المصدر التعليمي:</strong> {task["resource"]}</div>' if task.get("resource") else ''}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            done_check = st.checkbox(
                f"أنجزت مهمة تطوير مهارة ({task['skill']})",
                value=is_done,
                key=f"task_check_{i}",
            )
            if done_check != is_done:
                task["completed"] = done_check
                changed = True

    if changed:
        st.session_state.plan = plan

    st.markdown("<div style='margin-bottom:1.5rem;'></div>", unsafe_allow_html=True)

    col_reeval, col_back = st.columns([1.5, 1])
    with col_reeval:
        if st.button("إعادة التقييم وعرض النتيجة الجديدة ←", type="primary", use_container_width=True):
            st.session_state.reeval_result = reevaluate(st.session_state.student, opp, plan)
            navigate_to("reeval")
    with col_back:
        if st.button("← العودة لتفاصيل المطابقة", use_container_width=True):
            navigate_to("match")


# ---------------------------------------------------------------------------
# الصفحة 5: إعادة التقييم (Re-evaluation)
# ---------------------------------------------------------------------------
def page_reeval() -> None:
    opp = get_selected_opportunity()
    plan = st.session_state.plan
    result = st.session_state.reeval_result

    if not opp or not plan:
        st.warning("لا توجد خطة لإعادة التقييم. يرجى البدء من صفحة الفرص.")
        if st.button("العودة إلى الفرص"):
            navigate_to("opportunities")
        return

    if result is None:
        result = reevaluate(st.session_state.student, opp, plan)
        st.session_state.reeval_result = result

    before_score = result["before"]
    after_score = result["after"]
    diff = result["improvement"]
    before_band = result["before_band"]
    after_band = result["after_band"]

    st.markdown("<h2 style='font-size:1.35rem; font-weight:700; color:#31516B; margin-bottom:0.25rem;'>نتائج إعادة تقييم الجاهزية</h2>", unsafe_allow_html=True)
    st.markdown(f"<p style='font-size:0.88rem; color:#5B6D7A; margin-bottom:1.5rem;'>مقارنة نسبة المطابقة قبل وبعد إنجاز المهام التطويرية لفرصة <strong>{opp['position']}</strong>.</p>", unsafe_allow_html=True)

    # مقارنة Before / After بصرية واضحة وفق الهوية الرسمية
    col_b, col_arrow, col_a, col_diff = st.columns([1.2, 0.4, 1.2, 1])
    with col_b:
        st.markdown(
            f"""
            <div class="ui-card-subtle" style="text-align:center; padding:1.25rem;">
                <div style="font-size:0.84rem; color:#5B6D7A; font-weight:600;">قبل التطوير</div>
                <div style="font-size:2.2rem; font-weight:800; color:#5B6D7A; margin:0.35rem 0;">{before_score:.0f}%</div>
                <div class="badge badge-neutral">{before_band}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_arrow:
        st.markdown("<div style='font-size:2rem; text-align:center; padding-top:1.75rem; color:#D7C9B1;'>←</div>", unsafe_allow_html=True)
    with col_a:
        st.markdown(
            f"""
            <div class="ui-card-subtle" style="text-align:center; padding:1.25rem; border-color:#2E8B7F; background:rgba(46, 139, 127, 0.04);">
                <div style="font-size:0.84rem; color:#2E8B7F; font-weight:600;">بعد التطوير</div>
                <div style="font-size:2.2rem; font-weight:800; color:#2E8B7F; margin:0.35rem 0;">{after_score:.0f}%</div>
                <div class="badge badge-teal">{after_band}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_diff:
        st.markdown(
            f"""
            <div class="ui-card-subtle" style="text-align:center; padding:1.25rem; border-color:#D7C9B1; background:rgba(215, 201, 177, 0.18);">
                <div style="font-size:0.84rem; color:#31516B; font-weight:600;">مقدار التحسن</div>
                <div style="font-size:2.2rem; font-weight:800; color:#31516B; margin:0.35rem 0;">+{diff:.0f}%</div>
                <div class="badge badge-beige">زيادة في الجاهزية</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='margin-bottom:1.5rem;'></div>", unsafe_allow_html=True)

    # المهام المنجزة المطبقة
    st.markdown("<h3 style='font-size:1.1rem; font-weight:700; color:#31516B; margin-bottom:0.75rem;'>المهام والمهارات التي تم ترقيتها</h3>", unsafe_allow_html=True)
    if result["applied_tasks"]:
        tasks_html = "".join([f"<li style='margin-bottom:0.35rem; color:#203342;'>{t}</li>" for t in result["applied_tasks"]])
        st.markdown(
            f"""
            <div class="ui-card" style="padding:1.25rem 1.5rem; border-right: 4px solid #2E8B7F;">
                <ul style="padding-right:1.2rem; margin:0; font-size:0.88rem; color:#203342;">
                    {tasks_html}
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.info("لم تقم بتحديد أي مهمة كمنجزة في خطة التطوير. يمكنك العودة وتحديد المهام المكتملة لرؤية النتيجة بعد التطوير.")

    # تفصيل أبعاد المطابقة المحدثة
    st.markdown("<h3 style='font-size:1.1rem; font-weight:700; color:#31516B; margin-top:1.5rem; margin-bottom:0.75rem;'>تفصيل أبعاد المطابقة المحدثة</h3>", unsafe_allow_html=True)
    up_match = result["updated_match"]
    dim_cols = st.columns(4)
    for i, d in enumerate(up_match["dimensions"]):
        with dim_cols[i]:
            st.markdown(
                f"""
                <div class="ui-card-subtle" style="text-align:center; padding:0.85rem; border-top: 2.5px solid #2E8B7F;">
                    <div style="font-size:0.82rem; font-weight:600; color:#5B6D7A;">{d['label']}</div>
                    <div style="font-size:1.3rem; font-weight:700; color:#2E8B7F; margin:0.25rem 0;">{d['score']:.0f}%</div>
                    <div style="font-size:0.74rem; color:#5B6D7A;">الوزن: {int(d['weight']*100)}%</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("<div style='margin-bottom:2rem;'></div>", unsafe_allow_html=True)

    col_plan, col_all = st.columns([1, 1])
    with col_plan:
        if st.button("← العودة لتعديل مهام الخطة", use_container_width=True):
            navigate_to("plan")
    with col_all:
        if st.button("العودة إلى قائمة الفرص", type="primary", use_container_width=True):
            navigate_to("opportunities")


# ---------------------------------------------------------------------------
# الموجه والتنقل الرئيسي (Routing)
# ---------------------------------------------------------------------------
scroll_to_top_if_requested()
render_top_header()
render_stepper()

PAGE_MAP = {
    "profile": page_profile,
    "opportunities": page_opportunities,
    "match": page_match,
    "assessment": page_assessment,
    "plan": page_plan,
    "reeval": page_reeval,
}

current_page_func = PAGE_MAP.get(st.session_state.step, page_profile)
current_page_func()
