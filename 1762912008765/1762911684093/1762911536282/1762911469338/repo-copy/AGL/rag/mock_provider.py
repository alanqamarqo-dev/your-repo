from __future__ import annotations
from typing import Final, Dict

# كلمات/مرتكزات يتوقّعها الاختبار
_ANCHORS: Final[tuple[str, ...]] = (
	"2020",
	"covid",
	"كوفيد",
	"نفط",
	"oil",
	"price",
	# إضافات لتعزيز إجابات محاكاة لسيناريوهات الزلازل والإنذارات
	"زلزال",
	"زلازل",
	"إنذار",
	"هواتف",
	"فيزياء",
	"خوارزمية",
	"تطبيق",
)


def mock_answer(query: str) -> Dict[str, object]:
	"""
	يُرجع قاموسًا بالشكل الذي تتوقّعه الاختبارات:
	  {
		"ok": True,
		"text": "<نص الإجابة>",
		"contains_hints": <bool>  # هل النص يحتوي على المرتكزات أم لا
	  }
	"""
	q = (query or "")
	q_low = q.lower()

	contains = any(k in q_low for k in _ANCHORS)

	if contains:
		# tailor the mock text depending on which anchors were found
		if any(x in q_low for x in ("2020", "covid", "كوفيد")):
			text = (
				"إجابة محاكية: في عام 2020 تسبّبت جائحة COVID في صدمة طلب/عرض؛ "
				"تدنّت أسعار النفط بشكل حاد ثم تعافَت تدريجيًا لاحقًا."
			)
		elif any(x in q_low for x in ("نفط", "oil", "price")):
			text = (
				"إجابة محاكية: تأثرت أسعار النفط بسبب ضعف الطلب اثر الجائحة واضطرابات العرض؛ "
				"تضمّن أثرًا جيوسياسيًا وتغيرًا في سلوك النقل."
			)
		elif any(x in q_low for x in ("زلزال", "زلازل", "إنذار", "هواتف")):
			text = (
				"إجابة محاكية متخصصة: يمكن استخدام هواتف ذكية لرصد اهتزازات محلية عبر قياس التسارع المحلي، "
				"مع فلترة إشارة وإزالة الضوضاء، وخوارزميات كشف نمط مبكر (feature extraction + thresholding). "
				"الفيزياء الأساسية تعتمد على تحويل موجات الاهتزاز إلى نطاقات ترددية وتحليل الطور."
			)
		else:
			# generic hit
			text = "إجابة محاكية: استجابة تحتوي على مرتكزات ذات صلة بالسؤال وتلخص النقاط الأساسية." 
	else:
		# keep a phrase expected by existing unit tests; make it a bit longer
		text = (
			"إجابة محاكية عامّة: لا توجد كلمات مفتاحية محددة في المدخل. "
			"في وضع الاختبار، تُرجى تفعيل مزيد من المصادر الحقيقية للحصول على إجابة مفصّلة."
		)

	return {
		"ok": True,
		"text": text,
		"contains_hints": bool(contains),
	}


__all__ = ["mock_answer"]
