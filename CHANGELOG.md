# Changelog

## v5.5.0 — 2026-07-25

### 重构
- 零依赖运行：内嵌 customtkinter + pystray + six，无需 pip install
- 克莱因蓝 Apple 暗色主题系统（THEME 令牌集中管理）
- 22 家付费 AI 提供商，移除开源/无 API 条目

### 新增
- 💳 付费链接直达：每行 Key 旁悬停显示 URL，点击跳转浏览器
- 通义千问 Key 自动识别（sk-ws- / sk-sp- 前缀）
- README 中英文重写，精简实用

### 修复
- 通义千问 base URL 更正为 dashscope.aliyuncs.com
- 排名刷新排除无效提供商
- ORG_TO_KEY 同步清理

## v5.4.0 — 2026-07-25

### 新增
- 💳 API Key 页面每个槽位新增付费链接按钮，悬停显示目标 URL，点击跳转浏览器
- 通义千问 API Key 自动识别（sk-ws- / sk-sp- 前缀），余额以 ¥ 显示

### 优化
- 精简提供商：移除 nous、llama、openbmb（开源模型）及 meituan、xiaomi（无公开 API），从 27 家减至 22 家
- 排名刷新自动排除不在 PROVIDERS 中的免费/无效提供商
- 补齐 llama、sarvam、unisound、inception 的付费链接

### 设计
- 全面重构 UI 配色：Apple 暗色面板 + 克莱因蓝 accent
- 统一 ToolTip 提示系统，移除冗余 `bind_tooltip` 函数
- THEME 设计令牌集中管理，移除所有硬编码色值
- 优化函数参数：移除 `_fetch_generic_balance` 中未使用的 `provider` 参数

### 修复
- 通义千问 base URL 更正为 dashscope.aliyuncs.com/compatible-mode/v1
- ORG_TO_KEY 与 PROVIDERS 同步清理

## v5.3.2 — 2026-07-20

### 修复
- 防重复执行失效：原 PID 锁文件逻辑将 `WaitForSingleObject` 返回值含义写反（0 为进程已结束而非运行中），且 `OpenProcess` 权限旗标无效，导致可同时运行多个实例、出现重复浮动小视窗
- 改用 Windows 命名 Mutex：核心保证原子互斥、跨 exe 路径生效、进程崩溃自动释放，无残留锁文件

## v5.3.1 — 2026-07-20

- 首个正式版本：系统托盘 hover 弹出、迷你余额浮窗、定时抓取余额、最多 5 Key 并发查询、llm-stats 排行榜刷新、DPAPI 加密储存、27 家提供商
