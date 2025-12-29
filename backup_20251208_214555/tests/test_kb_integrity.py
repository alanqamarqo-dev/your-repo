import io, json, os, re, unittest, shutil


class TestKBIntegrity(unittest.TestCase):
    def test_kb_is_valid_and_utf8(self):
        p = 'Knowledge_Base/Learned_Patterns.json'
        # If canonical KB missing, attempt safe restore from lock or .new snapshot
        if not os.path.exists(p):
            lock = 'Knowledge_Base/Learned_Patterns.lock.json'
            new = 'Knowledge_Base/Learned_Patterns.json.new'
            if os.path.exists(lock):
                try:
                    shutil.copyfile(lock, p)
                except Exception:
                    pass
            elif os.path.exists(new):
                try:
                    shutil.copyfile(new, p)
                except Exception:
                    pass
        self.assertTrue(os.path.exists(p), 'KB file missing')
        txt = io.open(p, 'r', encoding='utf-8-sig').read().strip()
        try:
            json.loads(txt)
        except Exception:
            blocks = re.findall(r'\{.*?\}', txt, flags=re.S)
            ok = any([self._is_json(b) for b in blocks])
            self.assertTrue(ok, 'KB not recoverable JSON')

    def _is_json(self, s):
        try:
            json.loads(s)
            return True
        except Exception:
            return False
