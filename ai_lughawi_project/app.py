import json
import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="مدقّق | AI", page_icon="✍️", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Cairo', sans-serif; }
.block-container { max-width: 1100px; padding-top: 2rem; }
.arabic { direction: rtl; text-align: right; }
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='arabic'><h1>✍️ مدقّق | AI</h1><p>مساعدك الذكي لمراجعة النصوص وتحسينها مع الحفاظ على المعنى وأسلوب الكاتب.</p></div>", unsafe_allow_html=True)

with st.sidebar:
    st.header("الإعدادات")
    language = st.selectbox("لغة النص", ["العربية", "الإنجليزية", "العربية والإنجليزية"])
    style = st.selectbox("نوع المراجعة", [
        "تدقيق لغوي فقط",
        "تدقيق لغوي وتحسين الصياغة",
        "تدقيق نص مترجم",
        "نص أكاديمي أو بحثي"
    ])
    explain = st.checkbox("شرح الأخطاء وأسباب التصحيح", value=True)
    alternatives = st.checkbox("اقتراح بدائل لغوية", value=True)
    st.caption("تحتاج الأداة إلى مفتاح OpenAI API لتشغيل التحليل.")

default_text = ""
text = st.text_area("ألصق النص الذي تريد تدقيقه هنا", value=default_text, height=260,
                    placeholder="اكتب النص هنا...")

api_key = st.text_input("مفتاح OpenAI API", type="password",
                        help="يُستخدم لتشغيل المراجعة. لا تضع المفتاح في ملف الكود أو تشاركه مع الآخرين.")

def build_prompt(source, language, style, explain, alternatives):
    return f"""
أنت مدقق لغوي محترف ومتخصص في {language}. راجع النص وفق نوع المراجعة التالي: {style}.
حافظ على المعنى الأصلي وأسلوب الكاتب قدر الإمكان، ولا تخترع معلومات أو تغيّر المقصود.
افحص الإملاء، والنحو، والصرف، والأسلوب، وعلامات الترقيم، وبناء الجمل، والألفاظ غير المناسبة للسياق.
ميّز بين الخطأ المؤكد والاقتراح الأسلوبي، ولا تعتبر كل اختلاف أسلوبي خطأ.
{"اشرح سبب كل تصحيح باختصار." if explain else "لا تضف شرحًا للأخطاء."}
{"اقترح بديلًا لغويًا عند الحاجة." if alternatives else "لا تضف بدائل لغوية."}
أخرج النتيجة باللغة المناسبة للنص وبصيغة JSON صالحة فقط، بالشكل التالي:
{{
  "corrected_text": "النص بعد التصحيح",
  "summary": ["ملخص موجز لأهم الملاحظات"],
  "issues": [
    {{
      "original": "المقطع الأصلي",
      "correction": "التصحيح المقترح",
      "category": "إملائي أو نحوي أو صرفي أو ترقيم أو أسلوبي أو صياغة",
      "explanation": "سبب التصحيح أو ملاحظة أسلوبية",
      "alternative": "بديل اختياري أو سلسلة فارغة"
    }}
  ]
}}
إذا لم توجد أخطاء، اذكر ذلك في summary وأعد النص كما هو.
النص المراد مراجعته:
{source}
"""

if st.button("ابدأ التدقيق", type="primary", use_container_width=True):
    if not text.strip():
        st.warning("أدخل نصًا أولًا حتى تتم مراجعته.")
    elif not api_key.strip():
        st.error("أدخل مفتاح OpenAI API لتشغيل الأداة.")
    else:
        try:
            with st.spinner("جارٍ تدقيق النص..."):
                client = OpenAI(api_key=api_key.strip())
                response = client.responses.create(
                    model="gpt-4.1-mini",
                    input=build_prompt(text, language, style, explain, alternatives)
                )
                raw = response.output_text
                # Accept JSON even if the model wraps it in a code fence.
                cleaned = raw.strip()
                if cleaned.startswith("```"):
                    cleaned = cleaned.split("\n", 1)[1]
                    if cleaned.endswith("```"):
                        cleaned = cleaned[:-3]
                result = json.loads(cleaned)

            st.session_state["proofread_result"] = result
        except json.JSONDecodeError:
            st.error("وصلت نتيجة غير منظمة. جرّب مرة أخرى.")
            st.code(raw if "raw" in locals() else "")
        except Exception as e:
            st.error(f"تعذّر إكمال التدقيق: {e}")

result = st.session_state.get("proofread_result")
if result:
    st.divider()
    st.subheader("النص بعد التدقيق")
    st.text_area("يمكنك نسخ النص المصحح", value=result.get("corrected_text", ""), height=240)
    st.download_button(
        "تنزيل النص المصحح (.txt)",
        data=result.get("corrected_text", ""),
        file_name="النص_بعد_التدقيق.txt",
        mime="text/plain",
        use_container_width=True
    )

    st.subheader("ملخص الملاحظات")
    for item in result.get("summary", []):
        st.write("• " + str(item))

    issues = result.get("issues", [])
    st.subheader(f"الأخطاء والاقتراحات ({len(issues)})")
    if not issues:
        st.success("لم تُسجّل الأداة ملاحظات محددة.")
    for i, issue in enumerate(issues, 1):
        with st.expander(f"{i}. {issue.get('category', 'ملاحظة')} | {issue.get('original', '')}"):
            st.markdown(f"**الأصل:** {issue.get('original', '')}")
            st.markdown(f"**التصحيح المقترح:** {issue.get('correction', '')}")
            if issue.get("explanation"):
                st.markdown(f"**السبب:** {issue['explanation']}")
            if issue.get("alternative"):
                st.markdown(f"**بديل مقترح:** {issue['alternative']}")

st.caption("تنبيه: مخرجات الذكاء الاصطناعي قد تحتاج إلى مراجعة بشرية، خصوصًا في النصوص الأكاديمية أو المتخصصة.")
