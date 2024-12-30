#!/usr/bin/env python3

import readline
import subprocess
import asyncio
import os
import sys
import datetime
import re
from pathlib import Path

# Import chat function and models from Chat.py
from Chat import chat, MODELS

# Default model if not specified
DEFAULT_MODEL = "c"
# Get model from environment variable or use default 
MODEL = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_MODEL

print(f"Welcome to ChatSH. Model: {MODELS.get(MODEL, MODEL)}\n")

# System prompt to set the assistant's behavior
SYSTEM_PROMPT = '''You are ChatSH, an AI language model that specializes in assisting users with tasks on their system using shell commands, AND chatting or answering open-ended questions via the terminal.

# CHATSH GUIDE:

- If the USER asks you to perform a SYSTEM TASK, ChatSH must answer with a SHELL SCRIPT to perform the task.

- If the USER asks an open-ended question, ChatSH must answer with a friendly, concise, factual response.

# EXAMPLE 1: CHATTING AND PERFORMING SYSTEM COMMANDS

<USER>
Show me local files.
</USER>

<ChatSH>
\`\`\`sh
ls
\`\`\`
</ChatSH>

<SYSTEM>
example.gif example.tst example_dir/
</SYSTEM>

<USER>
Is there any text file?
</USER>

<ChatSH>
Yes, there is a file named example.txt in the current directory
</ChatSH>

<USER>
Show me the contents of example.txt.
</USER>

<ChatSH>
\`\`\`sh
cat example.txt
\`\`\`
</ChatSH>

<SYSTEM>
Na matemática, um grupo é um conjunto de elementos associados a uma operação que combina dois elementos quaisquer para formar um terceiro. Para se qualificar como grupo o conjunto e a operação devem satisfazer algumas condições chamadas axiomas de grupo: associatividade, elemento neutro e elementos inversos.
</SYSTEM>

<USER>
Can you translate the first sentence to English?
</USER>

<ChatSH>
In mathematics, a group is a set of elements associated with an operation that combines any two elements to form a third element.
</ChatSH>

<USER>
What is the monster group?
</USER>

<ChatSH>
The monster group is the largest sporadic simple group, with order approximately 8×10^53.
</ChatSH>

<USER>
What is a simple group?
</USER>

<ChatSH>
A simple group is a nontrivial group that contains no proper nontrivial normal subgroups.
</ChatSH>

<USER>
Move the text file to that dir.
</USER>

<ChatSH>
\`\`\`sh
mv example.txt example_dir/
\`\`\`
</ChatSH>

# EXAMPLE 2: ASSISTING WITH CODING TASKS

<USER>
Fix main.ts
</USER>

<ChatSH>
\`\`\`sh
cat main.ts
tsc --noEmit main.ts
\`\`\`
</ChatSH>

<SYSTEM>
import List from './list';
import map from './map';

const n_1_2: List<number> = { $: "cons", head: 1, tail: { $: "cons", head: 2, tail: { $: "nil" }}};
const n_2_4: List<number> = map(n_1_2, x => x * 2);

console.log(JSON.stringify(n_2_4));

map.ts:7:22 - error TS2345: Argument of type '(val: T) => U' is not assignable to parameter of type 'List<unknown>'.

7       let tail = map(fun, list.tail);
                       ~~~
</SYSTEM>

<ChatSH>
\`\`\`sh
ls
\`\`\`
</ChatSH>

<SYSTEM>
list.ts main.ts map.ts
</SYSTEM>

<ChatSH>
\`\`\`sh
cat map.ts
\`\`\`
</ChatSH>

<SYSTEM>
import List from './list';

function map<T, U>(list: List<T>, fun: (val: T) => U): List<U> {
  switch (list.$) {
    case "cons":
      let head = fun(list.head);
      let tail = map(fun, list.tail);
      return { $: "cons", head, tail };
    case "nil":
      return { $: "nil" };
  }
}

export default map;
</SYSTEM>

<ChatSH>
\`\`\`sh
cat > map.ts << EOL
import List from './list';

function map<T, U>(list: List<T>, fun: (val: T) => U): List<U> {
  switch (list.$) {
    case "cons":
      let head = fun(list.head);
      let tail = map(list.tail, fun);
      return { $: "cons", head, tail };
    case "nil":
      return { $: "nil" };
  }
}

export default map;
EOL
tsc --noEmit map.ts
\`\`\`
</ChatSH>

<SYSTEM>

</SYSTEM>

<ChatSH>
Done.
</ChatSH>

## NOTES:

- In COMMAND MODE, answer with SH BLOCKS.

- In TEXT MODE, answer with normal text.

- Be concise, objective, correct and factual.

- Do not attempt to install new tools; assume they're available.

- Do not include the <ChatSH> tags in your answer.

- REMEMBER: you are NOT limited to system tasks or shell commands. You must answer ANY question or request by the user.

- The system shell in use is: %s.'''%os.environ['SHELL']

