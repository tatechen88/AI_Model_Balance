# Changelog

## v5.4.0 — 2026-07-25

### 新增
- 💳 API Key 页面每个槽位新增付费链接按钮，悬停显示目标 URL，点击跳转浏览器
- 通义千问 API Key 自动识别（sk-ws- / sk-sp- 前缀），余额以 ¥ 显示

### 优化
- 精简提供商：移除 nous、llama、openbmb（开源模型）及 meituan、xiaomi（无公开 API），从 27 家减至 22 家
- 排名刷新自动排除不在 PROVIDERS 中的免费/无效提供商
- 补齐 llama、sarvam、unisound、inception 的付费链接

### 修复
- 通义千问 base URL 更正为 dashscope.aliyuncs.com/compatible-mode/v1
- ORG_TO_KEY 与 PROVIDERS 同步清理

## v5.3.2 — 2026-07-20

### 修复
- 防重复执行失效：原 PID 锁文件逻辑将 `WaitForSingleObject` 返回值含义写反（0 为进程已结束而非运行中），且 `OpenProcess` 权限旗标无效，导致可同时运行多个实例、出现重复浮动小视窗
- 改用 Windows 命名 Mutex：核心保证原子互斥、跨 exe 路径生效、进程崩溃自动释放，无残留锁文件

## v5.3.1 — 2026-07-20

- 首个正式版本：系统托盘 hover 弹出、迷你余额浮窗、定时抓取余额、最多 5 Key 并发查询、llm-stats 排行榜刷新、DPAPI 加密储存、27 家提供商
