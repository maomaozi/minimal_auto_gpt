import os
import requests
import itertools
import tqdm
import json
from functools import wraps
from duckduckgo_search import ddg
import subprocess
import re
import numpy as np
import uuid

URL = "https://api.openai.com/v1/"
TOKEN = ""

# import tiktoken
# cl100k_base = tiktoken.get_encoding("cl100k_base")

task = "create a flask app, serve a document management api"

prompts = """Complete the task I gave you step by step by generating command. The list of commands you can use as follows:

1. save_variable: Save content into variable. parameter: [<variable_name>, <content>]
2. search: Search for content on the Internet, return variables of the contents if success. parameter: [<search keyword>]
3. write_file: Write variable to file. parameters: [<filename>, <variable_name>]
4. read_file: Read file to variable, return a variable of the result if success. parameter: [<filename>]
5. search_file: Search related text content in file, return variables of the contents if success. parameter: [<filename>, <search string>]
6. sh: Execute shell commands (only non-interactive commands can be used). parameters: [<shell_command>, <parameter1>, <parameter2>]
7. llm: Let a large language model (chatGPT) to generate some text result, return a variable of the result if success. parameters: [<prompts_string>]
8. stop: call this command while job is done. parameters: []

requirements:
1. Generate one single command at a time, and wait for me give you the result of the command execution
2. Before generating commands, think about what you have done, what you plan to do next, and why you are doing it
3. Save whatever you need to remember into the variable or file
4. Use llm commands for different job (like summarize, code generate, etc.) as much as possible to get work done
5. Use "{variable_name}" (include braces) to reference the existing variable for command parameter

limitations:
1. The content returned by the search command is not always accurate and requires additional cleaning work
2. The knowledge of llm is limited
3. llm can only handle contents less than 3000 words, so use search_file to get related information or summarize your inputs before generate prompts
4. llm can not access variables and files, pass the all information llm need as parameter instead
5. the code generate by llm always have some explanation and steps, you need to delete them manually

The format of the output is as follows:
{"thought": "<what you have done, what you plan to do next>", "command": {"name": "<command name>", "args":["<arg1>", "<arg2>"]}}

start you answer with: "{\"thought\""

{"task": "your task is to %s"}
""" % task

shot = '{"thought": "Before starting, I should save the task into a variable for later reference.", "command": {"name": "save_variable", "args": ["task", "%s"]}}' % task

messages = [
    {
        "role": "system",
        "content": "you are an AI help finish task by generate commands"
    },
    {
        "role": "user",
        "content": prompts
    },
    {
        "role": "assistant",
        "content": shot
    },
    {
        "role": "user",
        "content": '{"results": "task"}'
    }
]


class Chunker:
    DEFAULT_SHORT_LINE_LIMIT = 20
    DEFAULT_CHUNK_SOFT_LIMIT = 200
    DEFAULT_CHUNK_HARD_LIMIT = 300

    PUNCTUATIONS = [
        {"\n"},
        {".", "?", "!", "。", "？", "！", "…"},
        {",", "，", "：", "；", "、", " "}
    ]

    @staticmethod
    def get_text_chunks(text: str, soft_limit=DEFAULT_CHUNK_SOFT_LIMIT, hard_limit=DEFAULT_CHUNK_HARD_LIMIT):
        contents = Chunker.split(text, soft_limit, hard_limit)

        if len(contents) > 1 and len(contents[-1]) < soft_limit // 2:
            last = contents.pop()
            new_last = contents.pop() + last
            contents.append(new_last)

        return contents

    @staticmethod
    def split(text: str, soft_limit, hard_limit):
        if not text.strip():
            return []

        text = Chunker.remove_short_line_break(text)
        tokens = list(text)  # 不做tokenizer也无所谓吧

        chunks = []
        pos = 0

        while True:
            if pos >= len(tokens):
                return chunks

            if pos + hard_limit >= len(tokens):
                chunks.append("".join(tokens[pos:]))
                return chunks

            split_range = tokens[pos + soft_limit: pos + hard_limit]

            punc_pos = Chunker.get_punc_pos(split_range, soft_limit, hard_limit)
            chunks.append("".join(tokens[pos: pos + punc_pos + 1]))

            pos += punc_pos + 1

    @staticmethod
    def remove_short_line_break(input_str):
        input_str = re.sub("(\r\n|\r)", "\n", input_str)
        input_str = re.sub("(\r\n|\r|\n){3,}", "\n", input_str)
        input_str = re.sub("( ){3,}", " ", input_str)

        result = []
        lines = input_str.split("\n")

        for line in lines:
            if len(line) < Chunker.DEFAULT_SHORT_LINE_LIMIT:
                result.append(line.strip() + " ")
            else:
                result.append(line)

        return "".join(result)

    @staticmethod
    def get_punc_pos(split_range, soft_limit, hard_limit):
        for punc_set in Chunker.PUNCTUATIONS:
            for i, term in enumerate(split_range):
                if term in punc_set:
                    return i + soft_limit

        return hard_limit


