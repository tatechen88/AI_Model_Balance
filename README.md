# AI 模型余额监控

> 托盘常驻 · 迷你浮窗 · 自动查询 · 22 家付费 AI 提供商

一个 Windows 桌面小工具，帮你随时看一眼 DeepSeek、Kimi、通义千问等 AI 平台的 API 余额还剩多少。

---

## 下载

Windows 用户直接下载 EXE，无需安装任何东西：

> [📥 Ai_MB_v5.5.0_Windows.zip](https://github.com/tatechen88/AI_Model_Balance/releases/download/v5.5.0/Ai_MB_v5.5.0_Windows.zip)（20MB）

解压后双击 `Ai_MB_v5.5.0.exe` 即可运行。右下角会出现托盘图标。

---

## 怎么用

下载上面的 ZIP，解压，双击 `Ai_MB_v5.5.0.exe`。右下角托盘出现图标，鼠标移上去弹出主窗口，移开自动隐藏。

**配置 API Key**

点击 ⚙ 打开设置页，粘贴 Key 会自动识别是哪家的。每行右侧的 💳 按钮可以直接跳到该平台的付费页面。保存后余额会自动查询。

**打包成 EXE**

```powershell
pip install pyinstaller
pyinstaller --clean --noconfirm ai_model_monitor.spec
```

---

## 主要能力

- **系统托盘常驻** — 鼠标滑入托盘区弹出，滑出自闭，不占屏幕
- **迷你余额浮窗** — 右上角窄条始终置顶，点击轮换显示不同平台的余额
- **定时自动查询** — 1~60 分钟可选，默认 10 分钟刷新一次
- **并发抓取** — 最多 5 个 Key 同时查，各平台互不等待
- **Key 自动识别** — 粘贴即知是哪家，支持 OpenAI / DeepSeek / Kimi / 通义千问等前缀匹配
- **付费链接直达** — 每行 💳 悬停显示付费页 URL，点击浏览器打开
- **排名同步** — 一键从 llm-stats.com 拉取最新 Coding 排行榜
- **加密储存** — Key 用 Windows DPAPI 加密，仅当前用户可解密，换机换用户无效
- **防重复启动** — Windows 命名 Mutex，不留锁文件，崩溃自动释放

---

## 支持查询余额的平台

| 平台 | 状态 |
|---|---|
| 🐋 DeepSeek | ✅ 自动查余额 (CNY) |
| 🌙 Kimi | ✅ 余额 + Token 配额 + 速率 |
| ☁️ 通义千问 | ✅ 按量付费 ¥ / Token Plan |
| 🧠 智谱 GLM | 🔬 待 Key 实测 |
| 🟢 NVIDIA NIM | 🔬 待 Key 实测 |
| 🫘 豆包 | 🔬 待 Key 实测 |
| 🌬️ Mistral | 🔬 待 Key 实测 |
| 🤝 Cohere | 🔬 待 Key 实测 |
| 🤖 OpenAI | ⚠ 需 Session Key |
| 🐧 混元 | ⚠ 需 HMAC 签名 |

其余 Claude、Gemini、Grok、MiniMax、Azure 等 12 家可手动追踪余额。

---

## 数据在哪

所有文件与 EXE 同目录：

| 文件 | 内容 |
|---|---|
| `AI_config.enc` | 加密的 Key + 设置（DPAPI） |
| `AI_model_data.json` | 余额快取（不含 Key） |
| `AI_ranking_cache.json` | 排行榜快取 |

---

## 安全

- API 请求全部 HTTPS
- Key 经 Windows 系统级 DPAPI 加密，只有你的账号能解
- 余额缓存文件不含密钥
- 命名 Mutex 防多开，崩了不残留

---

## 版本

**v5.5.0** — 2026-07-25
