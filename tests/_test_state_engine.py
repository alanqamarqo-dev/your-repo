"""Test script for State Extraction Engine"""
import sys, json
sys.path.insert(0, '.')
from agl_security_tool.state_extraction import StateExtractionEngine

engine = StateExtractionEngine()
result = engine.extract('test_project/src/Vault.sol')

print('=== EXTRACTION RESULT ===')
print('Success:', result.success)
print('Contracts parsed:', result.contracts_parsed)
print('Entities found:', result.entities_found)
print('Relationships found:', result.relationships_found)
print('Fund flows found:', result.fund_flows_found)
print('Validation issues:', result.validation_issues)
print('Errors:', result.errors)
print('Warnings:', result.warnings)

if result.graph:
    stats = result.graph.stats()
    print('\n=== GRAPH STATS ===')
    print('Nodes:', stats['total_nodes'])
    print('Edges:', stats['total_edges'])
    print('Node types:', stats['node_types'])
    print('Edge types:', stats['edge_types'])
    
    print('\n=== ENTITIES ===')
    for eid, ent in result.graph.entities.items():
        print(f'  {eid} -> {ent.entity_type.value} (confidence: {ent.confidence})')
        if ent.balance_vars:
            print(f'    balance_vars: {ent.balance_vars}')
        if ent.access_modifiers:
            print(f'    access_mods: {ent.access_modifiers}')
    
    print('\n=== RELATIONSHIPS ===')
    for rel in result.graph.relationships[:10]:
        print(f'  {rel.source_id} --[{rel.relation_type.value}]--> {rel.target_id}')
        if rel.function_name:
            print(f'    function: {rel.function_name}')
    
    print('\n=== FUND FLOWS ===')
    for flow in result.graph.fund_flows[:10]:
        print(f'  {flow.source_account} --[{flow.flow_type}]--> {flow.target_account}')
        print(f'    token: {flow.token_id}, amount: {flow.amount_expr[:50] if flow.amount_expr else "N/A"}')
    
    print('\n=== VALIDATION ===')
    if result.graph.validation:
        v = result.graph.validation
        print('  Consistent:', v.is_consistent)
        print('  Balance OK:', v.balance_conservation_ok)
        print('  No cycles:', v.no_illogical_cycles)
        print('  Summary:', v.summary)
        for issue in v.issues[:5]:
            print(f'  [{issue.severity}] {issue.issue_type}: {issue.description[:120]}')
    
    # Test JSON export
    json_output = result.to_json(indent=2)
    print(f'\n=== JSON SIZE: {len(json_output)} bytes ===')
    parsed = json.loads(json_output)
    print('JSON valid: True')
    print('Top keys:', list(parsed.keys()))
    
    # Save to file
    with open('_state_extraction_test.json', 'w', encoding='utf-8') as f:
        f.write(json_output)
    print('Saved to _state_extraction_test.json')
else:
    print('ERROR: No graph generated')
