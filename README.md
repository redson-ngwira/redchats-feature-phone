# FeatureChat

**AI chatbot built for feature phones.** No JavaScript. No heavy CSS. Just XHTML-MP, keypad navigation, and Cerebras AI.

By **Redson Ngwira**

## Why

1 billion+ people still use feature phones. They deserve AI too. FeatureChat brings ChatGPT-level intelligence to devices with tiny screens, T9 keypads, and browsers that can't run JavaScript.

## Features

| Feature | Description |
|---|---|
| **AI Chat** | Powered by Cerebras free tier (GPT-OSS 120B, Llama 3.3 70B, Llama 4 Scout, DeepSeek R1) |
| **Web Search** | AI can search the web via DuckDuckGo tool calling for current info |
| **Phone + PIN Auth** | Simple registration — phone number and 4-6 digit PIN |
| **Multiple Conversations** | Create, rename, pin, delete, switch between threads |
| **Personas** | 6 built-in AI personas (Helper, Teacher, Coder, Writer, Translator, Summarizer) + custom |
| **Quick Actions** | 9 keypad shortcuts — type `1 sun` to get "Explain this simply: sun" |
| **Memory** | AI extracts and remembers facts about you across conversations |
| **Context Summarization** | Long conversations auto-summarized to fit the token budget |
| **Daily Prompts** | Pre-built useful prompts to save T9 typing (`/d`) |
| **SMS Export** | Export conversations as SMS-ready 160-char chunks |
| **Sharing** | Share prompts/personas via 6-character codes |
| **Token Tracking** | Warns at 80% of Cerebras 1M daily free token limit |

## Architecture

```
featurechat/          # Django project config
accounts/             # Phone + PIN authentication
chat/                 # Core chat engine, Cerebras API, tool calling
conversations/        # Conversation threads with auto-summarization
personas/             # AI system prompts / personalities
quickactions/         # Keypad shortcut prompt templates
memory/               # Cross-conversation fact extraction
sharing/              # Share codes for prompts
export/               # SMS and text export
templates/            # XHTML-MP templates (no JS, minimal CSS)
```

## Tech Stack

- **Backend**: Django 5.x, Python 3.11+
- **AI**: Cerebras Inference API (OpenAI-compatible, 1M tokens/day free)
- **Search**: DuckDuckGo Instant Answer API (via Cerebras tool calling)
- **Markup**: XHTML-MP 1.0
- **Database**: SQLite (swappable to PostgreSQL)

## Quick Start

```bash
# Clone and enter directory
cd featurechat

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env and add your Cerebras API key:
#   CEREBRAS_API_KEY=your-key-here
# Get one free at: https://cloud.cerebras.ai/

# Run migrations
python manage.py migrate

# Start the server
python manage.py runserver 0.0.0.0:8000
```

Open `http://localhost:8000` in your browser (disable JavaScript for authentic feature phone experience, or use `w3m` / `lynx`).

## Usage on a Feature Phone

### Navigation
Every page has a numbered nav bar at the bottom:
```
1:Chat  2:Convos  3:Personas  4:Actions  5:Mem  6:Set  0:Out
```

### Chat Commands
Type these in the message box:
```
/c       Clear current chat
/n       New conversation
/p       Switch persona
/m       Memory management
/q       Quick actions
/s       Switch conversation
/d       Daily prompts
/e       Export as SMS
/model   Change AI model
/help    Show all commands
```

### Quick Actions
Type a number + space + your text to use a shortcut:
```
1 photosynthesis    → "Explain this simply: photosynthesis"
2 long article...   → "Summarize the following: long article..."
3 bonjour           → "Translate to English: bonjour"
```

### Response Chunking
Long AI responses are split into ~120 character pages. Navigate with [Next] / [Prev] / [Full] links.

## Configuration

Environment variables in `.env`:

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | auto-generated | Django secret key |
| `CEREBRAS_API_KEY` | (required) | Your Cerebras API key |
| `DEBUG` | `True` | Django debug mode |
| `ALLOWED_HOSTS` | `*` | Comma-separated hostnames |

Settings in `featurechat/settings.py`:

| Setting | Default | Description |
|---|---|---|
| `CEREBRAS_DEFAULT_MODEL` | `gpt-oss-120b` | Default AI model |
| `CEREBRAS_DAILY_TOKEN_LIMIT` | `1,000,000` | Daily token budget warning |
| `MESSAGES_PER_PAGE` | `3` | Messages shown per chat page |
| `RESPONSE_CHUNK_SIZE` | `120` | Characters per response chunk |

## How Context Works

Like ChatGPT, FeatureChat fills the context window intelligently:

1. System prompt (persona + memory) — always included, cached by Cerebras
2. Recent messages — newest first, until the 6000-token budget is full
3. If older messages don't fit — they're auto-summarized by AI and the summary is injected as context

This means users can have long conversations and the AI remembers everything, even on a small token budget.

## Deploying for Real Feature Phones

1. Deploy behind a WAP gateway or use a service like Opera Mini server
2. Set `Content-Type: application/xhtml+xml` (already configured)
3. Set `DEBUG=False` and a proper `SECRET_KEY`
4. Use PostgreSQL for production
5. Consider adding HTTPS via a reverse proxy (nginx/caddy)
6. Feature phone browsers: Opera Mini, UC Browser, Bolt, Nokia Xpress

## License

MIT

---

*Built by Redson Ngwira*
