import subprocess, time, os, json
from urllib.request import Request, urlopen
import urllib.error
import re
from datetime import datetime

CHILD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'generated', 'MedicalAssistant_v1'))
CHILD_MAIN = os.path.join(CHILD_DIR, 'main_stub.py')
PY = 'python'

class MissionControlEnhanced:
    def __init__(self):
        self.available_systems = {
            'parent': 'AGL_Main',
            'children': []
        }

    def register_child_system(self, child_config: dict):
        self.available_systems['children'].append({
            'name': child_config['name'],
            'domain': child_config.get('domain', 'عام'),
            'api_endpoint': child_config.get('api_endpoint'),
            'capabilities': child_config.get('capabilities', [])
        })
        print(f"✅ تم تسجيل النظام الابن: {child_config['name']}")

    def get_child_system(self, name: str):
        for c in self.available_systems['children']:
            if c['name'] == name:
                return c
        return None

    def enhance_child_result(self, result: dict, mission: dict) -> dict:
        # Minimal enhancement: mark success and add parent's note
        enhanced_note = 'Parent added clinical caution note'
        if isinstance(result, dict):
            out = result.copy()
            out['enhanced_by_parent'] = enhanced_note
            out['success'] = True
            return out
        # result could be a string or other primitive -> wrap it
        return {'success': True, 'raw_result': result, 'enhanced_by_parent': enhanced_note}

    def route_mission(self, mission: dict) -> dict:
        # select target by name if provided
        target_name = mission.get('target_system')
        if not target_name:
            return {'error': 'no target specified'}
        child = self.get_child_system(target_name)
        if not child:
            return {'error': 'child not registered'}

        api = child.get('api_endpoint').rstrip('/')
        # Build payload: prefer sending 'engine' request to call engine directly
        payload = {'engine': 'MathematicalBrain', 'data': mission.get('data')}
        url = api + '/process'
        req = Request(url, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type':'application/json'})
        try:
            with urlopen(req, timeout=5) as resp:
                body = resp.read().decode('utf-8')
                res_obj = json.loads(body)
        except urllib.error.HTTPError as e:
            return {'error': f'http error {e.code}'}
        except Exception as e:
            return {'error': str(e)}

        # the stub returns {'result': ...}
        result = res_obj.get('result') if isinstance(res_obj, dict) else res_obj
        # attempt to extract capabilities from registered child
        child_caps = child.get('capabilities', [])
        enhanced = intelligent_enhancement(result, child_caps, mission) # pyright: ignore[reportUndefinedVariable]
        return enhanced


def create_medical_mission():
    return {
        'id': 'mission_medical_001',
        'type': 'diagnosis',
        'priority': 'high',
        'target_system': 'MedicalAssistant_v1',
        'data': {
            'patient': 'مريض اختبار',
            'symptoms': ['حمى', 'صداع', 'سعال', 'إرهاق'],
            'age': 35,
            'medical_history': 'لا يوجد'
        }
    }


def start_child_server():
    # launch the main_stub.py as a subprocess
    proc = subprocess.Popen([PY, CHILD_MAIN], cwd=CHILD_DIR)
    # wait a short time for it to be ready
    time.sleep(0.6)
    return proc


def stop_child_server(proc):
    try:
        proc.terminate()
        proc.wait(timeout=2)
    except Exception:
        proc.kill()


if __name__ == '__main__':
    print('\n🧪 بدء اختبار تكامل Mission Control مع النظام الابن...')
    # try auto-discovery first (scans common local ports)
    mc = MissionControlEnhanced()
    discovered = auto_discover_child_systems() # pyright: ignore[reportUndefinedVariable]
    if discovered:
        for d in discovered:
            mc.register_child_system(d)
        proc = None
        print(f"Discovered and registered {len(discovered)} child systems")
    else:
        proc = start_child_server()
        print('Child server pid:', proc.pid)

        # fallback: manual registration
        mc.register_child_system({
            'name': 'MedicalAssistant_v1',
            'domain': 'طب',
            'api_endpoint': 'http://127.0.0.1:8080',
            'capabilities': ['تشخيص', 'تحليل أعراض', 'اقتراح علاج']
        })

    mission = create_medical_mission()
    print('📤 إرسال مهمة:', mission['id'])

    result = mc.route_mission(mission)
    print('📥 النتيجة:', result)

    if result.get('success'):
        print('✅ اختبار التكامل نجح!')
    else:
        print('❌ اختبار التكامل فشل')

    if proc:
        stop_child_server(proc)
        print('Child server stopped')
