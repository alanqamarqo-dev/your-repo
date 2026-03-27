"""Test State Extraction Engine on full project"""
import sys, json
sys.path.insert(0, '.')
from agl_security_tool.state_extraction import StateExtractionEngine

engine = StateExtractionEngine()
result = engine.extract_project('test_project/src/')

print('=== PROJECT EXTRACTION ===')
print('Success:', result.success)
print('Contracts parsed:', result.contracts_parsed)
print('Entities found:', result.entities_found)
print('Relationships found:', result.relationships_found)
print('Fund flows found:', result.fund_flows_found)
print('Validation issues:', result.validation_issues)
print('Errors:', result.errors[:3])
print('Warnings:', result.warnings[:3])

if result.graph:
    stats = result.graph.stats()
    print('\n=== GRAPH STATS ===')
    print('Nodes:', stats['total_nodes'])
    print('Edges:', stats['total_edges'])
    print('Node types:', stats['node_types'])
    print('Edge types:', stats['edge_types'])
    print('Source files:', stats['source_files'])
    
    print('\n=== ALL ENTITIES ===')
    for eid, ent in result.graph.entities.items():
        print(f'  {eid} -> {ent.entity_type.value} (conf: {ent.confidence:.2f})')
    
    print('\n=== VALIDATION ===')
    if result.graph.validation:
        v = result.graph.validation
        print('  Consistent:', v.is_consistent)
        print('  Issues:', len(v.issues))
        for issue in v.issues[:8]:
            print(f'  [{issue.severity}] {issue.issue_type}: {issue.description[:100]}')
    
    # Dynamic operations test
    print('\n=== DYNAMIC OPERATIONS TEST ===')
    # Test fund flow paths
    tokens = set()
    for flow in result.graph.fund_flows:
        tokens.add(flow.token_id)
    print(f'Unique tokens in flows: {len(tokens)}')
    for tok in list(tokens)[:3]:
        paths = result.graph.get_fund_flow_paths(tok)
        if paths:
            print(f'  Paths for {tok}: {len(paths)}')
    
    # Test JSON roundtrip
    json_str = result.graph.to_json()
    from agl_security_tool.state_extraction.models import FinancialGraph
    reloaded = FinancialGraph.from_dict(json.loads(json_str))
    print(f'\nJSON roundtrip: {len(reloaded.nodes)} nodes, {len(reloaded.edges)} edges')
    print('Roundtrip OK:', len(reloaded.nodes) == stats['total_nodes'])
    
    # Save full output
    with open('_state_extraction_project.json', 'w', encoding='utf-8') as f:
        f.write(result.to_json(indent=2))
    print(f'\nSaved full output ({len(result.to_json())} bytes)')
    
    # Test engine info
    print('\n=== ENGINE INFO ===')
    info = engine.get_info()
    print('Name:', info['name'])
    print('Version:', info['version'])
    print('Components:', list(info['components'].keys()))
    print('Capabilities:', len(info['capabilities']), 'features')
else:
    print('ERROR: No graph generated')
