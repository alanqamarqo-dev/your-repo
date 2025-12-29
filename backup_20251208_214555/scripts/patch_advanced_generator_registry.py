import io,sys,os
root = r'd:\AGL'
old_new = {
    'Core_Engines.mathematical_brain':'Core_Engines.Mathematical_Brain',
    'Core_Engines.quantum_neural_core':'Core_Engines.Quantum_Neural_Core',
    'Core_Engines.creative_innovation_engine':'Core_Engines.Creative_Innovation',
    'Core_Engines.advanced_simulation_engine':'Core_Engines.Quantum_Processor',
    'Core_Engines.visual_spatial':'Core_Engines.Visual_Spatial'
}
changed = []
for dirpath, dirs, files in os.walk(root):
    for fn in files:
        if fn == 'Advanced_Code_Generator.py':
            path = os.path.join(dirpath, fn)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    s = f.read()
                ns = s
                for o,nv in old_new.items():
                    if o in ns:
                        ns = ns.replace(o, nv)
                if ns != s:
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(ns)
                    changed.append(path)
            except Exception as e:
                print('ERR', path, e)
print('Patched files:')
for p in changed:
    print(p)
