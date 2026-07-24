# AI Model Balance Monitor

> System tray · Mini float window · Auto query · 22 paid AI providers

A Windows desktop utility that lets you glance at your API balance across DeepSeek, Kimi, Qwen, and other AI platforms.

---

## Getting Started

**Run directly (zero pip install)**

```powershell
python ai_model_monitor.py
```

All dependencies are vendored in the project. Only Python 3.10+ needed.

**Or build a standalone EXE**

```powershell
pip install pyinstaller
pyinstaller --clean --noconfirm ai_model_monitor.spec
# Output: dist\Ai_MB.exe (copy to any Windows PC, double-click to run)
```

An icon appears in the system tray. Hover to open the main panel — it auto-hides when your cursor leaves.

**Configure API Keys**

Click ⚙ to open settings. Paste a key and it auto-detects the provider. The 💳 button on each row opens that platform's billing page in your browser. Save and balances are queried automatically.

**Build EXE**

```powershell
pip install pyinstaller
pyinstaller --clean --noconfirm ai_model_monitor.spec
```

---

## Features

- **System tray resident** — Hover to open, leave to hide. No screen clutter.
- **Mini balance float** — Always-on-top strip in the top-right corner. Click to cycle providers.
- **Scheduled auto-fetch** — 1–60 min interval, defaults to 10 min.
- **Concurrent queries** — Up to 5 keys queried in parallel.
- **Key auto-detection** — Paste a key and it knows which provider it belongs to.
- **Billing link shortcuts** — Hover on 💳 to see the URL, click to open in browser.
- **Ranking sync** — Pull latest Coding leaderboard from llm-stats.com with one click.
- **Encrypted storage** — Keys encrypted via Windows DPAPI, accessible only by your account.
- **Single-instance lock** — Named Mutex, no lock files, auto-releases on crash.

---

## Supported Providers

| Provider | Status |
|---|---|
| 🐋 DeepSeek | ✅ Auto balance (CNY) |
| 🌙 Kimi | ✅ Balance + token quota + rate limits |
| ☁️ Qwen | ✅ Pay-as-you-go / Token Plan |
| 🧠 GLM | 🔬 Pending key test |
| 🟢 NVIDIA NIM | 🔬 Pending key test |
| 🫘 Doubao | 🔬 Pending key test |
| 🌬️ Mistral | 🔬 Pending key test |
| 🤝 Cohere | 🔬 Pending key test |
| 🤖 OpenAI | ⚠ Requires Session Key |
| 🐧 Hunyuan | ⚠ Requires HMAC signature |

12 more providers (Claude, Gemini, Grok, MiniMax, Azure, etc.) support manual balance tracking.

---

## Data Files

All stored alongside the EXE:

| File | Content |
|---|---|
| `AI_config.enc` | Encrypted keys + settings (DPAPI) |
| `AI_model_data.json` | Cached balances (no keys) |
| `AI_ranking_cache.json` | Cached leaderboard |

---

## Security

- All API requests over HTTPS
- Keys encrypted with Windows DPAPI — tied to your account
- Balance cache never contains keys
- Named Mutex prevents duplicate instances

---

## Version

**v5.5.0** — 2026-07-25
