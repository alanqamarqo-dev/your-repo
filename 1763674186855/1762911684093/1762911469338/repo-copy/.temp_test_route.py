import traceback

try:
    from Integration_Layer.Conversation_Manager import auto_route_and_respond
    print('Imported auto_route_and_respond')
    res = auto_route_and_respond('test_debug_session', 'مرحبًا هذا اختبار')
    print('Result:', res)
except Exception as e:
    print('Exception calling auto_route_and_respond:')
    traceback.print_exc()