# Create history directory
HISTORY_DIR = Path.home() / '.ai' / 'chatsh_history'
HISTORY_DIR.mkdir(parents=True, exist_ok=True)

# Generate unique filename for conversation
conversation_file = HISTORY_DIR / f"conversation_{datetime.datetime.now().isoformat().replace(':', '-')}.txt"

def append_to_history(role, message):
    with open(conversation_file, 'a') as f:
        f.write(f"<{role}>\n{message}\n</{role}>\n\n")

def extract_codes(text):
    regex = r"```sh([\s\S]*?)```"
    matches = re.finditer(regex, text)
    return [match.group(1).replace('$', '$$').strip() for match in matches]

async def get_shell():
    proc = await asyncio.create_subprocess_shell(
        'uname -a && $SHELL --version',
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    stdout, _ = await proc.communicate()
    return stdout.decode().strip()

async def main():
    last_output = ""
    ask = chat(MODEL)

    if MODEL in ["o", "om"]:
        print("NOTE: disabling system prompt.")

    # Get initial message from command line args if provided
    initial_message = ' '.join(sys.argv[2:]) if len(sys.argv) > 2 else None

    while True:
        try:
            if initial_message is not None:
                user_message = initial_message
                initial_message = None
            else:
                print('\033[1m', end='')  # bold
                user_message = input('λ ')
                print('\033[0m', end='')  # reset

            full_message = f"<SYSTEM>\n{last_output.strip()}\n</SYSTEM>\n<USER>\n{user_message}\n</USER>\n" if user_message.strip() else f"<SYSTEM>\n{last_output.strip()}\n</SYSTEM>"

            append_to_history('USER', user_message)

            # Handle different model types
            if MODEL in ["o", "om"]:
                assistant_message = await ask(full_message, {"system": None, "model": MODEL, "max_tokens": 8192, "system_cacheable": True})
            else:
                assistant_message = await ask(full_message, {"system": SYSTEM_PROMPT, "model": MODEL, "max_tokens": 8192, "system_cacheable": True})

            print()
            append_to_history('ChatSH', assistant_message)

            codes = extract_codes(assistant_message)
            last_output = ""

            if codes:
                combined_code = '\n'.join(codes)
                print("\033[31mPress enter to execute, or 'N' to cancel.\033[0m")
                answer = input()
                # Clear the warning
                print('\033[2A')  # Move cursor up 2 lines
                print('\033[K')   # Clear line

                if answer.lower() == 'n':
                    print('Execution skipped.')
                    last_output = "Command skipped.\n"
                else:
                    try:
                        proc = await asyncio.create_subprocess_shell(
                            combined_code,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE
                        )
                        stdout, stderr = await proc.communicate()
                        output = f"{stdout.decode().strip()}{stderr.decode().strip()}"
                        print('\033[2m' + output.strip() + '\033[0m')
                        last_output = output
                        append_to_history('SYSTEM', output)
                    except Exception as e:
                        output = str(e)
                        print('\033[2m' + output.strip() + '\033[0m')
                        last_output = output
                        append_to_history('SYSTEM', output)

        except Exception as e:
            print(f"Error: {str(e)}")
            append_to_history('ERROR', str(e))

if __name__ == "__main__":
    asyncio.run(main())
