from scripts._bootstrap import ensure_project_root
ensure_project_root()

from Integration_Layer import rag_wrapper as rw
p = """
لماذا انخفضت أسعار النفط عام 2020؟
ناقش بالأبعاد: اقتصادي، جيوسياسي، اجتماعي، تكنولوجي. اذكر نقاط على كل مستوى.
"""
print('Calling rag_answer for oil-2020...')
res = rw.rag_answer(p)
print('RAG output:', res)
