import requests
from openai import OpenAI
import json
import subprocess
from openai.types.chat.chat_completion_message import FunctionCall
import zipfile
import os
import shutil
from bs4 import BeautifulSoup
import sys


class DivarContest:
    def __init__(self, api_token, base_url="https://api.metisai.ir/openai/v1"):
        self.api_token = api_token
        self.client = OpenAI(api_key=self.api_token, base_url=base_url)
        self.model = "gpt-4.1-mini"
        self.available_tools = {
            "read_file": self.read_file,
            "read_file_lines": self.read_file_lines,
            "write_file": self.write_file,
            "replace_code_block": self.replace_code_block,
            "run_python_file": self.run_python_file,
            "run_shell_command": self.run_shell_command,
            "list_files": self.list_files,
            "find_files_recursively": self.find_files_recursively,
            "make_directory": self.make_directory,
            "remove_directory": self.remove_directory,
            "download_file": self.download_file,
            "git_clone": self.git_clone,
            "unzip_file": self.unzip_file,
            "scrape_html_content": self.scrape_html_content,
        }

    def download_file(self, url, filename):
        try:
            response = requests.get(url, timeout=20)
            response.raise_for_status()
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            with open(filename, "wb") as f:
                f.write(response.content)
            return f"File downloaded and saved as {filename}"
        except requests.RequestException as e:
            return f"[ERROR] Failed to download {url}. Error: {str(e)}"

    def git_clone(self, repo_url, target_dir):
        try:
            result = subprocess.run(
                ["git", "clone", repo_url, target_dir],
                capture_output=True,
                text=True,
                timeout=120,
            )
            if result.returncode != 0:
                return f"[ERROR] Git clone failed. STDERR: {result.stderr}"
            return f"Repository {repo_url} cloned into {target_dir}"
        except FileNotFoundError:
            return "[ERROR] Git command not found. Is Git installed and in your PATH?"
        except Exception as e:
            return f"[ERROR] An unexpected error occurred during git clone: {str(e)}"

    def unzip_file(self, zip_path, extract_to):
        try:
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(extract_to)
            return f"Extracted {zip_path} to {extract_to}"
        except Exception as e:
            return f"[ERROR] Failed to unzip {zip_path}. Error: {str(e)}"

    def read_file(self, file_path):
        if not os.path.isfile(file_path):
            return f"[ERROR] Path is not a file: {file_path}"
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        except Exception as e:
            return f"[ERROR] Could not read file {file_path}. Error: {str(e)}"

    def read_file_lines(self, file_path, start_line, end_line):
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
            start_line = max(0, start_line - 1)
            end_line = min(len(lines), end_line)
            return "".join(lines[start_line:end_line])
        except Exception as e:
            return f"[ERROR] Could not read lines {start_line}-{end_line} from {file_path}. Error: {e}"

    def write_file(self, file_path, content):
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return f"Successfully written to {file_path}"
        except Exception as e:
            return f"[ERROR] Could not write to file {file_path}. Error: {str(e)}"

    def replace_code_block(self, file_path, start_marker, end_marker, new_content):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            start_index, end_index = -1, -1
            for i, line in enumerate(lines):
                if start_marker in line:
                    start_index = i
                if end_marker in line and i > start_index != -1:
                    end_index = i
                    break

            if start_index == -1 or end_index == -1:
                return f"[ERROR] Markers not found. Could not find '{start_marker}' and '{end_marker}' in {file_path}."

            new_lines = (
                lines[: start_index + 1] + [new_content + "\n"] + lines[end_index:]
            )

            with open(file_path, "w", encoding="utf-8") as f:
                f.writelines(new_lines)

            return f"Successfully replaced block between '{start_marker}' and '{end_marker}' in {file_path}."
        except Exception as e:
            return f"[ERROR] Failed to replace code block in {file_path}. Error: {e}"

    def run_python_file(self, file_path):
        try:
            python_executable = sys.executable
            result = subprocess.run(
                [python_executable, file_path],
                capture_output=True,
                text=True,
                timeout=30,
            )
            output = ""
            if result.stdout:
                output += f"[STDOUT]:\n{result.stdout}\n"
            if result.stderr:
                output += f"[STDERR]:\n{result.stderr}\n"
            return output.strip() if output else "Script ran with no output."
        except Exception as e:
            return f"[ERROR] An unexpected error occurred while running {file_path}: {str(e)}"

    def run_shell_command(self, command):
        try:
            result = subprocess.run(
                command, shell=True, capture_output=True, text=True, timeout=60
            )
            output = ""
            if result.stdout:
                output += f"[STDOUT]:\n{result.stdout}\n"
            if result.stderr:
                output += f"[STDERR]:\n{result.stderr}\n"
            return output.strip() if output else "Command ran with no output."
        except Exception as e:
            return f"[ERROR] Failed to run shell command '{command}'. Error: {str(e)}"

    def list_files(self, directory_path="."):
        if not os.path.isdir(directory_path):
            return f"[ERROR] Path is not a valid directory: {directory_path}"
        try:
            items = os.listdir(directory_path)
            return json.dumps(items)
        except Exception as e:
            return f"[ERROR] Could not list files in {directory_path}. Error: {str(e)}"

    def find_files_recursively(self, start_path: str, pattern: str):
        if not os.path.isdir(start_path):
            return f"[ERROR] Path '{start_path}' is not a valid directory."
        found_files = [
            os.path.join(root, name)
            for root, _, files in os.walk(start_path)
            for name in files
            if pattern in name
        ]
        return (
            json.dumps(found_files)
            if found_files
            else f"No files found matching '{pattern}' in '{start_path}'."
        )

    def make_directory(self, path):
        try:
            os.makedirs(path, exist_ok=True)
            return f"Directory ensured to exist: {path}"
        except Exception as e:
            return f"[ERROR] Failed to create directory: {str(e)}"

    def remove_directory(self, path: str):
        if not os.path.isdir(path):
            return f"[ERROR] Path '{path}' is not a directory. Cannot remove."
        try:
            shutil.rmtree(path)
            return f"Successfully removed directory: {path}"
        except Exception as e:
            return f"[ERROR] Failed to remove directory {path}. Error: {str(e)}"

    def scrape_html_content(self, url: str, selector: str = "body"):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            elements = soup.select(selector)
            full_text = " ".join(
                el.get_text(separator=" ", strip=True) for el in elements
            )
            return json.dumps({"content": full_text[:10000]})
        except Exception as e:
            return f"[ERROR] An error occurred during scraping: {str(e)}"

    def get_functions(self):
        return [
            {
                "name": "download_file",
                "description": "Download a single file from a URL and save it locally.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string"},
                        "filename": {"type": "string"},
                    },
                    "required": ["url", "filename"],
                },
            },
            {
                "name": "git_clone",
                "description": "Clones a git repository from a URL to a local directory. The standard way to get a codebase.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "repo_url": {"type": "string"},
                        "target_dir": {"type": "string"},
                    },
                    "required": ["repo_url", "target_dir"],
                },
            },
            {
                "name": "unzip_file",
                "description": "Unzip a .zip file to a specified directory.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "zip_path": {"type": "string"},
                        "extract_to": {"type": "string"},
                    },
                    "required": ["zip_path", "extract_to"],
                },
            },
            {
                "name": "read_file",
                "description": "Read the entire content of a local file.",
                "parameters": {
                    "type": "object",
                    "properties": {"file_path": {"type": "string"}},
                    "required": ["file_path"],
                },
            },
            {
                "name": "read_file_lines",
                "description": "Reads a specific range of lines from a file. Useful for inspecting code around an error.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string"},
                        "start_line": {"type": "integer"},
                        "end_line": {"type": "integer"},
                    },
                    "required": ["file_path", "start_line", "end_line"],
                },
            },
            {
                "name": "write_file",
                "description": "Write or overwrite string content to a file. Creates directories if they don't exist.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string"},
                        "content": {"type": "string"},
                    },
                    "required": ["file_path", "content"],
                },
            },
            {
                "name": "replace_code_block",
                "description": "Replaces a block of text in a file between two specified marker lines. Markers must be unique.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string"},
                        "start_marker": {"type": "string"},
                        "end_marker": {"type": "string"},
                        "new_content": {"type": "string"},
                    },
                    "required": [
                        "file_path",
                        "start_marker",
                        "end_marker",
                        "new_content",
                    ],
                },
            },
            {
                "name": "run_python_file",
                "description": "Execute a Python script and return its stdout and stderr.",
                "parameters": {
                    "type": "object",
                    "properties": {"file_path": {"type": "string"}},
                    "required": ["file_path"],
                },
            },
            {
                "name": "run_shell_command",
                "description": "Execute a shell command. Use with extreme caution. Useful for git, pip, etc.",
                "parameters": {
                    "type": "object",
                    "properties": {"command": {"type": "string"}},
                    "required": ["command"],
                },
            },
            {
                "name": "list_files",
                "description": "List all files and directories inside a given folder.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "directory_path": {"type": "string", "default": "."}
                    },
                    "required": [],
                },
            },
            {
                "name": "find_files_recursively",
                "description": "Find files recursively in a directory that match a string pattern.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "start_path": {"type": "string"},
                        "pattern": {"type": "string"},
                    },
                    "required": ["start_path", "pattern"],
                },
            },
            {
                "name": "make_directory",
                "description": "Create a new directory, including any necessary parent directories.",
                "parameters": {
                    "type": "object",
                    "properties": {"path": {"type": "string"}},
                    "required": ["path"],
                },
            },
            {
                "name": "remove_directory",
                "description": "Remove a directory and all its contents. Use for cleaning up the workspace.",
                "parameters": {
                    "type": "object",
                    "properties": {"path": {"type": "string"}},
                    "required": ["path"],
                },
            },
            {
                "name": "scrape_html_content",
                "description": "Scrape text from a webpage using a CSS selector.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string"},
                        "selector": {"type": "string", "default": "body"},
                    },
                    "required": ["url"],
                },
            },
        ]

    def handle_function_call(self, function_call: FunctionCall):
        func_name = function_call.name
        arguments = json.loads(function_call.arguments or "{}")

        if func_name in self.available_tools:
            function_to_call = self.available_tools[func_name]
            try:
                return str(function_to_call(**arguments))
            except Exception as e:
                return f"[ERROR] Failed to execute {func_name} with args {arguments}. Error: {str(e)}"
        else:
            return f"[ERROR] Function '{func_name}' is not an available tool."

    def capture_the_flag(self, question):
        system_prompt = """
### ROLE & GOAL ###
You are a senior autonomous software agent. Your goal is to solve the user's request by forming a plan and executing it using the available tools. You operate in a loop of Thought -> Action -> Observation.

### CORE PHILOSOPHY ###
1.  **Plan:** Start by creating a clear, step-by-step plan.
2.  **Workspace:** ALWAYS create a temporary working directory (e.g., './workspace') for each new task. Get the code using `git_clone` or `download_file`. Perform all operations inside this workspace.
3.  **Explore & Debug:** Use `list_files` and `read_file_lines` to understand the code. Use `run_python_file` and `run_shell_command` to test and debug.
4.  **Self-Correction:** If you encounter an error, analyze the observation, revise your plan, and try again. Use your debugging tools to isolate the problem.
5.  **Modify Code:** For fixing bugs, use `replace_code_block` for targeted changes or `write_file` to rewrite a whole file if necessary.
6.  **Cleanup:** Use `remove_directory` to clean up the workspace at the end if appropriate.

### OUTPUT FORMAT ###
When you have the final answer that directly addresses the user's entire request, provide it directly without any extra text or function calls.
"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"TASK: {question}"},
        ]

        functions = self.get_functions()

        for _ in range(50):
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                functions=functions,
                function_call="auto",
            )
            message = response.choices[0].message

            if message.function_call:
                function_call = message.function_call

                function_response = self.handle_function_call(function_call)

                messages.append(message)
                messages.append(
                    {
                        "role": "function",
                        "name": function_call.name,
                        "content": function_response,
                    }
                )
            else:
                return message.content.strip()

        return "Agent stopped after reaching the maximum loop limit."