def retry(times, print_exception=False):
    def _retry(func: callable) -> callable:
        @wraps(func)
        def new_func(*args, **kwargs) -> callable:
            for try_count in range(times):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    print("retry %d: for exception %s" % (try_count + 1, e)) if print_exception else None

        return new_func

    return _retry


@retry(times=3, print_exception=True)
def chat(messages):
    payload = json.dumps({
        "model": "gpt-3.5-turbo",
        "messages": messages,
        "temperature": 1.0,
        "n": 1
    })
    headers = {
        'Authorization': 'Bearer ' + TOKEN,
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", URL + "chat/completions", headers=headers, data=payload, timeout=200)

    data = json.loads(response.text)
    content = data["choices"][0]['message']['content']
    return content


@retry(times=3, print_exception=True)
def embedding(messages):
    payload = json.dumps({
        "input": messages,
        "model": "text-embedding-ada-002"
    })
    headers = {
        'Authorization': 'Bearer ' + TOKEN,
        'Content-Type': 'application/json'
    }
    response = requests.request(
        "POST", URL + "embeddings", headers=headers, data=payload, timeout=60)
    data = json.loads(response.text)
    return list(map(lambda x: x["embedding"], data["data"]))


def cosine_similarity(v1, v2):
    return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))


class CommandsContext:
    def __init__(self):
        self.variables = {}
        self.embeddings = {}

    def make_variable(self):
        return "variable_%s" % (str(uuid.uuid4())[0:8])

    def __save_variable(self, var_name, content):
        self.variables[var_name] = content
        return "{%s}" % var_name

    def save_variable(self, var_name, content):
        return {"results": self.__save_variable(var_name, content)}

    def search(self, keyword):
        return {"results": str(list(map(lambda item: self.__save_variable(self.make_variable(), item['body']),
                                        ddg(keyword, max_results=5)))).replace("'", "")}

    def write_file(self, filename, content):
        if len(content) < 10000:
            chunks = Chunker.get_text_chunks(content)
            self.embeddings[filename] = list(zip(embedding(chunks), chunks))

        with open(filename, 'a+') as f:
            f.write(content)
        return {"results": "success write to " + filename}

    def read_file(self, filename):
        with open(filename, 'r') as f:
            content = f.read()
        return self.save_variable(self.make_variable(), content)

    def search_file(self, filename, search_string):
        if filename not in self.embeddings:
            return {"results": "no such file" + filename}

        query_embedding = embedding([search_string])[0]

        result = sorted(self.embeddings[filename], key=lambda x: cosine_similarity(x[0], query_embedding),
                        reverse=True)[:5]
        return {
            "results": str(list(map(lambda x: self.__save_variable(self.make_variable(), x[1]), result))).replace("'",
                                                                                                                  "")}

    def sh(self, *cmd):
        if cmd[0].find(" ") != -1:
            cmd = cmd[0].split(" ") + cmd[1:]

        try:
            process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()

            if process.returncode == 0:
                res = stdout.decode("utf-8")
            else:
                res = stderr.decode("utf-8")
        except Exception as e:
            res = str(e)
        if len(res) > 350:
            return {"results": res[:200] + "..." + res[-100:]}
        return {"results": res}

    def llm(self, prompts):
        result = chat([
            {
                "role": "system",
                "content": "you are a helpful assistant, answer question clearly and concisely"
            },
            {
                "role": "user",
                "content": prompts
            }])
        return self.save_variable(self.make_variable(), result)

    def stop(self):
        exit()

    def exec_by_name(self, command_name, *args):
        def replace_var(arg):
            for item in self.variables:
                arg = arg.replace("{%s}" % item, self.variables[item])
            return arg

        replaced_args = [replace_var(arg) for arg in args]
        return getattr(self, command_name)(*replaced_args)


if __name__ == '__main__':
    context = CommandsContext()

    while True:
        result = chat(messages)
        try:
            print("RESPONSE: %s" % result)
            data = json.loads(result)

            if data['command']['name'] == "stop":
                print("job done...")
                exit()
        except Exception as ex:
            retry = input("Error load json, retry? y/n: ")
            if retry == 'y':
                print("retry...")
                continue
            else:
                exit()

        print("command: %s" % data['command'])
        retry = input("accept? y/n: ")
        if retry == 'y':
            pass
        else:
            print("retry...")
            continue

        messages.append({
            "role": "assistant",
            "content": result
        }, )

        exec_result = context.exec_by_name(data['command']['name'], *data['command']['args'])

        print("EXEC RESULT: %s" % exec_result)

        messages.append({
            "role": "user",
            "content": '{"results":%s}' % exec_result
        }, )
