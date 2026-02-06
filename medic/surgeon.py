def construct_prompt(code_context, error_message):
    """
    Constructs an enhanced prompt for the AI model with error-type specific guidance.
    
    Args:
        code_context: The code snippet where the error occurred
        error_message: The full error traceback message
    
    Returns:
        Enhanced prompt string for the AI model
    """
    
    # Extract error type from the error message
    error_type = "Unknown"
    if "NameError" in error_message:
        error_type = "NameError"
        specific_guidance = """
Common fixes for NameError:
- Add missing parameter to function signature
- Define the variable before use
- Check for typos in variable names
- Import missing modules or functions
"""
    elif "TypeError" in error_message:
        error_type = "TypeError"
        specific_guidance = """
Common fixes for TypeError:
- Add type conversion (int(), str(), float(), etc.)
- Add type checking before operations
- Ensure correct number of arguments
- Check for None values
"""
    elif "IndexError" in error_message:
        error_type = "IndexError"
        specific_guidance = """
Common fixes for IndexError:
- Add bounds checking (if len(list) > index)
- Use try/except to handle out of range
- Check if list is empty before accessing
- Use .get() for safer access
"""
    elif "ZeroDivisionError" in error_message:
        error_type = "ZeroDivisionError"
        specific_guidance = """
Common fixes for ZeroDivisionError:
- Add check: if divisor != 0
- Return default value or raise custom error
- Use try/except for division operations
"""
    elif "AttributeError" in error_message:
        error_type = "AttributeError"
        specific_guidance = """
Common fixes for AttributeError:
- Add type conversion to ensure correct type
- Check if attribute exists with hasattr()
- Add type checking before method calls
- Handle None values
"""
    elif "KeyError" in error_message:
        error_type = "KeyError"
        specific_guidance = """
Common fixes for KeyError:
- Use dict.get(key, default) instead of dict[key]
- Check if key exists: if key in dict
- Use try/except for key access
- Provide default values
"""
    elif "ImportError" in error_message or "ModuleNotFoundError" in error_message:
        error_type = "ImportError"
        specific_guidance = """
Common fixes for ImportError:
- Remove the problematic import if not needed
- Install the missing package
- Check for typos in module name
- Use try/except for optional imports
"""
    elif "SyntaxError" in error_message:
        error_type = "SyntaxError"
        specific_guidance = """
Common fixes for SyntaxError:
- Add missing colons, parentheses, or brackets
- Fix indentation issues
- Check for unclosed strings or brackets
- Ensure proper syntax structure
"""
    else:
        specific_guidance = """
General debugging approach:
- Identify the root cause from the error message
- Apply defensive programming practices
- Add appropriate error handling
- Ensure code follows Python best practices
"""
    
    return f"""You are an expert Python debugger and code repair specialist.

ERROR TYPE: {error_type}

BROKEN CODE:
```python
{code_context}
```

ERROR MESSAGE:
{error_message}

{specific_guidance}

YOUR MISSION:
1. Analyze the error and identify the root cause
2. Fix the code using best practices
3. Return ONLY the fully fixed code (no explanations, no markdown backticks)
4. Ensure the fix is minimal and focused on the error
5. The fixed code should be a complete drop-in replacement

IMPORTANT FORMATTING RULES:
- DO NOT use markdown code blocks (no ```)
- DO NOT include explanations or comments about the fix
- DO NOT return a diff or comparison
- Return ONLY the raw, fixed Python code
- Preserve original indentation and structure where possible

FIXED CODE:
"""
