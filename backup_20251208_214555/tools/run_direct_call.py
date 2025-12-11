# Import the server module and call the helper directly to test passthrough
import server_fixed
messages = [
    {"role": "system", "content": "أجب بالعربية: كن موجزًا وواضحًا."},
    {"role": "user", "content": "ما هي سرعة الضوء؟"}
]
print('Calling call_llm_with_messages()...')
res = server_fixed.call_llm_with_messages(messages)
print('--- RESULT ---')
print(res)
