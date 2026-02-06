def construct_prompt(code_context, error_message):
    return f"""you are python debugger.
   The broken code is :
      {code_context}
     and the error message is {error_message}
     YOUR MISSION:
     Fix the code.
     Return ONLY the fully fixed function code.
     DO NOT use Markdown backticks (```).
     DO NOT return a Diff. Just the raw code.
    """
