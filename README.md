# AI 流量监控 (AI Traffic Monitor)

> 系统托盘常驻 · 迷你余额浮窗 · 自动定时抓取 · 27 家 AI 提供商排名

Windows 桌面工具，监控多个 AI 模型的 API 余额、配额与速率，支持 DeepSeek、Kimi 等主流平台。

---

## 功能一览

| 功能 | 说明 |
|------|------|
| 🔔 系统托盘 | 鼠标移到右下角托盘图标即弹出主视窗，离开自动隐藏 |
| 💰 迷你余额浮窗 | 右上角窄条，始终置顶；点击轮换公司，右键打开主视窗，托盘菜单开关 |
| ⏱ 自动定时抓取 | 可设定 1/5/10/15/30/60 分钟间隔，预设 10 分钟 |
| 🔄 并发余额查询 | 最多 5 个 API Key，并行抓取，单次 ~6 秒 |
| 🏆 排名更新 | 从 llm-stats.com Coding 排行榜抓取最新排名，自动更新提供商排序 |
| 🔑 加密储存 | API Key 使用 Windows DPAPI 加密，仅本机本用户可解密 |
| 🖱 悬停提示 | 所有工具栏按钮都有文字提示 |

---

## 快速开始

### 直接运行（Python 3.10+）

```powershell
pip install customtkinter pystray pillow
python ai_traffic_monitor.py
```

### 编译为 EXE

```powershell
pip install pyinstaller
pyinstaller --clean --noconfirm ai_traffic_monitor.spec
# 输出: dist\AI_v5.3.1.exe
```

---

## 操作指南

| 操作 | 方式 |
|------|------|
| 打开主视窗 | 鼠标移到托盘图标 / 右键迷你浮窗 |
| 配置 Key | ⚙ 按钮 → 粘贴 Key（自动识别提供商）→ 💾 保存 |
| 删除 Key | Key 页面 🗑 按钮 |
| 刷新余额 | 🔄 按钮 / 双击主视窗 |
| 更新排名 | Key 页面 🏆 更新排名 |
| 开关迷你浮窗 | 右键托盘 → 切换余额浮窗 |
| 轮换公司 | 点击迷你浮窗 |
| 拖拽浮窗 | 按住迷你浮窗拖动 |
| 退出程式 | 右键托盘 → 退出 |

---

## 产生的档案

与 EXE 同目录，`AI_` 前缀：

| 档案 | 类型 | 说明 |
|------|------|------|
| `AI_config.enc` | 加密 | DPAPI 加密的 API Key + 设定 |
| `AI_traffic_data.json` | 明文 | 余额 / 配额快取（不含 Key） |
| `AI_ranking_cache.json` | 明文 | 排名快取（含网站更新日期） |

锁文件：`%TEMP%\ai_traffic_monitor.lock`（防重复执行）

---

## 安全机制

- **传输**：所有 API 请求使用 HTTPS
- **储存**：API Key 经 Windows DPAPI (`CryptProtectData`) 加密，仅当前用户可解密
- **快取**：`traffic_data.json` 仅存余额，不含密钥
- **防重复**：文件锁 + 进程存活检测，防止多实例
- **无第三方依赖风险**：仅使用标准库 + customtkinter + pystray + Pillow

---

## 支持的 AI 提供商（按 Coding 排名）

| 排名 | 提供商 | API 状态 |
|------|--------|----------|
| #1 | 🤖 OpenAI / 📜 Claude / ☁️ Qwen | ⚠ 特殊 / ❌ 无 |
| #2 | 🧠 GLM 智谱 / 🍚 美团 | 🔬 待测 / ❌ 无 |
| #3 | 🌙 Kimi 月之暗面 | ✅ 余额+配额+速率 |
| #4 | 🟢 NVIDIA NIM | 🔬 待测 |
| #5 | 🐧 混元 Hunyuan (腾讯) | ⚠ HMAC 签名 |
| #6 | 🫘 豆包 / 📱 小米 | 🔬 待测 / ❌ 无 |
| #14 | 🐋 DeepSeek | ✅ 余额 (CNY) |
| #16 | 🌬️ Mistral AI | 🔬 待测 |
| #52 | 🤝 Cohere | 🔬 待测 |
| 其他 16 家 | — | ❌ 无公开 API |

---

## 技术架构

```
ai_traffic_monitor.py
├── DPAPI 加密层 (CryptProtectData)
├── 数据层 (config.enc / traffic_data.json / ranking_cache.json)
├── 网络层 (ThreadPoolExecutor 并发 fetch)
├── UI 层
│   ├── TrafficMonitor    — 主视窗 (customtkinter, 无边框)
│   ├── MiniBalance       — 迷你余额浮窗 (始终置顶)
│   ├── SettingsDialog    — Key 设定 + 排名更新
│   └── 系统托盘          — pystray (hover 检测)
└── 工具函数 (排名抓取、Key 识别、格式化)
```

---

## 版本

**v5.3.1** — 2026-07-20
