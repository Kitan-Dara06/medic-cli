import argparse
import ast
import difflib
import re
import subprocess
import sys
from unittest import result
from weakref import KeyedRef

from .brain import query_model
from .surgeon import construct_prompt

try:
    from .logger import get_logger
    LOGGING_AVAILABLE = True
except ImportError:
    LOGGING_AVAILABLE = False
    def get_logger(*args, **kwargs):
        return None


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

    try:
        # Try to understand the code structure
        source_code = ast.parse(content)
    except SyntaxError:
        print("⚠️  Patient file has Syntax Errors. AST Parsing failed.")
        return None

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


def show_diff(old_code, new_code):
    """
    Display a colored diff between old and new code
    """
    old_lines = old_code.strip().splitlines(keepends=True)
    new_lines = new_code.strip().splitlines(keepends=True)
    
    diff = difflib.unified_diff(
        old_lines,
        new_lines,
        fromfile="original",
        tofile="fixed",
        lineterm=""
    )
    
    print("\n--- PROPOSED CHANGES ---")
    for line in diff:
        if line.startswith("+") and not line.startswith("+++"):
            print(f"\033[92m{line}\033[0m", end="")  # Green for additions
        elif line.startswith("-") and not line.startswith("---"):
            print(f"\033[91m{line}\033[0m", end="")  # Red for deletions
        else:
            print(line, end="")
    print("\n--- END CHANGES ---\n")


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


def run_script(command_args, dry_run=False, auto_fix=False, enable_logging=True):
    """
    Run a script and monitor for crashes
    
    Args:
        command_args: Command to run
        dry_run: If True, show fixes but don't apply them
        auto_fix: If True, automatically apply fixes without prompting
        enable_logging: If True, log events to the logger
    """
    logger = get_logger(enable_logging and LOGGING_AVAILABLE)
    
    print(f"🚀 Medic Running: {' '.join(command_args)}")
    if dry_run:
        print("🔍 DRY-RUN MODE: Fixes will be shown but not applied")
    if auto_fix:
        print("⚡ AUTO-FIX MODE: Fixes will be applied automatically")

    # 1. Start the process (Merging stderr into stdout)
    process = subprocess.Popen(
        command_args,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    captured_logs = []

    # 2. Stream the output live
    try:
        for line in process.stdout:
            print(line, end="")  # Print live to screen
            captured_logs.append(line)  # Save for later

        process.wait()  # Wait for exit code
    except KeyboardInterrupt:
        print("\n🛑 Stopping...")
        process.terminate()
        return

    # 3. Check for crashes
    if process.returncode != 0:
        print("\n❌ Process Crashed.")

        # WE USE THIS instead of process.stdout (which is now empty)
        full_error_log = "".join(captured_logs)

        file_name, line_num = parse_error(full_error_log)

        if file_name and line_num:
            print(f"📍 Traceback points to: {file_name} at line {line_num}")

            # Extract error type for logging
            error_type = "Unknown"
            for err in ["NameError", "TypeError", "IndexError", "ZeroDivisionError", 
                       "AttributeError", "KeyError", "ImportError", "SyntaxError"]:
                if err in full_error_log:
                    error_type = err
                    break
            
            if logger:
                logger.log_crash(file_name, line_num, error_type, full_error_log)

            context = get_context(file_name, line_num)

            if not context:
                print("⚠️  Context is global/complex. Fetching window...")
                context = get_file_window(file_name, line_num)

            if context:
                print(f"\n--- MEDIC DIAGNOSIS ---\n{context}")

                # FIX 1: Pass 'full_error_log', NOT 'process.stderr' (which is None)
                prompts = construct_prompt(context, full_error_log)

                solution = query_model(prompts)

                # Sanitize the solution
                if solution:
                    solution = (
                        solution.replace("```python", "").replace("```", "").strip()
                    )
                    print(f"\n--- AI SUGGESTED FIX ---\n{solution}\n")

                    if logger:
                        logger.log_fix_generated(file_name, context, solution)
                    
                    # Show diff preview
                    show_diff(context, solution)
                    
                    if dry_run:
                        print("🔍 DRY-RUN: Fix preview shown above. No changes applied.")
                        return
                    
                    # Decide whether to apply
                    should_apply = False
                    if auto_fix:
                        should_apply = True
                        print("⚡ AUTO-FIX: Applying fix automatically...")
                    else:
                        user_choice = input("\nDo you want to apply this fix? (y/n): ")
                        should_apply = user_choice.lower() == "y"
                    
                    if should_apply:
                        success = apply_fix(file_name, context, solution)
                        if success:
                            print("✅ Fix applied! Run your script again.")
                            if logger:
                                logger.log_fix_applied(file_name, True)
                        else:
                            print("❌ Failed to apply fix. Context mismatch.")
                    else:
                        print("Skipping fix.")
            else:
                print("❌ Could not extract code context.")
        else:
            print("⚠️  Could not find a file path in the traceback.")

    else:
        print("\n✅ Process finished successfully.")


def main():
    if len(sys.argv) < 2:
        print("Usage: medic <script.py> OR medic <command>")
        sys.exit(1)

    user_args = sys.argv[1:]
    if len(user_args) == 1 and user_args[0].endswith(".py"):
        command = ["python", user_args[0]]
    else:
        command = user_args

    run_script(command)


if __name__ == "__main__":
    main()
