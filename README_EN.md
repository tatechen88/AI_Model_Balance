# MiGPT-TateMig

MiGPT-TateMig is a local voice bridge for Xiaomi speakers. It polls MiNA conversation records, sends ordinary requests to an OpenAI-compatible LLM, and replies through Volcano TTS, Edge TTS, or Xiaomi native speech. It can also resolve supported Taiwan radio pages and play their online audio directly on the speaker.

The project connects services that you provide. It does not host Xiaomi accounts, API keys, LLMs, TTS, or audio content.

Chinese documentation: [README.md](README.md)

## Implemented capabilities

- Poll MiNA records with `wake`, `proxy`, and `silent` modes.
- Select Xiaomi devices, control volume/mute/wake, send text replies, and play URLs through MiNA/MiIO.
- Use an OpenAI-compatible `/v1/chat/completions` endpoint for ordinary conversation and learning follow-ups.
- Play five configurable Taiwan radio categories: news, songs, English, stories, and English learning.
- Keep local SQLite memory, reading records, English-learning records, and a FastAPI web console.

## Taiwan radio categories

The console has five multiline URL fields under `Routing → Taiwan radio`. Enter one webpage URL per line. Blank and duplicate lines are removed, only HTTP(S) URLs are accepted, and pages are tried from top to bottom as fallbacks.

| Category | Simplified command | Traditional command | Default page |
| --- | --- | --- | --- |
| News | `播放台湾新闻` | `播放台灣新聞` | `https://www.radiotaiwan.tw/zhong-guang-xin-wen-wang` |
| Songs | `播放台湾歌曲` | `播放台灣歌曲` | `https://www.radiotaiwan.tw/zhong-guang-liu-xing-wang-i-like-radio2` |
| English | `播放台湾英文` | `播放台灣英文` | `https://www.radiotaiwan.tw/podcasts/taiwan-this-week` |
| Stories | `播放台湾故事` | `播放台灣故事` | `https://www.radiotaiwan.tw/podcasts/lan-ren-ma-ma-shuo-gu-shi` |
| English learning | `播放台湾英文学习` | `播放台灣英文學習` | `https://www.radiotaiwan.tw/podcasts/ting-gu-shi-xue-ying-wen` |

These explicit commands are matched after whitespace is removed. The configured Taiwan-news trigger words also route to the news category. General `播放新闻` remains Xiaomi native news and is not a Taiwan-radio command.

Radio pages are parsed by `bridge/online_audio.py`: supported radio pages expose `radio-streams-json` and `last-update`; podcast pages expose the page's current `audio_player_podcasts` episode, which is the site's current/latest episode when the page is updated. On success, the resolved audio URL is sent to MiNA directly. This path does not call the LLM or TTS. If every configured page fails, the existing voice reply path reports that the Taiwan radio is temporarily unavailable.

## Runtime modes

| Mode | Behavior |
| --- | --- |
| `wake` | Handles wake-word, conversation-window, and explicit direct-route requests. |
| `proxy` | Handles new de-duplicated MiNA records without requiring an extra wake word. |
| `silent` | Skips LLM/TTS/active replies while the poller and console may remain running. Stop polling separately when needed. |

## Reading and English-learning records

The current console and voice commands provide record management; this is not a standalone reader, pronunciation scorer, or speaker-recognition system.

Reading commands include:

```text
记录阅读 标题：我的文章，网址：https://example.com/article，章节：第1章
继续阅读上次文章
我读到《我的文章》第8页
暂停阅读《我的文章》
完成阅读《我的文章》
```

English-learning commands include:

```text
开始初级英文角色扮演，主题是机场
继续英文学习
记录单字 boarding，意思是登机
记录英文错误：I need help 应改成 Could you help me?
结束英文学习
```

Reading continuation fetches visible text from public HTTP(S) pages and commits the character cursor only after playback completes. Learning data is stored locally in `learning.sqlite3`.

## Requirements and accounts

- [Python 3.10+](https://www.python.org/downloads/).
- Install the exact packages in [requirements.txt](requirements.txt), including [`httpx`](https://pypi.org/project/httpx/), [`pycryptodome`](https://pypi.org/project/pycryptodome/), FastAPI, Uvicorn, PyYAML, Edge TTS, and MiCloud.
- A Xiaomi account at [account.xiaomi.com](https://account.xiaomi.com/) and a reachable, selected Xiaomi speaker are required for MiNA polling and direct playback. Follow [XIAOMI_LOGIN_GUIDE.md](XIAOMI_LOGIN_GUIDE.md) for `userId` and `passToken` setup.
- An OpenAI-compatible LLM is required for ordinary AI replies and learning conversations, but not for successful Taiwan-radio playback. Use the official [DeepSeek API documentation](https://api-docs.deepseek.com/) / [DeepSeek platform](https://platform.deepseek.com/) or another provider's official console.
- TTS is optional for successful direct radio playback. Volcano TTS requires an account/app and credentials from the official [Volcano Speech console](https://console.volcengine.com/speech/app); Edge TTS uses the installed [`edge-tts`](https://pypi.org/project/edge-tts/) package without a separate account. Xiaomi native TTS remains the fallback path when applicable.

Never put passwords, `passToken`, service tokens, or API keys in documentation, example files, commits, or messages.

## Install and run

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item config.yaml.example config.yaml
.\.venv\Scripts\python.exe main.py --config config.yaml
```

Linux can use `python3 -m venv .venv`, `.venv/bin/python -m pip install -r requirements.txt`, and `.venv/bin/python main.py --config config.yaml`. The console defaults to `http://127.0.0.1:8200/`; the static TTS audio server defaults to port `8201` and must be reachable by the speaker when external TTS is used.

Useful options:

```text
--config PATH       Use a specific configuration file
--console-only      Start only the console and static audio server
--port PORT         Override the console port
--verbose           Enable verbose logging
```

Use [config.yaml.example](config.yaml.example) for the nested configuration shape. The five radio lists are under `routing.taiwan_radio`; the TTS fields are under `tts` and `audio`.

## Verification

```powershell
python -m compileall -q main.py bridge console xiaomi
python -m unittest discover -s tests -p 'test_*.py'
```

See [TUTORIAL.md](TUTORIAL.md), [TTS_VOICES.md](TTS_VOICES.md), [CHANGELOG.md](CHANGELOG.md), and [VERSION.md](VERSION.md) for more detail.
