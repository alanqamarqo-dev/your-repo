from pprint import pprint
ok = {}
try:
    # try to import registry
    from Integration_Layer import integration_registry
    reg = getattr(integration_registry, 'registry', None)
    ok['registry_imported'] = reg is not None
    if reg:
        try:
            services = list(getattr(reg, 'services', {}).keys())
            ok['registered_services_count'] = len(services)
            ok['registered_services_sample'] = services[:20]
        except Exception as e:
            ok['services_error'] = str(e)
except Exception as e:
    ok['registry_import_error'] = str(e)

# try to import ENGINE_STATS from any likely module path
candidates = ['Core_Engines.engine_monitor','AGL.Infra.engine_monitor','tools.engine_monitor','AGL.Infra.health']
for c in candidates:
    try:
        m = __import__(c, fromlist=['*'])
        if hasattr(m, 'ENGINE_STATS'):
            ok['ENGINE_STATS_from'] = c
            ok['ENGINE_STATS_keys'] = list(getattr(m,'ENGINE_STATS').keys())[:10]
            break
    except Exception as e:
        ok['import_'+c] = str(e)

# attempt to call a light engine if registry present
if ok.get('registry_imported') and reg:
    for candidate in ['NLP_Advanced','Reasoning_Layer','CAUSAL_GRAPH','Hosted_LLM']:
        eng = getattr(reg, 'services', {}).get(candidate)
        if eng and hasattr(eng,'process_task'):
            try:
                out = eng.process_task({'trace_id':'probe-0001','mode':'probe'})
                ok['probe_'+candidate] = {'called':True, 'out_keys': list(out.keys())[:5]}
            except Exception as e:
                ok['probe_'+candidate] = {'error': str(e)}
            break

pprint(ok)
