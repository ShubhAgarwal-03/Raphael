# Raphael

A local, offline-first command-line AI assistant for Windows. Raphael (internally called **Mini-JARVIS**) understands plain-English commands, opens and closes apps, plays music, runs web searches, does quick maths, and remembers things about you. Anything it can't handle with rules or tools is passed to a local LLM running through [Ollama](https://ollama.com), so nothing leaves your machine.

## Features

- **App control**: open and close apps by name or alias (`open browser`, `close notepad`, `close all chrome`), driven by a configurable app registry.
- **Music playback**: `play <song>` finds the track on YouTube with `yt-dlp` and opens it in Chrome. Results are cached so repeat requests are instant.
- **Web search**: `search <query>` or `google <query>` opens Google results in Chrome.
- **Calculator**: type an expression like `12*(3+4)` and get the answer directly, with no LLM call.
- **Persistent memory**: `remember <fact>` stores facts in `memory.json`. Use `show memory`, `search memory <keyword>`, or `clear memory`.
- **Rule inference**: phrases like "never open X" or "never close X" are turned into block rules, with authority levels (`system` > `user` > `derived`).
- **Layered response pipeline**: session cache, then semantic cache, then long-term memory, then tools, and only then the local LLM.
- **Semantic cache**: similar queries (cosine similarity ≥ 0.85, 10-minute TTL) reuse earlier answers via `sentence-transformers` embeddings.
- **Local LLM fallback**: unhandled queries go to an Ollama model (`phi3:mini` by default), with an automatic CPU retry on GPU out-of-memory errors.

## How It Works

```
user input
   │
   ▼
detect_intent ──► open / close / remember / show / search / clear / exit
   │ (unknown)
   ▼
planner ──► play → music tool │ search → web tool │ else delegate
   │
   ▼
search_manager
   1. session cache
   2. semantic cache
   3. long-term memory
   4. compute tool
   5. web search
   │ (no match)
   ▼
local LLM (Ollama)
```

## Project Structure

```
Raphael/
├── main.py              # Main loop, intent detection, memory, app control
├── config.py            # Ollama paths, model name, app registry loader
├── planner.py           # Routes play/search commands to tools
├── tool_executor.py     # Runs tools: web search, music (yt-dlp), compute
├── executor.py          # Launches external processes
├── rule_engine.py       # Block-rule checks
├── memory_store.py      # JSON load/save helpers for memory
├── system_info.py       # OS information helper
├── commands.py          # Simple built-in command map
├── utils.py             # Command logging
├── app_registry.json    # App paths, capabilities, aliases
├── memory.json          # Long-term memory (facts, preferences, rules, history)
├── memory/
│   ├── semantic_cache.py / .json   # Embedding-based response cache
│   └── song_cache.py / .json       # Song name → YouTube URL cache
└── tools/
    └── compute.py       # Safe expression extraction and evaluation
```

## Getting Started

### Prerequisites

- Windows 10/11 (app launching and closing use Windows-specific calls)
- Python 3.10+
- [Ollama](https://ollama.com) installed and running
- Google Chrome (path configured in `app_registry.json`)

### Installation

```bash
git clone https://github.com/ShubhAgarwal-03/Raphael.git
cd Raphael

pip install ollama yt-dlp sentence-transformers scikit-learn

ollama pull phi3:mini
```

### Run

```bash
python main.py
```

## Usage

| Command | What it does |
|---|---|
| `open chrome` / `open notepad` / `open calculator` | Launches the app (aliases like `browser` work too) |
| `close notepad` / `close all chrome` | Closes one or all instances |
| `play starboy` | Finds and plays the song on YouTube |
| `search python tutorials` | Opens a Google search |
| `25 * (4 + 2)` | Calculates directly |
| `remember I prefer Python over Java` | Saves a fact |
| `show memory` | Lists everything stored |
| `search memory python` | Searches stored memory |
| `clear memory` | Deletes stored facts (asks for confirmation) |
| `exit` / `quit` | Shuts down |
| Anything else | Answered by the local LLM |

## Configuration

**Add or change apps** in `app_registry.json`:

```json
{
  "chrome": {
    "windows": ["C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"],
    "capabilities": ["web_search", "music_play"],
    "aliases": ["browser", "google", "internet"]
  }
}
```

- `windows`: launch commands, tried in order
- `capabilities`: what the app can be used for (`web_search`, `music_play`, `compute`, `text_write`)
- `aliases`: alternative names you can say

**Change the model** by editing `MODEL_NAME` in `main.py` (default `phi3:mini`).

**Tune the semantic cache** in `memory/semantic_cache.py` (`CACHE_TTL`, `SIM_THRESHOLD`).

## Roadmap

- Cross-platform support (macOS/Linux)
- LLM-based intent detection as a fallback
- Unifying the duplicated memory helpers across `main.py` and `memory_store.py`
- Voice input and output

## Contributing

Issues and pull requests are welcome. For larger changes, please open an issue first to discuss what you'd like to change.

## Author

Shubh Agarwal: [@ShubhAgarwal-03](https://github.com/ShubhAgarwal-03)
