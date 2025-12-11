import os
from Integration_Layer.agl_state import AGLState


def test_scoring_calibration_prefers_structured():
    # Ensure the aggressive calibration is on for deterministic boost behavior
    os.environ['AGL_CALIBRATE_AGGRESSIVE'] = '1'

    s = AGLState(question='test')

    short_answer = "المستعمرة البحرية هي بنية تحت الماء توفر سكنًا وبحوثًا."

    rich_answer = (
        "المستعمرة البحرية هي بنية تحت الماء مصممة لاستدامة الحياة.\n"
        "1. الموقع: اختيار عمق مناسب واستقرار التربة البحرية.\n"
        "2. التصميم الهندسي: هياكل مقاومة للضغط، مواد مضادة للتآكل.\n"
        "3. الأنظمة: طاقة متجددة، تدوير مياه، دعم الحياة.\n"
        "+---+\n| مخطط مبسط |\n+---+\n"
    )

    r_short = s.evaluate_and_score(short_answer)
    r_rich = s.evaluate_and_score(rich_answer)

    score_short = float(r_short.get('score', 0.0))
    score_rich = float(r_rich.get('score', 0.0))

    # debug output on failure to help future debugging
    assert score_rich - score_short >= 0.3, (
        f"Rich answer should beat short by >=0.3 but got {score_rich:.3f} vs {score_short:.3f}.\n"
        f"components short={r_short.get('components')}\ncomponents rich={r_rich.get('components')}"
    )
