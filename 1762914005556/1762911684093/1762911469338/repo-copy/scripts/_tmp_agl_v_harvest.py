import json,subprocess,os
cfg=json.load(open('artifacts/domains_v5.json'))
print(f"[AGL-V] Harvesting across {len(cfg['domains'])} domains, target/each = {cfg['targets_per_domain']}")
for d in cfg['domains']:
    print('→ harvesting domain:',d)
    env=os.environ.copy()
    env['AGL_FORCE_DOMAIN']=d
    env['AGL_HARVEST_TARGET_PER_DOMAIN']=str(cfg['targets_per_domain'])
    try:
        subprocess.run([r'.venv\\Scripts\\python.exe','workers\\knowledge_harvester.py'],check=True,env=env)
    except subprocess.CalledProcessError as e:
        print('harvester exit',e.returncode)
if os.path.exists('infra/harvester/run_pipeline.py'):
    print('[AGL-V] running harvester pipeline (route facts)')
    subprocess.run([r'.venv\\Scripts\\python.exe','infra/harvester/run_pipeline.py'])
subprocess.run([r'.venv\\Scripts\\python.exe','tools\\harvest_progress.py','--last','5'])
