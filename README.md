# 🚑a Medic CLI

> **"Because debugging at 2 AM is hard."**

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Beta-orange)

**Medic** is a self-healing developer tool that intercepts Python crashes, understands the context, and uses AI to fix your code automatically.

It doesn't just read the error message—it reads your **source code** (via AST), diagnoses the logic flaw, and performs a surgical transplant of the fixed function.

---

## ⚡ Features

* **🔍 Context-Aware:** Uses Python's Abstract Syntax Tree (AST) to extract the *exact* function that crashed, not just the line number.
* **🧠 Hybrid Brain:**
    * **Cloud Mode:** Uses Google Gemini (Fast, Smart) for users with API keys.
    * **Local Mode:** Uses Ollama (DeepSeek/Llama3) for offline, private debugging.
* **💉 Surgical Patching:** Automatically applies the fix to your file with a confirmation prompt. No copy-pasting required.
* **🛡️ Global Fallback:** Even if the crash happens outside a function, Medic grabs the surrounding context window to diagnose the issue.

---

## 📦 Installation

### Option 1: For Users (Install from Source)
Since this is a new tool, clone it and install it in "editable" mode so you can tweak it.

```bash
git clone [https://github.com/yourusername/medic-cli.git](https://github.com/yourusername/medic-cli.git)
cd medic-cli

# Create a virtual environment (Recommended)
python3 -m venv .venv
source .venv/bin/activate

# Install the tool
pip install -e .
