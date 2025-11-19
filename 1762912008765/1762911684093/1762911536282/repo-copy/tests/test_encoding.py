import unittest
import os
import sys


class TestEncoding(unittest.TestCase):
    def test_logfile_is_utf8(self):
        log_path = os.path.join(os.getcwd(), 'logs', 'agl.log')
        # Ensure the log exists by touching via AGL run if necessary
        if not os.path.exists(log_path):
            # run a quick AGL invocation to create logs
            try:
                import subprocess
                subprocess.run([sys.executable, os.path.join(os.getcwd(), 'AGL.py'), '--task', 'اختبار الترميز'], check=True, timeout=10)
            except Exception:
                pass

        self.assertTrue(os.path.exists(log_path), msg='logs/agl.log does not exist')

        # Try reading file as utf-8 and ensure no replacement chars appear
        with open(log_path, 'rb') as f:
            raw = f.read()
        try:
            text = raw.decode('utf-8')
        except UnicodeDecodeError as e:
            self.fail(f'Log file is not valid UTF-8: {e}')

        # Check for typical replacement character U+FFFD
        self.assertNotIn('\ufffd', text, msg='Log contains Unicode replacement characters (decoding issues)')

    def test_pythonioencoding_or_stdout_utf8(self):
        # Check environment variable
        env_val = os.environ.get('PYTHONIOENCODING')
        if env_val:
            self.assertTrue('utf-8' in env_val.lower(), msg=f'PYTHONIOENCODING is set but not utf-8: {env_val}')
        else:
            # fallback: check stdout encoding
            enc = None
            try:
                enc = sys.stdout.encoding
            except Exception:
                enc = None
            self.assertIsNotNone(enc, msg='Unable to determine stdout encoding')
            self.assertTrue('utf' in enc.lower(), msg=f'stdout encoding is not utf-8: {enc}') # type: ignore


if __name__ == '__main__':
    unittest.main()
