import tempfile
import os
from pathlib import Path
from AGL import create_agl_instance

def main():
    with tempfile.TemporaryDirectory() as td:
        p = Path(td)
        cfg = p / 'config.yaml'
        cfg.write_text(
            "features:\n"
            "  enable_self_improvement: true\n"
            "  enable_meta_cognition: true\n"
            "  persist_memory: true\n",
            encoding='utf-8'
        )
        # change cwd so create_agl_instance picks up cwd config
        os.chdir(p)
        agl = create_agl_instance(config=None)
        print('AGL.config:', agl.config)
        reg = getattr(agl, 'integration_registry', None)
        if reg:
            print('REGISTRY KEYS:', sorted(reg.keys()))
        else:
            print('No registry')

if __name__ == '__main__':
    main()
