#!/usr/bin/env python3
import os
import sys
import re
from pathlib import Path
from datetime import datetime
from typing import Optional

# Assuming Chat.py exists with these functions
from Chat import chat, MODELS, token_count

SYSTEM = "You're a code completion assistant."
FILL = "{:FILL_HERE:}"
TASK = f"### TASK: complete the {FILL} part of the file above. Write ONLY the needed text to replace {FILL} by the correct completion, including correct spacing and indentation. Include the answer inside a <COMPLETION></COMPLETION> tag."

async def main():
    if len(sys.argv) < 2:
        print("Usage: holefill <file> [<shortened_file>] [<model_name>]")
        print("")
        print("This will complete a HOLE, written as '.?.', in <file>, using the AI.")
        print("A shortened file can be used to omit irrelevant parts.")
        sys.exit(1)

    file = sys.argv[1]
    mini = sys.argv[2] if len(sys.argv) > 2 else None
    model = sys.argv[3] if len(sys.argv) > 3 else "C"
    ask = chat(model)

    with open(file, 'r', encoding='utf-8') as f:
        file_code = f.read()
    
    mini_code = file_code
    if mini:
        with open(mini, 'r', encoding='utf-8') as f:
            mini_code = f.read()

    # Import context files
    regex = r"//\./(.*?)//"
    for match in re.finditer(regex, mini_code):
        import_path = Path(file).parent / match.group(1)
        if import_path.exists():
            with open(import_path, 'r', encoding='utf-8') as f:
                import_text = f.read()
            print("import_file:", match.group(0))
            mini_code = mini_code.replace(match.group(0), '\n' + import_text)
        else:
            print("import_file:", match.group(0), "ERROR")
            sys.exit(1)

    if mini:
        with open(mini, 'w', encoding='utf-8') as f:
            f.write(mini_code)

    tokens = token_count(mini_code)
    source = mini_code.replace(".?.", FILL)
    prompt = source + "\n\n" + TASK
    predict = "<COMPLETION>\n" + source + "</COMPLETION>"

    ai_dir = Path.home() / '.ai'
    ai_dir.mkdir(exist_ok=True)
    
    with open(ai_dir / '.holefill', 'w', encoding='utf-8') as f:
        f.write(f"{SYSTEM}\n###\n{prompt}")

    print("token_count:", tokens)
    print("model_label:", MODELS.get(model, model))

    if ".?." not in mini_code:
        print("No hole found.")
        sys.exit(1)

    reply = await ask(prompt, system=SYSTEM, model=model, max_tokens=8192)
    
    if "<COMPLETION>" not in reply:
        reply = "<COMPLETION>" + reply
    if "</COMPLETION>" not in reply:
        reply = reply + "</COMPLETION>"

    match = re.search(r"<COMPLETION>([\s\S]*?)</COMPLETION>", reply)
    if match:
        file_code = file_code.replace(".?.", match.group(1))
    else:
        print("Error: Could not find <COMPLETION> tags in the AI's response.")
        sys.exit(1)

    with open(file, 'w', encoding='utf-8') as f:
        f.write(file_code)

    save_prompt_history(SYSTEM, prompt, reply, MODELS.get(model, model))

def save_prompt_history(system: str, prompt: str, reply: str, model: str):
    timestamp = datetime.now().isoformat().replace(':', '-').replace('.', '-')
    log_dir = Path.home() / '.ai' / 'prompt_history'
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log_path = log_dir / f"{timestamp}_{model}.log"
    log_content = f"SYSTEM:\n{system}\n\nPROMPT:\n{prompt}\n\nREPLY:\n{reply}\n\n"
    
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(log_content)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
