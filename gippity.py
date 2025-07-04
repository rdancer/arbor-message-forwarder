import json
import openai
import os
from dotenv import load_dotenv
import re

REFORMAT_ATTEMPTS = 3

# Load environment
load_dotenv(override=True)

openai.api_key = os.getenv("OPENAI_API_KEY")
model = os.getenv("OPENAI_MODEL") or "gpt-4-turbo"

openai_client = None

def format_message(message_text: str) -> tuple[str, str]:
    """
    Reformats the message text to make it more readable.

    Returns:
    subject (str): The subject of the message.
    message_text (str): The body of the message.
    """
    default_subject = f"{message_text[:30].strip()}{'...' if len(message_text)>30 else ''}"
    if openai.api_key is None:
        print(f"Warning: OpenAI API key not set. Skipping message reformatting.")
        return default_subject, message_text

    prompt = f"""The following e-mail lost its subject and line breaks. Restore them.\n""" \
             f"""The typos and idiosyncracies are part of the text, NEVER alter them. Your task is to add the lost Subject and Line Breaks *ONLY*\n""" \
             f"""Don't use markdown:\n\n""" \
             f"""{message_text}"""

    global openai_client
    if openai_client is None:
        openai_client = openai.OpenAI(api_key=openai.api_key)
    
    try:
        response = openai_client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model="gpt-4-turbo-preview",
            n=REFORMAT_ATTEMPTS,
        )
        ai_texts = [choice.message.content for choice in response.choices]
    except Exception as e:
        print(f"Failed to reformat message: {e}")
        return default_subject, message_text
    subjects = [extract_subject(ai_text) for ai_text in ai_texts]
    body_texts = [extract_body_text(message_text, ai_text, subject) for (ai_text, subject) in zip(ai_texts, subjects)]
    subject = next((s for s in subjects if s is not None and len(s) > 0), default_subject)
    if os.getenv("DEBUG") == "True":
        print(f"Body texts: {json.dumps(body_texts, indent=4)}")
    body_texts.sort(key=lambda x: x[1], reverse=True)
    body_text = body_texts[0][0]
    if os.getenv("DEBUG") == "True":
        print(f"Subject: {subject}\nBody:\n{body_text}\nOriginal:\n{message_text}")
    return subject, body_text

def extract_body_text(message_text: str, ai_text: str, subject: str) -> str:
    # Start extraction after the subject
    ai_text = ai_text[(ai_text.find(subject) + len(subject)) if subject else 0:]
    message_text = message_text.strip()
    ai_text = ai_text.strip()
    i = 0
    j = 0
    out = ""
    try:
        while i < len(message_text):
            if message_text[i] == ai_text[j]:
                out += message_text[i]
                j += 1
                i += 1
            elif ai_text[j] == "\n" and message_text[i] == " ": # AI added a line break
                out += ai_text[j]
                j += 1
                i += 1
            elif ai_text[j] == "\n": # Extra linebreak in AI text
                out += ai_text[j]
                j += 1
            else:
                # TODO: recover and attempt to match the next paragraph
                print("=" * 80)
                # print the red terminal escape sequence (bright red text)
                print("\033[91m", end="")
                print(f"Warning: Could not match AI and original text:")
                print(f"LLM text: {ai_text[j:]}")
                print(f"Original: {message_text[i:]}")
                # reset terminal to default text color
                print("\033[0m", end="")
                print("="* 80)
                out += message_text[i:]
                problem_idx = i
                break
    except Exception as e:
        print(f"Warning: Failed to match AI and original text: {e}")
        out += message_text[i:]
        problem_idx = i
    # Even among successes, we prefer the longer texts, i.e. more formatting applied: len(out) instead of len(message_text)
    success_length = len(out) if "problem_idx" not in locals() else problem_idx
    return out, success_length

def extract_subject(s: str) -> str:
    subject = None
    my_lines = []
    for line in s.split("\n"):
        if line.strip() == "":
            continue
        if line.startswith("Subject:"):
            subject = line[len("Subject:"):]
            if len(subject) == 0:
                print(f"Warning: Found empty subject.")
                subject = None
            else:
                break
    return subject.strip() if subject else None
