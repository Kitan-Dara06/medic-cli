# 🚑 Medic CLI

> **"Because debugging at 2 AM is hard."**

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Beta-orange)

**Medic** is a self-healing developer tool that intercepts Python crashes, understands the context, and uses AI to fix your code automatically.

It doesn't just read the error message—it reads your **source code** (via AST), diagnoses the logic flaw, and performs a surgical transplant of the fixed function.

---

## ⚡ Features

* **🔍 Context-Aware:** Uses Python's Abstract Syntax Tree (AST) to extract the *exact* function that crashed, not just the line number.
* **🧠 Hybrid Brain:** Choose your AI backend:
    * **Local Mode:** Uses Ollama (Llama3, DeepSeek, Mistral) for offline, private, free debugging
    * **Cloud Mode:** Uses OpenAI GPT-4 for powerful cloud-based debugging
    * **Auto Mode:** Intelligently picks the best available backend
* **💉 Surgical Patching:** Automatically applies the fix to your file with a confirmation prompt. No copy-pasting required.
* **🛡️ Global Fallback:** Even if the crash happens outside a function, Medic grabs the surrounding context window to diagnose the issue.
* **📊 Smart Logging:** Tracks crashes, fix rates, and error patterns over time.

---

## 📦 Installation

### Option 1: Install from Source

```bash
git clone https://github.com/yourusername/medic-cli.git
cd medic-cli

# Create a virtual environment (Recommended)
python3 -m venv .venv
source .venv/bin/activate

# Install the tool
pip install -e .
```

---

## 🚀 Quick Start

### 1. Local Mode (Recommended - Private & Free)

Install [Ollama](https://ollama.com) and pull a model:

```bash
# Install Ollama (macOS/Linux)
curl -fsSL https://ollama.com/install.sh | sh

# Pull a model (smaller = faster, larger = smarter)
ollama pull llama3.2        # Fast, good for quick fixes
ollama pull deepseek-r1:8b  # Better reasoning, slower
ollama pull mistral         # Balanced option

# Run Medic with local AI
medic script.py
```

### 2. Cloud Mode (OpenAI)

```bash
# Set your API key
export OPENAI_API_KEY="your-key-here"

# Run with OpenAI
medic --backend openai script.py
```

---

## 🎯 Usage

### Basic Usage

```bash
# Auto-select backend (prefers local Ollama if available)
medic script.py

# Force local backend
medic --backend ollama script.py

# Force cloud backend
medic --backend openai script.py

# Use a specific model
medic --backend ollama --model deepseek-r1:8b script.py

# Dry-run mode (see fixes without applying)
medic --dry-run script.py

# Auto-fix mode (apply fixes without prompting)
medic --auto-fix script.py

# Run any command
medic pytest tests/
medic python -m mypackage
```

### Check Available Backends

```bash
$ medic --list-backends

🧠 Available AI Backends:

  ollama  - ✅ Available
            Host: http://localhost:11434
            Default model: llama3.2

  openai  - ❌ No API key
            Set OPENAI_API_KEY or API_KEY env variable

💡 Auto-select will prefer Ollama (local) if available.
```

---

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OLLAMA_HOST` | Ollama server URL | `http://localhost:11434` |
| `OLLAMA_MODEL` | Default Ollama model | `llama3.2` |
| `OPENAI_API_KEY` | OpenAI API key | None |
| `API_KEY` | Legacy OpenAI key (fallback) | None |

### Example .env File

```bash
# ~/.medic/env or project root .env
OLLAMA_MODEL=deepseek-r1:8b
OPENAI_API_KEY=sk-...
```

---

## 🧠 Choosing a Backend

### When to Use Local (Ollama)

✅ **Pros:**
- Completely private—code never leaves your machine
- Free—no API costs
- Works offline
- No rate limits

❌ **Cons:**
- Requires sufficient RAM/CPU/GPU
- Smaller models may be less accurate than GPT-4
- First run needs to download models

**Best for:**
- Proprietary code you can't share
- Air-gapped environments
- High-volume debugging
- Cost-conscious teams

### When to Use Cloud (OpenAI)

✅ **Pros:**
- More powerful models (GPT-4)
- Faster inference
- No local resource requirements

❌ **Cons:**
- Sends code to external API
- API costs
- Requires internet

**Best for:**
- Complex bugs requiring deep reasoning
- When local models aren't accurate enough
- Quick setup without installing Ollama

---

## 🏥 How It Works

```
1. medic script.py
        ↓
2. Medic runs your script as a subprocess
        ↓
3. Captures any crash + traceback
        ↓
4. Uses AST to extract the exact function that failed
        ↓
5. Sends (code + error) to AI backend
        ↓
6. AI suggests a fix
        ↓
7. Medic shows a colored diff
        ↓
8. You confirm → fix is applied automatically
```

---

## 📊 Logging & Metrics

Medic tracks usage in `~/.medic/logs/`:

```bash
# View your stats (future feature)
medic --stats

# Logs include:
# - Crash frequency by error type
# - Fix success rates
# - Which backend performed better
```

---

## 🛠️ Troubleshooting

### "Cannot connect to Ollama"

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama server
ollama serve

# Or pull a model first
ollama pull llama3.2
```

### "OpenAI API key not found"

```bash
# Set the environment variable
export OPENAI_API_KEY="sk-..."

# Or add to your shell profile (~/.bashrc, ~/.zshrc)
echo 'export OPENAI_API_KEY="sk-..."' >> ~/.bashrc
```

### Slow fixes with local models

- Use a smaller model: `ollama pull llama3.2` (3B params) vs `llama3.1:70b` (70B params)
- Ensure your system has enough RAM
- Consider using OpenAI for complex bugs

---

## 🔒 Security & Privacy

| Backend | Code Sent to Cloud | Data Retained |
|---------|-------------------|---------------|
| Ollama | ❌ Never | Local only |
| OpenAI | ✅ Yes | Per OpenAI policy |

**Recommendation:** Use Ollama for proprietary code, OpenAI for open-source projects.

---

## 📝 License

MIT License - See LICENSE file for details.

---

## 🤝 Contributing

Contributions welcome! Areas we'd love help with:

- Additional AI backends (Claude, Gemini, local LLMs)
- Editor integrations (VS Code, Vim)
- More sophisticated AST analysis
- Test generation from fixes

---

> 💡 **Pro tip:** Run `medic --list-backends` to check your setup before debugging!
