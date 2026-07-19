# AI 模型余额监控 (AI Model Balance)

> 系统托盘常驻 · 迷你余额浮窗 · 自动定时抓取 · 27 家 AI 提供商

Windows 桌面工具，实时监控 DeepSeek、Kimi 等 AI 模型的 API 余额与配额。

---

## 功能

| 功能 | 说明 |
|------|------|
| 🔔 系统托盘 | 鼠标移到右下角即弹出主视窗，离开自动隐藏 |
| 💰 迷你余额浮窗 | 右上角窄条，始终置顶；点击轮换公司，右键开主视窗，托盘菜单开关 |
| ⏱ 自动定时抓取 | 可设定 1/5/10/15/30/60 分钟间隔，预设 10 分钟 |
| 🔄 并发余额查询 | 最多 5 个 API Key，并行抓取 |
| 🏆 排名更新 | 从 llm-stats.com Coding 排行榜抓取最新排名 |
| 🔑 加密储存 | API Key 使用 Windows DPAPI 加密，仅本机本用户可解密 |
| 🖱 悬停提示 | 所有工具栏按钮都有文字提示 |

---

## 快速开始

### 直接运行（Python 3.10+）

```powershell
pip install customtkinter pystray pillow
python ai_model_monitor.py
```

### 编译为 EXE

```powershell
pip install pyinstaller
pyinstaller --clean --noconfirm ai_model_monitor.spec
# 输出: dist\Ai_MB.exe
```

---

## 操作指南

| 操作 | 方式 |
|------|------|
| 打开主视窗 | 鼠标移到托盘图标 / 右键迷你浮窗 |
| 配置 Key | ⚙ → 粘贴 Key（自动识别）→ 💾 保存 |
| 删除 Key | Key 页面 🗑 按钮 |
| 刷新余额 | 🔄 按钮 / 双击主视窗 |
| 更新排名 | Key 页面 🏆 更新排名 |
| 开关迷你浮窗 | 右键托盘 → 切换余额浮窗 |
| 轮换公司 | 点击迷你浮窗 |
| 退出 | 右键托盘 → 退出 |

---

## 产生的档案

与 EXE 同目录：

| 档案 | 说明 |
|------|------|
| `AI_config.enc` | DPAPI 加密的 API Key + 设定 |
| `AI_model_data.json` | 余额 / 配额快取（不含密钥） |
| `AI_ranking_cache.json` | 排名快取（含网站更新日期） |

防重复执行：Windows 命名 Mutex（无锁文件，跨路径生效，崩溃自动释放）

---

## 安全

- 所有 API 请求 HTTPS 加密传输
- API Key 经 Windows DPAPI 加密储存，仅当前用户可解密
- 余额快取不含密钥
- Windows 命名 Mutex 防止多实例，进程异常退出时自动释放

---

## 支持的提供商（按 Coding 排名）

| 提供商 | 状态 |
|--------|------|
| 🐋 DeepSeek | ✅ 余额 (CNY) |
| 🌙 Kimi | ✅ 余额 + 配额 + 速率 |
| 🧠 GLM 智谱 | 🔬 待测 |
| 🟢 NVIDIA NIM | 🔬 待测 |
| 🫘 豆包 Doubao | 🔬 待测 |
| 🌬️ Mistral AI | 🔬 待测 |
| 🤝 Cohere | 🔬 待测 |
| 🤖 OpenAI | ⚠ 需 Session Key |
| 🐧 混元 Hunyuan | ⚠ 需 HMAC 签名 |
| ♊ Gemini | ⚠ 需 Google Cloud |
| 📜 Claude / ☁️ Qwen / 🍚 美团 等 16 家 | 📋 仅本地追踪 |

---

## 版本

**v5.3.2** — 2026-07-20
