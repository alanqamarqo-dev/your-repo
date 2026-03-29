"""Deep dive: inheritance, external calls, state writes"""
import sys, re
sys.path.insert(0, '..')
from pathlib import Path
from collections import Counter
from agl_security_tool.detectors.solidity_parser import SoliditySemanticParser
from agl_security_tool.detectors import OpType

p = SoliditySemanticParser()
src = Path('test_contracts/real_world/compound_comet.sol').read_text(encoding='utf-8')
contracts = p.parse(src, 'compound_comet.sol')

comet = [c for c in contracts if c.name == 'Comet'][0]
storage = [c for c in contracts if c.name == 'CometStorage'][0]

print('=== INHERITANCE ANALYSIS ===')
print(f'CometStorage state vars: {len(storage.state_vars)}')
print(f'Comet state vars: {len(comet.state_vars)}')
inherited_vars = set(storage.state_vars.keys())
comet_vars = set(comet.state_vars.keys())
print(f'Inherited vars ({len(inherited_vars)}): {sorted(inherited_vars)}')
print(f'Comet own vars ({len(comet_vars)}): {sorted(comet_vars)[:10]}...')

print('\n=== STATE WRITE ANALYSIS ===')
hidden_writes = 0
detected_writes = 0
for fn_name, fn in sorted(comet.functions.items()):
    if fn.state_writes:
        detected_writes += len(fn.state_writes)
        print(f'  [DETECTED] {fn_name}(): {fn.state_writes}')
    for op in fn.operations:
        if op.raw_text:
            for ivar in inherited_vars:
                if re.search(rf'\b{re.escape(ivar)}\b\s*(?:=|\+=|-=)', op.raw_text):
                    if ivar not in fn.state_writes:
                        hidden_writes += 1
                        print(f'  [HIDDEN!]  {fn_name}(): write to [{ivar}] -> {op.raw_text[:80]}')
                        break

print(f'\n  Total detected writes: {detected_writes}')
print(f'  Total HIDDEN writes (inheritance gap): {hidden_writes}')

print('\n=== EXTERNAL CALL ANALYSIS ===')
total_ext = 0
for fn_name, fn in sorted(comet.functions.items()):
    for op in fn.operations:
        if op.op_type in (OpType.EXTERNAL_CALL, OpType.EXTERNAL_CALL_ETH, OpType.DELEGATECALL):
            total_ext += 1
            txt = op.raw_text[:80] if op.raw_text else '(no text)'
            print(f'  {fn_name}() L{op.line}: {op.op_type.value} -> {txt}')
print(f'Total external calls detected in Comet: {total_ext}')

# Lines with IERC20/IPriceFeed calls
print('\n=== REGEX PATTERN TEST ===')
re_erc20 = re.compile(r'(\w[\w.\[\]]*)\s*\.\s*(transfer|transferFrom|safeTransfer|safeTransferFrom|approve|safeApprove)\s*\(')
re_transfer = re.compile(r'(\w[\w.\[\]]*)\s*\.\s*transfer\s*\(')

test_lines = [
    'IERC20(asset).transferFrom(from, address(this), amount);',
    'IERC20(asset).transfer(to, amount);',
    'IERC20(asset).approve(manager, amount);',
    'IERC20(asset).balanceOf(address(this));',
    'token.transfer(msg.sender, amount);',
    'dola.transferFrom(msg.sender, address(this), amount);',
    'LOAN_TOKEN.safeTransfer(exchangeOrder.maker, refund);',
]
for line in test_lines:
    erc_m = re_erc20.search(line)
    tr_m = re_transfer.search(line)
    erc_result = f'MATCH grp={erc_m.groups()}' if erc_m else 'MISS'
    tr_result = f'MATCH grp={tr_m.groups()}' if tr_m else 'MISS'
    print(f'  "{line[:65]}"')
    print(f'    _RE_ERC20: {erc_result}')
    print(f'    _RE_TRANSFER: {tr_result}')

print('\n=== OPERATION TYPE DISTRIBUTION (Comet) ===')
op_counts = Counter()
for fn_name, fn in comet.functions.items():
    for op in fn.operations:
        op_counts[op.op_type.value] += 1
for k, v in sorted(op_counts.items(), key=lambda x: -x[1]):
    bar = '#' * min(v, 40)
    print(f'  {k:25s} {v:4d} {bar}')

print('\n=== FUNCTION COUNT BY VISIBILITY ===')
vis_counts = Counter()
mut_counts = Counter()
for fn_name, fn in comet.functions.items():
    vis_counts[fn.visibility] += 1
    mut_counts[fn.mutability or 'nonpayable'] += 1
print(f'  Visibility: {dict(vis_counts)}')
print(f'  Mutability: {dict(mut_counts)}')

print('\n=== SAFE FUNCS CLASSIFICATION ANALYSIS ===')
safe = []
unsafe = []
safe_but_state_changing = []
for fn_name, fn in comet.functions.items():
    is_safe = fn.visibility in ('internal', 'private') or fn.mutability in ('view', 'pure')
    if is_safe:
        safe.append(fn_name)
        # But does it actually modify state?
        if fn.modifies_state:
            safe_but_state_changing.append(fn_name)
    else:
        unsafe.append(fn_name)

print(f'  Safe: {len(safe)}, Unsafe: {len(unsafe)}')
print(f'  Safe but modifies state: {safe_but_state_changing}')
print(f'  These are suppressed by downstream layers but SHOULD be analyzed!')
