import sys,traceback
sys.path.insert(0, r'D:\AGL\repo-copy')
try:
    from sentence_transformers import SentenceTransformer
    print('sentence-transformers version imported')
    try:
        m = SentenceTransformer('all-MiniLM-L6-v2')
        print('loaded model dim', m.get_sentence_embedding_dimension())
    except Exception:
        print('model instantiation failed:')
        traceback.print_exc()
except Exception:
    print('import failed:')
    traceback.print_exc()
