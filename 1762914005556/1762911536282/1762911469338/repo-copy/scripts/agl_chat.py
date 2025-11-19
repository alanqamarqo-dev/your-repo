import sys
import argparse
from Integration_Layer.Intent_Recognizer import recognize_intent
from AGL_UI.Language_Interface import parse_entities
from Integration_Layer.Action_Router import route
from AGL_UI.Response_Formatter import humanize
from Integration_Layer.Conversation_Manager import create_session, append_turn, last_turn


def main(): # type: ignore
    p = argparse.ArgumentParser()
    p.add_argument('text', nargs='*')
    p.add_argument('--session', '-s', help='session id to persist conversation', default=None)
    args = p.parse_args()
    text = " ".join(args.text) if args.text else input("اكتب سؤالك: ")

    if args.session:
        create_session(args.session)

    intent = recognize_intent(text)
    kv = parse_entities(text)
    out = route(intent.get("task"), intent.get("law"), kv, session_id=args.session) # type: ignore

    # persist turn
    if args.session:
        append_turn(args.session, text, out)

    # handle follow-up suggestion
    if out.get('follow_up'):
        print(humanize(out, lang="ar"))
        follow = input(out['follow_up'] + " [y/N]: ")
        if follow.strip().lower() in ('y', 'نعم', 'yep', 'yes'):
            # naive follow-up handling
            print('تمام — أعد إرسال الطلب مع القيم المطلوبة أو قل: V=... R=...')
        return

    print(humanize(out, lang="ar"))


if __name__ == "__main__":
    main()
import sys
from Integration_Layer.Intent_Recognizer import recognize_intent
from AGL_UI.Language_Interface import parse_entities
from Integration_Layer.Action_Router import route
from AGL_UI.Response_Formatter import humanize

def main():
    text = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else input("اكتب سؤالك: ")
    intent = recognize_intent(text)
    kv = parse_entities(text)
    out = route(intent.get("task"), intent.get("law"), kv) # type: ignore
    print(humanize(out, lang="ar"))

if __name__ == "__main__":
    main()
