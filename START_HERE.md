# START HERE — JARVIS Developer Onboarding

## You have 2 files in this folder:
- `prompt.md` — Full system design, all code, all modules (READ THIS FIRST)
- `jarvis_system_architecture.svg` — Visual architecture diagram (open in browser to see the full map)

---

## Step 1 — Understand the System (Day 1 Morning)
1. Open `jarvis_system_architecture.svg` in your browser — study the 4 layers
2. Read `prompt.md` top to bottom — everything is already designed for you
3. The architecture is: **Voice In → Claude AI Brain → Action Out → Laptop Control**

---

## Step 2 — Set Up the Project (Day 1 Morning)

```bash
# Create the project folder structure exactly as in prompt.md
mkdir jarvis && cd jarvis
mkdir tools data

# Create virtual environment
python -m venv jarvis-env
source jarvis-env/bin/activate       # Mac/Linux
# jarvis-env\Scripts\activate        # Windows

# Install all packages
pip install -r requirements.txt
playwright install chromium
```

---

## Step 3 — Add API Keys (Day 1)

Create `config.py` and fill in:
```python
ANTHROPIC_API_KEY = "your-key"   # Required — get from console.anthropic.com
ELEVENLABS_API_KEY = ""          # Optional (free voice works without this)
USER_NAME = "Your Name"
```

---

## Step 4 — Build in This Order (Do NOT skip steps)

| Day | What to Build | File | Test It By |
|-----|--------------|------|------------|
| Day 1 | TTS voice output | `tts.py` | Running `python tts.py` — should speak "Hello" |
| Day 1 | STT voice input | `stt.py` | Running `python stt.py` — should print what you say |
| Day 1 | AI Brain (no tools yet) | `brain.py` | Ask it a question, get a text reply |
| Day 2 | Connect voice + brain | `main.py` | Talk to it, it talks back |
| Day 2 | Computer control | `tools/computer_use.py` | Say "open Chrome" |
| Day 3 | Browser control | `tools/browser.py` | Say "search Google for weather" |
| Day 3 | File system | `tools/file_manager.py` | Say "create a file on desktop" |
| Day 4 | Memory | `memory.py` | It remembers your name next session |
| Day 4 | Safety layer | `safety.py` | It asks confirmation before deleting |
| Day 5 | Wake word | `wake_word.py` | Say "Hey JARVIS" to activate |

---

## Step 5 — Key Rules While Building

1. **Always test each module alone before connecting it** — don't connect voice + brain + tools all at once
2. **Start with text input** (type commands) before switching to voice — easier to debug
3. **The brain.py system prompt is the most important file** — tune it carefully
4. **Safety first** — the safety.py confirmation layer must be working before giving full laptop access
5. **Use `claude-sonnet-4-20250514`** as the model — do not change this

---

## Step 6 — First Working Version Goal

By end of Day 2, you should be able to:
- Say "Hey JARVIS"
- Ask "What time is it?" → JARVIS speaks the answer
- Say "Open Chrome" → Chrome opens
- Say "Type hello in the search bar" → it types

That is the MVP. Everything else builds on top.

---

## Questions?
All code, architecture, and module specs are inside `prompt.md`.
The diagram in `jarvis_system_architecture.svg` shows how all modules connect.
