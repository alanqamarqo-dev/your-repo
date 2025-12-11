import sys, os, json
sys.path.insert(0, r'D:\AGL\repo-copy')
from Engineering_Engines.Advanced_Code_Generator import AdvancedCodeGenerator

OUT_BASE = os.path.join(os.path.dirname(__file__), '..', 'generated')
os.makedirs(OUT_BASE, exist_ok=True)

gen = AdvancedCodeGenerator(parent_system_name='FatherAGI')

spec = {
    'name': 'MedicalAssistant_v1',
    'domain': 'طب',
    'required_engines': ['MathematicalBrain', 'CreativeInnovationEngine'],
    'software_requirements': {
        'name': 'MedicalAssistantService',
        'language': 'python',
        'component_type': 'api_server',
        'component_spec': {'type': 'api_server'}
    },
    'subdomain': None,
    'fertile': False
}

child = gen.generate_child_agi(spec)

out_dir = os.path.abspath(os.path.join(OUT_BASE, spec['name']))
os.makedirs(out_dir, exist_ok=True)

# Save JSON
json_path = os.path.join(out_dir, 'child_system.json')
with open(json_path, 'w', encoding='utf-8') as f:
    json.dump(child, f, ensure_ascii=False, indent=2)

# Write API, web, CLI, init script if present
api_code = child.get('interfaces', {}).get('api')
if api_code:
    with open(os.path.join(out_dir, 'api.py'), 'w', encoding='utf-8') as f:
        f.write(api_code)

web_code = child.get('interfaces', {}).get('web')
if web_code:
    with open(os.path.join(out_dir, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(web_code)

cli_code = child.get('interfaces', {}).get('cli')
if cli_code:
    with open(os.path.join(out_dir, 'cli.py'), 'w', encoding='utf-8') as f:
        f.write(cli_code)

init_script = child.get('lifecycle', {}).get('initialization_script')
if init_script:
    with open(os.path.join(out_dir, 'init.sh'), 'w', encoding='utf-8') as f:
        f.write(init_script)

# Print short summary
engines = child.get('components', {}).get('agi_engines', {})
knowledge = child.get('components', {}).get('knowledge_base', {})
software = child.get('components', {}).get('software_components', {})

print('=== Generated child system summary ===')
print('Name:', child.get('metadata', {}).get('name'))
print('Engines count:', len(engines))
print('Engine keys:', list(engines.keys()))
print('Knowledge tables:', len(knowledge.get('tables', {})))
print('Software components:', list(software.keys()))
print('API file written:' , os.path.exists(os.path.join(out_dir, 'api.py')))
print('CLI file written:' , os.path.exists(os.path.join(out_dir, 'cli.py')))
print('Web file written:' , os.path.exists(os.path.join(out_dir, 'index.html')))
print('Init script written:' , os.path.exists(os.path.join(out_dir, 'init.sh')))
print('Saved JSON to:', json_path)

# Basic readiness checks
readiness = True
issues = []
if len(engines) == 0:
    readiness = False
    issues.append('No engines cloned')
if len(knowledge.get('tables', {})) == 0:
    issues.append('No knowledge tables present')

print('\nReadiness: ', 'READY' if readiness else 'NOT READY')
if issues:
    print('Issues:')
    for it in issues:
        print('-', it)

# Exit with code 0 even if not fully ready (so we can inspect files)
