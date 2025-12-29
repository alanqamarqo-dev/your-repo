import runpy

globals_dict = runpy.run_path('server_fixed.py')
call_fn = globals_dict.get('call_llm_with_messages')
if not call_fn:
    print('call_llm_with_messages not found in server_fixed')
else:
    messages = [
        {"role": "system", "content": "أجب بالعربية: كن موجزًا وواضحًا."},
        {"role": "user", "content": "ما هي سرعة الضوء؟"}
    ]
    print('Calling call_llm_with_messages...')
    res = call_fn(messages)
    print('--- RESULT ---')
    print(res)
