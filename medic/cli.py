import argparse
import ast
import difflib
import re
import subprocess
import sys

from .brain import query_model, BackendFactory
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


def run_script(command_args, dry_run=False, auto_fix=False, enable_logging=True, backend=None, model=None):
    """
    Run a script and monitor for crashes

    Args:
        command_args: Command to run
        dry_run: If True, show fixes but don't apply them
        auto_fix: If True, automatically apply fixes without prompting
        enable_logging: If True, log events to the logger
        backend: AI backend to use ("openai", "ollama", or None for auto-select)
        model: Specific model to use (e.g., "gpt-4", "deepseek-r1:8b")
    """
    logger = get_logger(enable_logging and LOGGING_AVAILABLE)

    print(f"🚀 Medic Running: {' '.join(command_args)}")
    if dry_run:
        print("🔍 DRY-RUN MODE: Fixes will be shown but not applied")
    if auto_fix:
        print("⚡ AUTO-FIX MODE: Fixes will be applied automatically")
    if backend:
        print(f"🧠 Using backend: {backend}")
    if model:
        print(f"🤖 Using model: {model}")

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

                solution = query_model(prompts, backend=backend, model=model)

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
    parser = argparse.ArgumentParser(
        description="🚑 Medic CLI - AI-powered Python debugging",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  medic script.py                  # Run script with auto-selected backend
  medic --backend ollama script.py # Force local Ollama backend
  medic --backend openai script.py # Force OpenAI backend
  medic --dry-run script.py        # Show fixes without applying
  medic --auto-fix script.py       # Apply fixes automatically
  medic pytest tests/              # Run any command with monitoring

Backends:
  ollama      - Local models (private, offline, free). Requires Ollama installed.
  openai      - Cloud GPT models. Requires OPENAI_API_KEY env variable.
  (auto)      - Defaults to Ollama if available, falls back to OpenAI.

Environment Variables:
  OLLAMA_HOST     - Ollama server URL (default: http://localhost:11434)
  OLLAMA_MODEL    - Default Ollama model (default: llama3.2)
  OPENAI_API_KEY  - OpenAI API key (or use API_KEY for legacy support)
        """
    )

    parser.add_argument(
        "command",
        nargs="*",
        help="Python script or command to run (e.g., script.py or pytest)"
    )

    parser.add_argument(
        "--backend",
        choices=["openai", "ollama"],
        default=None,
        help="AI backend to use (default: auto-select)"
    )

    parser.add_argument(
        "--model",
        default=None,
        help="Specific model to use (e.g., 'gpt-4', 'deepseek-r1', 'mistral')"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show proposed fixes without applying them"
    )

    parser.add_argument(
        "--auto-fix",
        action="store_true",
        help="Automatically apply fixes without prompting"
    )

    parser.add_argument(
        "--no-log",
        action="store_true",
        help="Disable logging"
    )

    parser.add_argument(
        "--list-backends",
        action="store_true",
        help="List available backends and their status"
    )

    args = parser.parse_args()

    # Validate: either --list-backends or a command must be provided
    if not args.list_backends and not args.command:
        parser.error("Please provide a command to run (e.g., medic script.py) or use --list-backends")

    # Handle --list-backends
    if args.list_backends:
        print("🧠 Available AI Backends:")
        print()

        # Check Ollama
        from .brain import OllamaBackend
        ollama = OllamaBackend()
        ollama_status = "✅ Available" if ollama.is_available() else "❌ Not connected"
        print(f"  ollama  - {ollama_status}")
        print(f"            Host: {ollama.host}")
        print(f"            Default model: {ollama.model}")
        print()

        # Check OpenAI
        from .brain import OpenAIBackend
        openai = OpenAIBackend()
        openai_status = "✅ Available" if openai.is_available() else "❌ No API key"
        print(f"  openai  - {openai_status}")
        if openai.is_available():
            print(f"            Default model: {openai.model}")
        else:
            print(f"            Set OPENAI_API_KEY or API_KEY env variable")
        print()

        print("💡 Auto-select will prefer Ollama (local) if available.")
        return

    # Build the command to monitor
    user_args = args.command
    if len(user_args) == 1 and user_args[0].endswith(".py"):
        command = ["python", user_args[0]]
    else:
        command = user_args

    # Run with the selected backend
    run_script(
        command,
        dry_run=args.dry_run,
        auto_fix=args.auto_fix,
        enable_logging=not args.no_log,
        backend=args.backend,
        model=args.model
    )


if __name__ == "__main__":
    main()
