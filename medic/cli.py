import ast
import re
import subprocess
import sys

from .brain import query_model
from .surgeon import construct_prompt


def parse_error(error_text):
    lines = error_text.splitlines()
    for line in reversed(lines):
        pattern = r'File "([^"]+)", line (\d+)'
        match = re.search(pattern, line)

        if match:
            file_path = match.group(1)
            line_num = int(match.group(2))
            return file_path, line_num

    return None, None


def get_context(file_path, crash_line):
    with open(file_path, "r") as file:
        content = file.read()

    source_code = ast.parse(content)
    for node in ast.walk(source_code):
        if isinstance(node, ast.FunctionDef):
            start = getattr(node, "lineno", -1)
            end = getattr(node, "end_lineno", -1)

            if start <= crash_line <= end:
                return ast.get_source_segment(content, node)
    return None


def get_file_window(file_path, crash_line, window=5):
    """
    Fallback: Just grab the lines around the crash if AST fails.
    """
    with open(file_path, "r") as file:
        lines = file.readlines()

    center_index = crash_line - 1

    start = max(0, center_index - window)
    end = min(len(lines), center_index + window + 1)

    return "".join(lines[start:end])


def apply_fix(file_path, old_code, new_code):
    with open(file_path, "r") as f:
        content = f.read()
    if old_code.strip() in content:
        new_content = content.replace(old_code.strip(), new_code.strip())

        with open(file_path, "w") as f:
            f.write(new_content)
        return True
    else:
        return False


def run_script(script_name):
    print({script_name})
    try:
        results = subprocess.run(
            ["python", script_name], capture_output=True, text=True, check=False
        )
        if results.returncode != 0:
            print("STDOUT", results.stdout)
            # print("STDERR:", results.stderr)
            file_name, line_num = parse_error(results.stderr)
            if file_name and line_num:
                print(f"Error found in {file_name} at line {line_num}")

                context = get_context(file_name, line_num)

                if not context:
                    print("crash seems global ")
                    context = get_file_window(file_name, line_num)

                if context:
                    print(f"The code that broke is {context}")
                    prompts = construct_prompt(context, results.stderr)
                    solution = query_model(prompts)
                    solution = (
                        solution.replace("```python", "").replace("```", "").strip()
                    )

                    print(solution)
                    user_choice = input("\nDo you want to apply this fix? (y/n): ")
                    if user_choice.lower() == "y":
                        success = apply_fix(file_name, context, solution)
                        if success:
                            print("Fix applied! Run your script again.")
                        else:
                            print(
                                "❌ Failed to apply fix. Context mismatch (Whitespace issue?)."
                            )
                    else:
                        print("Skipping fix.")
                else:
                    print("Could not extract function context")
            else:
                print("could not parse the error location")
            print("Return code:", results.returncode)
        else:
            print("STDOUT", results.stdout)

    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
    except subprocess.TimeoutExpired as e:
        print(f"Error: {e}")


def main():
    if len(sys.argv) >= 2:
        target_script = sys.argv[1]
        run_script(target_script)
    else:
        print("Usage: medic <script.py>")
        sys.exit(1)


if __name__ == "__main__":
    main()
