# -*- coding: utf-8 -*-
"""AI 流量监控 — 系统托盘 + 迷你余额浮窗"""

import json, os, re, sys, threading, time, urllib.request, urllib.error, tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import customtkinter as ctk
from PIL import Image, ImageDraw
import pystray
import ctypes
from ctypes import wintypes

APP_NAME = "AI 模型余额"
APP_VERSION = "v5.3.1"
MAX_SLOTS = 5
FETCH_INTERVAL_MIN = 10  # 预设每10分钟自动抓取

# ═══════════ Windows DPAPI 加密 ═══════════

class DATA_BLOB(ctypes.Structure):
    _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_ubyte))]

def _dpapi_encrypt(plaintext: str) -> bytes:
    """使用 Windows DPAPI 加密 (仅当前用户可解密)"""
    crypt32 = ctypes.windll.crypt32
    data_in = plaintext.encode("utf-16le")
    blob_in = DATA_BLOB(len(data_in), ctypes.cast(data_in, ctypes.POINTER(ctypes.c_ubyte)))
    blob_out = DATA_BLOB()
    flags = 0x01  # CRYPTPROTECT_UI_FORBIDDEN (仅当前用户可解密)
    if crypt32.CryptProtectData(ctypes.byref(blob_in), "AI-Model-Balance", None, None, None, flags, ctypes.byref(blob_out)):
        result = ctypes.string_at(blob_out.pbData, blob_out.cbData)
        ctypes.windll.kernel32.LocalFree(blob_out.pbData)
        return result
    raise OSError("DPAPI encrypt failed")

def _dpapi_decrypt(ciphertext: bytes) -> str:
    """使用 Windows DPAPI 解密"""
    crypt32 = ctypes.windll.crypt32
    blob_in = DATA_BLOB(len(ciphertext), ctypes.cast(ciphertext, ctypes.POINTER(ctypes.c_ubyte)))
    blob_out = DATA_BLOB()
    flags = 0x01
    if crypt32.CryptUnprotectData(ctypes.byref(blob_in), None, None, None, None, flags, ctypes.byref(blob_out)):
        result = ctypes.string_at(blob_out.pbData, blob_out.cbData)
        ctypes.windll.kernel32.LocalFree(blob_out.pbData)
        return result.decode("utf-16le")
    raise OSError("DPAPI decrypt failed")

if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).parent

# 加密配置文件存放于程式同目录
CONFIG_FILE = BASE_DIR / "AI_config.enc"
MODEL_DATA_FILE = BASE_DIR / "AI_model_data.json"
LOCK_FILE = Path(tempfile.gettempdir()) / "ai_model_monitor.lock"
RANKING_FILE = BASE_DIR / "AI_ranking_cache.json"
RANKING_URL = "https://llm-stats.com/"

SLOT_COLORS = ["#4F46E5", "#7C3AED", "#10B981", "#F59E0B", "#EC4899"]
SLOT_ICONS  = ["🖥", "🌙", "💎", "⚡", "🔥"]

# ═══════════ 30 家 AI 模型提供商 ═══════════
PROVIDERS = {
    # llm-stats.com CODE leaderboard rank  ✅=已验证 🔬=端点存在 ⚠=特殊认证 ❌=无API
    "openai":   {"rank":1,  "label":"🤖 OpenAI",             "api_ok":"special", "balance_url":"https://api.openai.com/v1/usage",                    "note":"⚠ 需 Session Key"},
    "claude":   {"rank":1,  "label":"📜 Claude (Anthropic)", "api_ok":False,                                                                    "note":"❌ 无公开余额 API"},
    "qwen":     {"rank":1,  "label":"☁️ 通义千问 Qwen",       "api_ok":False,                                                                    "note":"❌ DashScope 无余额端点"},
    "glm":      {"rank":2,  "label":"🧠 智谱 GLM",           "api_ok":"pending","balance_url":"https://open.bigmodel.cn/api/paas/v4/user/info", "note":"🔬 待 Key 实测"},
    "meituan":  {"rank":2,  "label":"🍚 美团 Meituan",       "api_ok":False,                                                                    "note":"❌ 无公开 API"},
    "kimi":     {"rank":3,  "label":"🌙 Kimi 月之暗面",      "api_ok":True,    "balance_url":"https://api.moonshot.cn/v1/users/me/balance",    "note":"✅ 余额+配额+速率", "extra_url":"https://api.moonshot.cn/v1/users/me"},
    "nvidia":   {"rank":4,  "label":"🟢 NVIDIA NIM",         "api_ok":"pending","balance_url":"https://api.nvcf.nvidia.com/v2/nvcf/users/me",   "note":"🔬 待 Key 实测"},
    "hunyuan":  {"rank":5,  "label":"🐧 混元 Hunyuan",       "api_ok":"special","balance_url":"https://hunyuan.tencentcloudapi.com/",             "note":"⚠ 需 HMAC 签名"},
    "doubao":   {"rank":6,  "label":"🫘 豆包 Doubao",        "api_ok":"pending","balance_url":"https://ark.cn-beijing.volces.com/api/v3/users/me","note":"🔬 待 Key 实测"},
    "xiaomi":   {"rank":6,  "label":"📱 小米 Xiaomi",        "api_ok":False,                                                                    "note":"❌ 无公开 LLM API"},
    "nous":     {"rank":7,  "label":"🧪 Nous Research",      "api_ok":False,                                                                    "note":"🖥 开源模型"},
    "grok":     {"rank":8,  "label":"🪐 Grok (xAI)",         "api_ok":False,                                                                    "note":"❌ 无余额端点"},
    "minimax":  {"rank":8,  "label":"📐 MiniMax",            "api_ok":False,                                                                    "note":"❌ 无余额端点"},
    "amazon":   {"rank":8,  "label":"🪨 Amazon Bedrock",     "api_ok":False,                                                                    "note":"⚠ 需 AWS Console"},
    "llama":    {"rank":13, "label":"🦙 Llama (Meta)",       "api_ok":False,                                                                    "note":"🖥 开源模型"},
    "deepseek": {"rank":14, "label":"🐋 DeepSeek",           "api_ok":True,    "balance_url":"https://api.deepseek.com/user/balance",            "note":"✅ 余额 (CNY)"},
    "mistral":  {"rank":16, "label":"🌬️ Mistral AI",        "api_ok":"pending","balance_url":"https://api.mistral.ai/v1/users/me",               "note":"🔬 待 Key 实测"},
    "microsoft":{"rank":17, "label":"🪟 Microsoft Azure",    "api_ok":False,                                                                    "note":"⚠ 需 Entra ID"},
    "gemini":   {"rank":18, "label":"♊ Gemini (Google)",    "api_ok":"special",                                                                  "note":"⚠ 无余额端点"},
    "ibm":      {"rank":20, "label":"🔵 IBM watsonx",        "api_ok":False,                                                                    "note":"❌ 端点不可达"},
    "sarvam":   {"rank":28, "label":"🇮🇳 Sarvam AI",         "api_ok":False,                                                                    "note":"❌ 无公开端点"},
    "ai21":     {"rank":29, "label":"2️⃣1️⃣ AI21 Labs",       "api_ok":False,                                                                    "note":"❌ 无余额端点"},
    "stepfun":  {"rank":38, "label":"👣 阶跃星辰 StepFun",   "api_ok":False,                                                                    "note":"❌ 无余额端点"},
    "cohere":   {"rank":52, "label":"🤝 Cohere",             "api_ok":"pending","balance_url":"https://api.cohere.ai/v1/users/me",               "note":"🔬 待 Key 实测"},
    "unisound": {"rank":57, "label":"🎤 云知声 Unisound",    "api_ok":False,                                                                    "note":"❌ 无公开 API"},
    "openbmb":  {"rank":58, "label":"🔬 OpenBMB",            "api_ok":False,                                                                    "note":"🖥 开源模型"},
    "inception": {"rank":88,"label":"🌌 Inception AI (Jais)","api_ok":False,                                                                    "note":"❌ 无公开端点"},
}
# ═══════════ 排名快取与线上查询 ═══════════

def load_ranking_cache():
    """载入本地排名快取，回传 (ranks_dict, updated_at_str, source_str)"""
    if RANKING_FILE.exists():
        try:
            data = json.loads(RANKING_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict) and "ranks" in data:
                return data.get("ranks", {}), data.get("updated_at", ""), data.get("source", ""), data.get("site_updated", "")
            # 旧格式兼容
            return data, "", "", ""
        except:
            pass
    return {}, "", "", ""

def get_ranking_meta():
    """取得排名快取的后设资料"""
    _, updated, source, site_updated = load_ranking_cache()
    return updated, source, site_updated

def save_ranking_cache(ranks: dict, site_updated: str = ""):
    """储存排名快取 (provider_key → rank)"""
    data = {"ranks": ranks,
            "updated_at": f"{time.localtime().tm_year}年{time.localtime().tm_mon}月{time.localtime().tm_mday}日 {time.strftime("%H:%M:%S")}",
            "site_updated": site_updated,
            "source": "llm-stats.com/leaderboards/best-ai-for-coding"}
    RANKING_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def apply_rankings(ranks: dict):
    """将排名套用到 PROVIDERS"""
    for key, rank in ranks.items():
        if key in PROVIDERS:
            PROVIDERS[key]["rank"] = rank

def fetch_rankings_from_web():
    """从 llm-stats.com 抓取最新 CODE 类别排名
    回传 ({provider_key: rank}, site_date_str) 或 (None, None)
    """
    try:
        req = urllib.request.Request(RANKING_URL)
        req.add_header("User-Agent", "AI-Model-Balance/5.3")
        resp = urllib.request.urlopen(req, timeout=10)
        html = resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"[RANKING] fetch failed: {e}", file=sys.stderr)
        return None, None

    # 找 CODE 类别资料
    pos = html.find('category_id\\":\\"code\\"')
    if pos < 0:
        return None
    chunk = html[pos:pos+100000]

    # 解析每个组织的最高排名
    org_ranks = {}
    for m in re.finditer(r'\\"organization_name\\":\\"([^"\\]+)\\"', chunk):
        org = m.group(1)
        ahead = chunk[m.end():m.end()+300]
        rank_m = re.search(r'\\"rank\\":(\d+)', ahead)
        if rank_m:
            rank = int(rank_m.group(1))
            if org not in org_ranks or rank < org_ranks[org]:
                org_ranks[org] = rank

    # 映射到 provider key
    ORG_TO_KEY = {
        "OpenAI": "openai", "Anthropic": "claude",
        "Alibaba Cloud / Qwen Team": "qwen", "Zhipu AI": "glm",
        "Meituan": "meituan", "Moonshot AI": "kimi",
        "NVIDIA": "nvidia", "Tencent": "hunyuan",
        "ByteDance": "doubao", "Xiaomi": "xiaomi",
        "Nous Research": "nous", "xAI": "grok",
        "MiniMax": "minimax", "Amazon": "amazon",
        "Meta": "llama", "DeepSeek": "deepseek",
        "Mistral AI": "mistral", "Microsoft": "microsoft",
        "Google": "gemini", "IBM": "ibm",
        "Sarvam AI": "sarvam", "AI21 Labs": "ai21",
        "StepFun": "stepfun", "Cohere": "cohere",
        "Unisound": "unisound", "OpenBMB": "openbmb",
        "Inception": "inception",
        "Baidu": "ernie",
        "LG AI Research": "lg",
    }
    result = {}
    for org_name, rank in org_ranks.items():
        key = ORG_TO_KEY.get(org_name)
        if key:
            result[key] = rank
    # 提取网站资料更新日期
    site_date = ""
    sdm = re.search(r'"dateModified":"([^"]+)"', html)
    if sdm:
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(sdm.group(1).replace("Z", "+00:00"))
            site_date = f"{dt.year}年{dt.month}月{dt.day}日"
        except:
            site_date = sdm.group(1)[:10]
    return (result if result else None), site_date

DEFAULT_SLOT = {"key": "", "provider": ""}
DEFAULT_DATA = {"balance": "—", "extra": {}}

# ═══════════ 防重复执行 ═══════════

def acquire_lock():
    """尝试获取进程锁，防止重复执行"""
    try:
        if LOCK_FILE.exists():
            try:
                pid = int(LOCK_FILE.read_text().strip())
                kernel32 = ctypes.windll.kernel32
                # SYNCHRONIZE | PROCESS_QUERY_LIMITED_INFORMATION
                handle = kernel32.OpenProcess(0x100000 | 0x00100000, False, pid)
                if handle:
                    # WaitForSingleObject with 0 timeout: returns 0 if alive, 0x102 if dead
                    ret = kernel32.WaitForSingleObject(handle, 0)
                    kernel32.CloseHandle(handle)
                    if ret == 0:
                        return False  # 进程仍在运行
            except:
                pass
            # 锁文件存在但进程已死，删除旧锁
            try: LOCK_FILE.unlink()
            except: pass
        LOCK_FILE.write_text(str(os.getpid()))
        return True
    except:
        return True

def release_lock():
    try:
        if LOCK_FILE.exists():
            LOCK_FILE.unlink()
    except:
        pass

# ═══════════ 数据 ═══════════

def load_config():
    if CONFIG_FILE.exists():
        try:
            raw = _dpapi_decrypt(CONFIG_FILE.read_bytes())
            cfg = json.loads(raw)
            slots = cfg.get("slots", [])
            while len(slots) < MAX_SLOTS: slots.append(dict(DEFAULT_SLOT))
            return {"slots": slots[:MAX_SLOTS], "fetch_interval_min": cfg.get("fetch_interval_min", FETCH_INTERVAL_MIN)}
        except:
            # 解密失败（换用户/损坏），删除旧文件重新开始
            try: CONFIG_FILE.unlink()
            except: pass
    return {"slots": [dict(DEFAULT_SLOT) for _ in range(MAX_SLOTS)], "fetch_interval_min": FETCH_INTERVAL_MIN}

def save_config(cfg):
    try:
        plain = json.dumps(cfg, ensure_ascii=False, indent=2)
        CONFIG_FILE.write_bytes(_dpapi_encrypt(plain))
    except Exception as e:
        print(f"[ERROR] save_config failed: {e}", file=sys.stderr)

def load_model_data():
    if MODEL_DATA_FILE.exists():
        try:
            data = json.loads(MODEL_DATA_FILE.read_text(encoding="utf-8"))
            slots = data.get("slots", [])
            while len(slots) < MAX_SLOTS: slots.append(dict(DEFAULT_DATA))
            return {"slots": slots[:MAX_SLOTS]}
        except: pass
    data = {"slots": [dict(DEFAULT_DATA) for _ in range(MAX_SLOTS)]}
    save_model_data(data)
    return data

def save_model_data(data):
    MODEL_DATA_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def detect_provider(key):
    k = key.strip()
    if not k: return ""
    if k.startswith("sk-proj-") or k.startswith("sk-svcacct-"): return "openai"
    if k.startswith("sk-ant-"): return "claude"
    if k.startswith("sk-"): return "deepseek" if re.match(r'^sk-[0-9a-f]{32,}$', k) else "kimi"
    if k.startswith("AIza"): return "gemini"
    if k.startswith("gsk_"): return "groq"
    return ""
def fetch_provider_data(provider, api_key):
    """查询提供商数据"""
    if provider == "deepseek":
        return _fetch_deepseek(api_key)
    if provider == "kimi":
        return _fetch_kimi(api_key)
    # Providers with known balance endpoints but not yet implemented
    pinfo = PROVIDERS.get(provider, {})
    if pinfo.get("balance_url"):
        return _fetch_generic_balance(provider, api_key, pinfo)
    return {"balance": None, "extra": {}}

def _fetch_generic_balance(provider, api_key, pinfo):
    url = pinfo.get("balance_url", "")
    if not url:
        return {"balance": None, "extra": {}}
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {api_key}")
    try:
        resp = urllib.request.urlopen(req, timeout=6)
        data = json.loads(resp.read())
        if "data" in data and isinstance(data["data"], dict):
            data = data["data"]
        for field in ["total_balance", "balance", "available_balance", "credit", "credits", "quota"]:
            val = data.get(field) if isinstance(data, dict) else None
            if val is not None:
                try: return {"balance": f"¥{float(val):.2f}", "extra": {}}
                except: return {"balance": str(val), "extra": {}}
    except:
        pass
    return {"balance": None, "extra": {}}

def _fetch_deepseek(key):
    req = urllib.request.Request("https://api.deepseek.com/user/balance")
    req.add_header("Authorization", f"Bearer {key}")
    try:
        resp = urllib.request.urlopen(req, timeout=6)
        data = json.loads(resp.read())
        for info in data.get("balance_infos", []):
            if info.get("currency") == "CNY":
                return {"balance": f"¥{float(info['total_balance']):.2f}", "extra": {}}
    except: pass
    return {"balance": None, "extra": {}}

def _fetch_kimi(key):
    result = {"balance": None, "extra": {}}
    def _get_balance():
        req = urllib.request.Request("https://api.moonshot.cn/v1/users/me/balance")
        req.add_header("Authorization", f"Bearer {key}")
        try:
            resp = urllib.request.urlopen(req, timeout=5)
            data = json.loads(resp.read())
            bal = data.get("data", {}).get("available_balance")
            if bal is not None: result["balance"] = f"¥{float(bal):.2f}"
        except: pass
    def _get_quota():
        req = urllib.request.Request("https://api.moonshot.cn/v1/users/me")
        req.add_header("Authorization", f"Bearer {key}")
        try:
            resp = urllib.request.urlopen(req, timeout=5)
            data = json.loads(resp.read())
            org = data.get("data", {}).get("organization", {})
            result["extra"] = {
                "token_quota": org.get("max_token_quota", 0),
                "max_rpm": org.get("max_request_per_minute", 0),
                "max_tpm": org.get("max_token_per_minute", 0),
                "max_concurrency": org.get("max_concurrency", 0),
            }
        except: pass
    # 并行请求两个端点
    t1 = threading.Thread(target=_get_balance); t1.start()
    t2 = threading.Thread(target=_get_quota); t2.start()
    t1.join(timeout=6); t2.join(timeout=6)
    return result

def fmt_big(n):
    if n >= 1_000_000: return f"{n/1_000_000:.1f}M"
    if n >= 1_000: return f"{n/1_000:.1f}K"
    return str(n)

def get_model_rows(provider, data, pinfo=None):
    api_ok = pinfo.get("api_ok", False) if pinfo else False
    extra = data.get("extra", {})
    balance = data.get("balance", "—")
    rows = []

    # 根据提供商 API 状态决定余额显示
    if api_ok == True:
        rows.append(("💰 余额", str(balance), "#F59E0B"))
        if provider == "kimi":
            if extra.get("token_quota"): rows.append(("🔤 Token 配额", fmt_big(extra["token_quota"]), "#A78BFA"))
            if extra.get("max_rpm"): rows.append(("📊 请求速率", f"{extra['max_rpm']}/min", "#34D399"))
            if extra.get("max_tpm"): rows.append(("⚡ Token 速率", fmt_big(extra["max_tpm"]), "#FBBF24"))
            if extra.get("max_concurrency"): rows.append(("🔗 最大并发", str(extra["max_concurrency"]), "#F472B6"))
    elif api_ok == "special":
        rows.append(("💰 余额", "需浏览器查询", "#F59E0B"))
    elif api_ok == "pending":
        rows.append(("💰 余额", "🔬 待 Key 实测", "#FBBF24"))
    else:
        rows.append(("💰 余额", "仅本地追踪", "#6B7280"))

    return rows

def create_tray_image():
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([4, 4, 60, 60], fill=(15, 15, 35, 255))
    draw.ellipse([10, 10, 54, 54], fill=(22, 22, 50, 255))
    draw.line([(16, 44), (28, 32), (40, 28), (48, 20)], fill=(79, 70, 229, 220), width=3)
    draw.line([(48, 20), (40, 28), (28, 36), (16, 44)], fill=(124, 58, 237, 220), width=3)
    draw.ellipse([27, 30, 37, 40], fill=(200, 200, 240, 200))
    return img

# ═══════════ UI ═══════════

class SettingsDialog(ctk.CTkToplevel):
    def __init__(self, parent, config, on_save):
        super().__init__(parent)
        self.title("🔑 API Key 配置")
        self.geometry("620x560")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.configure(fg_color="#16162A")
        self.config = config
        self.on_save = on_save
        self.entries = []
        self.warn_labels = {}

        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"620x560+{(sw-620)//2}+{(sh-560)//2}")

        ctk.CTkLabel(self, text="🔑 API Key 配置（最多 5 个槽位）",
                     font=ctk.CTkFont(family="Microsoft YaHei UI", size=17, weight="bold"),
                     text_color="#E0E0F0").pack(pady=(14, 6))
        ctk.CTkLabel(self, text="粘贴 Key 自动识别  |  27 家提供商按 Coding 排名",
                     font=("Microsoft YaHei UI", 13), text_color="#8B8BA0").pack()

        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=14, pady=(8, 2))
        for txt, w in [("#", 30), ("API Key", 310), ("提供商", 170), ("", 30)]:
            ctk.CTkLabel(hdr, text=txt, width=w, font=("Microsoft YaHei UI", 13),
                         text_color="#8B8BA0").pack(side="left", padx=(0 if txt == "#" else 4, 0))

        slots = self.config.get("slots", [])
        for i in range(MAX_SLOTS):
            s = slots[i] if i < len(slots) else dict(DEFAULT_SLOT)
            self._row(i, s.get("key", ""), s.get("provider", ""))

        # 自动抓取间隔
        intv_frame = ctk.CTkFrame(self, fg_color="#1E1E2E", corner_radius=6)
        intv_frame.pack(fill="x", padx=10, pady=(10, 0))
        ctk.CTkLabel(intv_frame, text="⏱ 抓取 API Key 余额时间间隔", font=("Microsoft YaHei UI", 13),
                     text_color="#E0E0F0").pack(side="left", padx=10, pady=8)
        self.interval_var = ctk.StringVar(value=str(self.config.get("fetch_interval_min", FETCH_INTERVAL_MIN)))
        intv_menu = ctk.CTkOptionMenu(intv_frame, values=["1", "5", "10", "15", "30", "60"],
                                      variable=self.interval_var, width=70,
                                      fg_color="#0F0F23", button_color="#4F46E5",
                                      font=("Microsoft YaHei UI", 13))
        intv_menu.pack(side="right", padx=10, pady=6)
        ctk.CTkLabel(intv_frame, text="分钟", font=("Microsoft YaHei UI", 13),
                     text_color="#8B8BA0").pack(side="right", padx=(0, 4), pady=8)

        btn = ctk.CTkFrame(self, fg_color="transparent")
        btn.pack(pady=(10, 0))
        ctk.CTkButton(btn, text="取消", width=85, height=30, font=("Microsoft YaHei UI", 13),
                      fg_color="#374151", hover_color="#4B5563", command=self.destroy).pack(side="left", padx=4)
        ctk.CTkButton(btn, text="💾 保存", width=85, height=30, font=("Microsoft YaHei UI", 13),
                      fg_color="#4F46E5", hover_color="#6366F1", command=self._save).pack(side="left", padx=4)
        ctk.CTkButton(btn, text="🏆 更新排名", width=95, height=30, font=("Microsoft YaHei UI", 13),
                      fg_color="#F59E0B", hover_color="#FBBF24", text_color="#0F0F23",
                      command=self._refresh_from_settings).pack(side="left", padx=4)

        # 排名来源资讯
        updated, source, site_updated = get_ranking_meta()
        meta_frame = ctk.CTkFrame(self, fg_color="transparent")
        meta_frame.pack(pady=(8, 4))
        # 排名更新状态（供 _refresh_from_settings 使用）
        self._rank_status = ctk.CTkLabel(meta_frame, text="",
                         font=("Microsoft YaHei UI", 12), text_color="#6B7280")
        self._rank_status.pack()
        if updated and site_updated:
            ctk.CTkLabel(meta_frame, text=f"🌐 网站更新: {site_updated}",
                         font=("Microsoft YaHei UI", 12), text_color="#8B8BA0").pack()
        if updated:
            ctk.CTkLabel(meta_frame, text=f"🔗 来源: {source}",
                         font=("Microsoft YaHei UI", 12), text_color="#A0A0C0",
                         wraplength=580).pack()
        else:
            ctk.CTkLabel(meta_frame, text="🔗 来源: llm-stats.com/leaderboards/best-ai-for-coding",
                         font=("Microsoft YaHei UI", 12), text_color="#A0A0C0",
                         wraplength=580).pack()

    def _row(self, idx, key, provider):
        row = ctk.CTkFrame(self, fg_color="#1E1E2E", corner_radius=6, height=42)
        row.pack(fill="x", padx=10, pady=3)
        row.pack_propagate(False)
        color = SLOT_COLORS[idx]
        ctk.CTkLabel(row, text=str(idx+1), width=30,
                     font=("Cascadia Code", 14, "bold"), text_color=color).pack(side="left", padx=(10, 6))
        ke = ctk.CTkEntry(row, width=310, show="•", font=("Cascadia Code", 12),
                          fg_color="#0F0F23", border_width=1, border_color="#2A2A4A",
                          height=30)
        ke.pack(side="left", padx=3, pady=5); ke.insert(0, key)
        pv = ctk.StringVar(value=PROVIDERS.get(provider, {}).get("label", provider) if provider else "")
        # 提供商列表：按模型能力排名排序，显示中英文标签
        prov_keys_sorted = sorted(PROVIDERS.keys(), key=lambda k: PROVIDERS[k].get("rank", 99))
        prov_labels = [PROVIDERS[k]["label"] for k in prov_keys_sorted]
        pm = ctk.CTkOptionMenu(row, width=170, values=[""]+prov_labels,
                               fg_color="#0F0F23", button_color="#4F46E5",
                               text_color="#E0E0F0",
                               variable=pv, font=("Microsoft YaHei UI", 13),
                               button_hover_color="#6366F1",
                               corner_radius=6)
        pm.pack(side="left", padx=3, pady=5)
        del_btn = ctk.CTkButton(row, text="🗑", width=30, height=30,
                                fg_color="transparent", hover_color="#EF4444",
                                font=("Segoe UI", 14), text_color="#8B8BA0",
                                command=lambda i=idx: self._clear_row(i))
        del_btn.pack(side="right", padx=(4, 6), pady=5)
        def on_key_change(*args, i=idx, k=ke, pvar=pv):
            detected = detect_provider(k.get().strip())
            if detected:
                pvar.set(PROVIDERS[detected]["label"])
            if i in self.warn_labels:
                self.warn_labels[i].destroy(); del self.warn_labels[i]
        ke.bind("<KeyRelease>", on_key_change)
        self.entries.append({"key": ke, "provider": pv})

    def _clear_row(self, idx):
        self.entries[idx]["key"].delete(0, "end")
        self.entries[idx]["provider"].set("")
        if idx in self.warn_labels:
            self.warn_labels[idx].destroy()
            del self.warn_labels[idx]

    def _save(self):
        slots = [{"key": e["key"].get().strip(),
                  "provider": e["provider"].get().strip()} for e in self.entries]
        # 将提供商标签转回 key
        for s in slots:
            lbl = s["provider"]
            for pk, pv in PROVIDERS.items():
                if pv.get("label") == lbl:
                    s["provider"] = pk
                    break
        self.config["slots"] = slots
        self.config["fetch_interval_min"] = int(self.interval_var.get())
        save_config(self.config)
        self.on_save()
        self.destroy()

    def _refresh_from_settings(self):
        # 先保存当前设定
        slots = [{"key": e["key"].get().strip(),
                  "provider": e["provider"].get().strip()} for e in self.entries]
        for s in slots:
            lbl = s["provider"]
            for pk, pv in PROVIDERS.items():
                if pv.get("label") == lbl:
                    s["provider"] = pk
                    break
        self.config["slots"] = slots
        self.config["fetch_interval_min"] = int(self.interval_var.get())
        save_config(self.config)

        # 在设定页显示进度
        self._rank_status.configure(text="🏆 正在从 llm-stats.com 抓取排名...", text_color="#F59E0B")
        self._rank_progress = ctk.CTkProgressBar(self, fg_color="#1E1E2E",
                                                   progress_color="#F59E0B", height=4, corner_radius=2)
        self._rank_progress.pack(fill="x", padx=10, pady=(4, 0))
        self._rank_progress.start()
        self.update_idletasks()

        def _done(count, updated):
            self._rank_progress.stop()
            self._rank_progress.pack_forget()
            if count > 0:
                _, __, site_updated = get_ranking_meta()
                site_info = f"  |  🌐 网站更新: {site_updated}" if site_updated else ""
                self._rank_status.configure(
                    text=f"✅ 排名更新完成 ({count} 家) @ {updated}{site_info}", text_color="#22C55E")
            elif count == 0:
                self._rank_status.configure(text="❌ 排名抓取失败，请检查网络", text_color="#EF4444")
            else:
                self._rank_status.configure(text=f"❌ 排名更新出错: {updated}", text_color="#EF4444")
            self.master._on_config_saved()

        self.master._refresh_rankings(on_done=_done)

# ═══════════ 主窗口 ═══════════


# ═══════════ 超小型余额浮窗 ═══════════

class MiniBalance(ctk.CTkToplevel):
    """始终置顶的迷你余额视窗"""
    def __init__(self, parent):
        super().__init__(parent)
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(fg_color="#16162A")
        self.resizable(False, False)
        self._drag_x = self._drag_y = 0

        self.label = ctk.CTkLabel(self, text="💰 —",
                                  font=ctk.CTkFont(family="Microsoft YaHei UI", size=14, weight="bold"),
                                  text_color="#F59E0B")
        self.label.pack(padx=12, pady=4)
        self._click_cb = None  # 点击回呼
        self._was_drag = False

        # 拖拽 + 点击轮换 (只绑 label，避免双击)
        self.label.bind("<Button-1>", self._on_press)
        self.label.bind("<B1-Motion>", self._do_drag)
        self.label.bind("<ButtonRelease-1>", self._on_release)
        self.label.bind("<Button-3>", self._on_right)

    def _on_press(self, e):
        self._drag_x, self._drag_y = e.x, e.y
        self._was_drag = False

    def _on_release(self, e):
        if not self._was_drag and self._click_cb:
            self._click_cb()

    def _do_drag(self, e):
        self._was_drag = True
        self.geometry(f"+{self.winfo_x()+e.x-self._drag_x}+{self.winfo_y()+e.y-self._drag_y}")

    def set_show_cb(self, cb):
        self._show_cb = cb

    def _on_right(self, e):
        if self._show_cb:
            self._show_cb()

    def update_balances(self, config, traffic, current_slot=None):
        ts = traffic.get("slots", [])
        if current_slot is not None and current_slot < len(ts):
            data = ts[current_slot]
            bal = data.get("balance", "—")
            text = f"💰 {bal}" if bal != "—" else "💰 —"
        else:
            text = "💰 —"
        self.label.configure(text=text)
        self.update_idletasks()
        # 自适应宽度
        w = self.label.winfo_reqwidth() + 24
        self.geometry(f"{max(w, 110)}x32")


def bind_tooltip(widget, text):
    tip = [None]
    def _enter(e):
        if tip[0]: return
        tip[0] = ctk.CTkToplevel(widget)
        tip[0].overrideredirect(True)
        tip[0].attributes("-topmost", True)
        tip[0].configure(fg_color="#2A2A3E")
        ctk.CTkLabel(tip[0], text=text, font=("Microsoft YaHei UI", 11), text_color="#E0E0F0").pack(padx=8, pady=3)
        tip[0].update_idletasks()
        x = widget.winfo_rootx() + (widget.winfo_width() - tip[0].winfo_reqwidth()) // 2
        y = widget.winfo_rooty() - tip[0].winfo_reqheight() - 4
        tip[0].geometry(f"+{x}+{y}")
    def _leave(e):
        if tip[0]: tip[0].destroy(); tip[0] = None
    widget.bind("<Enter>", _enter, add="+")
    widget.bind("<Leave>", _leave, add="+")

class ModelBalanceMonitor(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self.attributes("-topmost", True)
        self.overrideredirect(True)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.FONT_TITLE = ctk.CTkFont(family="Microsoft YaHei UI", size=16, weight="bold")
        self.FONT_LABEL = ("Microsoft YaHei UI", 13)
        self.FONT_VALUE = ("Cascadia Code", 15, "bold")

        self.config = load_config()
        self.model_data = load_model_data()
        # 载入本地排名快取
        cached_ranks, self._ranking_updated, self._ranking_source, _ = load_ranking_cache()
        if cached_ranks:
            apply_rankings(cached_ranks)
        else:
            self._ranking_updated = ""
            self._ranking_source = ""
        self._fetching = False
        self._current_slot = None
        self.card_widgets = []
        self._hide_timer = None
        self._visible = False
        self._quit = False

        self._build_ui()
        self._bind_drag()
        self._refresh_dropdown()
        self._resize_window()

        # 超小型余额浮窗 (须在 timer 前建立)
        self.mini = MiniBalance(self)
        self.mini._click_cb = self._cycle_mini_slot

        def _show_from_mini():
            self._hover_enabled = False
            self.show_window()
        self.mini.set_show_cb(_show_from_mini)
        self._mini_visible = True  # 首次启动显示
        self._position_mini()

        self._last_fetch = time.time()
        self._fetch_all_data()
        self._ui_timer()

        self.bind("<Leave>", self._on_leave)
        self.bind("<Enter>", self._on_enter)

        self._create_tray()
        self.show_window()
        self._hover_enabled = False  # 首次启动保持视窗显示
        # 无 Key 时自动跳出设定页面
        if not self.active_slots:
            self.after(500, self._open_settings)
        threading.Thread(target=self._hover_loop, daemon=True).start()

    @property
    def active_slots(self):
        return [(i, s) for i, s in enumerate(self.config.get("slots", [])) if s.get("key", "").strip()]

    def _build_ui(self):
        self.configure(fg_color="#0F0F23")
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=3, pady=3)

        tb = ctk.CTkFrame(main, fg_color="#16162A", corner_radius=12, height=44)
        tb.pack(fill="x", padx=10, pady=(8, 0)); tb.pack_propagate(False)

        self.model_var = ctk.StringVar(value="")
        self.model_dropdown = ctk.CTkOptionMenu(tb, variable=self.model_var, values=["暂无配置"],
                                                font=ctk.CTkFont(family="Microsoft YaHei UI", size=12, weight="bold"),
                                                fg_color="#4F46E5", button_color="#6366F1",
                                                button_hover_color="#818CF8",
                                                width=200, height=32, corner_radius=8,
                                                command=self._on_model_select)
        self.model_dropdown.pack(side="left", padx=8)
        btnf = ctk.CTkFrame(tb, fg_color="transparent")
        btnf.pack(side="right", padx=4)
        btn_refresh = ctk.CTkButton(btnf, text="🔄", width=32, height=32, font=("Segoe UI", 13),
                      fg_color="transparent", hover_color="#374151",
                      corner_radius=6, command=self._fetch_all_data)
        btn_refresh.pack(side="left", padx=2); bind_tooltip(btn_refresh, "刷新余额")
        btn_settings = ctk.CTkButton(btnf, text="⚙", width=32, height=32, font=("Segoe UI", 13),
                      fg_color="transparent", hover_color="#374151",
                      corner_radius=6, command=self._open_settings)
        btn_settings.pack(side="left", padx=2); bind_tooltip(btn_settings, "API Key 设定")
        self.api_dot = ctk.CTkLabel(btnf, text="●", font=("Segoe UI", 9), text_color="#6B7280")
        self.api_dot.pack(side="left", padx=(2, 2)); bind_tooltip(self.api_dot, "API 连线状态")
        btn_hide = ctk.CTkButton(btnf, text="✕", width=32, height=32, fg_color="transparent",
                      hover_color="#EF4444", text_color="#94A3B8", font=("Segoe UI", 14),
                      corner_radius=6, command=self.hide_window)
        btn_hide.pack(side="left"); bind_tooltip(btn_hide, "隐藏视窗")

        # 卡片区域
        self.card_frame = ctk.CTkFrame(main, fg_color="transparent")
        self.card_frame.pack(fill="both", expand=True, padx=10, pady=(6, 2))

        # 底部状态列 — 直接放在 main 底部，用固定高度确保可见
        self.status_bar = ctk.CTkFrame(main, fg_color="#16162A", corner_radius=8, height=56)
        self.status_bar.pack(fill="x", padx=8, pady=(0, 4), side="bottom")
        self.status_bar.pack_propagate(False)

        self.progress = ctk.CTkProgressBar(self.status_bar, fg_color="#1E1E2E",
                                            progress_color="#6366F1", height=5, corner_radius=2)
        self.progress.pack(fill="x", padx=10, pady=(6, 0))

        self.tip_label = ctk.CTkLabel(self.status_bar,
            text="💡 鼠标移到托盘图标自动弹出  |  🏆 刷新排名  |  右键退出",
            font=ctk.CTkFont(family="Microsoft YaHei UI", size=13),
            text_color="#D0D0F0")
        self.tip_label.pack(padx=10, pady=(2, 6))


    def _create_tray(self):
        icon_img = create_tray_image()
        menu = pystray.Menu(
            pystray.MenuItem("显示/隐藏主视窗", self.toggle_window, default=True),
            pystray.MenuItem("切换余额浮窗", self.toggle_mini),
            pystray.MenuItem("退出", self.quit_app),
        )
        self.tray = pystray.Icon(APP_NAME, icon_img, APP_NAME, menu)
        threading.Thread(target=self.tray.run, daemon=True).start()

    def _hover_loop(self):
        """后台检测鼠标是否在右下角托盘图标附近（缩小到 50x40）"""
        try:
            import ctypes
            from ctypes import wintypes
            user32 = ctypes.windll.user32
            class POINT(ctypes.Structure):
                _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
            while not self._quit:
                time.sleep(0.25)
                if not self._hover_enabled: continue
                try:
                    pt = POINT()
                    user32.GetCursorPos(ctypes.byref(pt))
                    sw = user32.GetSystemMetrics(0)
                    sh = user32.GetSystemMetrics(1)
                    in_tray = (pt.x > sw - 50 and pt.y > sh - 40)
                    self.after(0, self._on_tray_hover, in_tray)
                except Exception:
                    pass
        except Exception:
            pass

    def _on_tray_hover(self, in_tray=None, *_):
        if self._quit: return
        if in_tray and not self._visible:
            self.show_window()
        elif not in_tray and self._visible:
            x = self.winfo_pointerx(); y = self.winfo_pointery()
            wx, wy = self.winfo_rootx(), self.winfo_rooty()
            ww, wh = self.winfo_width(), self.winfo_height()
            if not (wx <= x <= wx + ww and wy <= y <= wy + wh):
                if not self._hide_timer:
                    self._hide_timer = self.after(500, self.hide_window)

    def toggle_mini(self, icon=None, item=None):
        self._mini_visible = not self._mini_visible
        if self._mini_visible:
            self.mini.deiconify()
            self._position_mini()
        else:
            self.mini.withdraw()
            self.mini.update()
        self._update_tray_menu()

    def _update_tray_menu(self):
        try:
            label = "隐藏余额浮窗" if self._mini_visible else "显示余额浮窗"
            self.tray.menu = pystray.Menu(
                pystray.MenuItem("显示/隐藏主视窗", self.toggle_window, default=True),
                pystray.MenuItem(label, self.toggle_mini),
                pystray.MenuItem("退出", self.quit_app),
            )
            self.tray.update_menu()
        except:
            pass

    def toggle_window(self, icon=None, item=None):
        if self._visible: self.hide_window()
        else: self._hover_enabled = False; self.show_window()

    def show_window(self):
        if self._hide_timer:
            self.after_cancel(self._hide_timer); self._hide_timer = None
        self._visible = True
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        w = 460
        h = 470 if (self._current_slot is not None and
                     self.config["slots"][self._current_slot].get("provider") == "kimi") else 400
        self.geometry(f"{w}x{h}+{sw-w-20}+{sh-h-80}")
        self.deiconify()
        self.lift()
        self.attributes("-topmost", True)  # 确保置顶

    def hide_window(self):
        self._visible = False
        self._hover_enabled = True  # 隐藏后启用hover检测
        self.withdraw()
        if self._hide_timer:
            self.after_cancel(self._hide_timer); self._hide_timer = None

    def quit_app(self, icon=None, item=None):
        self._quit = True
        self._hover_enabled = False
        if self.tray: self.tray.stop()
        release_lock()
        self.quit()
        self.destroy()

    def _on_leave(self, event):
        x = self.winfo_pointerx()
        y = self.winfo_pointery()
        wx, wy = self.winfo_rootx(), self.winfo_rooty()
        ww, wh = self.winfo_width(), self.winfo_height()
        if not (wx <= x <= wx + ww and wy <= y <= wy + wh):
            if not self._hide_timer:
                self._hide_timer = self.after(500, self.hide_window)

    def _on_enter(self, event):
        if self._hide_timer:
            self.after_cancel(self._hide_timer); self._hide_timer = None

    def _show_progress(self):
        self.progress.start()
        self.update_idletasks()

    def _hide_progress(self):
        self.progress.stop()
        self.progress.set(0)
        self.update_idletasks()

    def _refresh_dropdown(self):
        active = self.active_slots
        values = []
        for i, s in active:
            icon = SLOT_ICONS[i]
            prov = PROVIDERS.get(s.get("provider", ""), {}).get("label", "")
            values.append(f"{icon}  {prov}")
        if not values:
            values = ["暂无配置"]
            self._current_slot = None
        elif self._current_slot is None or self._current_slot not in [a[0] for a in active]:
            self._current_slot = active[0][0]
        self.model_dropdown.configure(values=values)
        if values and values[0] != "暂无配置" and self._current_slot is not None:
            for idx, (i, s) in enumerate(active):
                if i == self._current_slot:
                    self.model_var.set(values[idx]); break
        else:
            self.model_var.set(values[0])
        self._rebuild_card()

    def _on_model_select(self, choice):
        active = self.active_slots
        for idx, (i, s) in enumerate(active):
            icon = SLOT_ICONS[i]
            prov = PROVIDERS.get(s.get("provider", ""), {}).get("label", "")
            if choice == f"{icon}  {prov}":
                self._current_slot = i
                self._rebuild_card()
                self._resize_window()
                self._update_mini()
                return

    def _rebuild_card(self):
        for w in self.card_widgets: w.destroy()
        self.card_widgets.clear()
        if self._current_slot is None:
            empty = ctk.CTkLabel(self.card_frame, text="点击 ⚙ 配置 API Key",
                                 font=("Microsoft YaHei UI", 14), text_color="#6B7280")
            empty.pack(expand=True); self.card_widgets.append(empty); return
        slots = self.config.get("slots", [])
        if self._current_slot >= len(slots):
            self._current_slot = None; return
        slot = slots[self._current_slot]
        provider = slot.get("provider", "")
        color = SLOT_COLORS[self._current_slot]
        icon = SLOT_ICONS[self._current_slot]
        pinfo = PROVIDERS.get(provider, {})
        prov_label = pinfo.get("label", provider)
        prov_note = pinfo.get("note", "")
        api_ok = pinfo.get("api_ok", False)
        ts = self.model_data.get("slots", [])
        while len(ts) <= self._current_slot: ts.append(dict(DEFAULT_DATA))
        # 不支援 API 的提供商：清除残留的前一个提供商资料并写入磁盘
        if not api_ok or (api_ok != True and api_ok not in ("pending", "special")):
            ts[self._current_slot] = dict(DEFAULT_DATA)
            self.model_data["slots"] = ts
            save_model_data(self.model_data)
        data = ts[self._current_slot]
        rows = get_model_rows(provider, data, pinfo)
        card = ctk.CTkFrame(self.card_frame, fg_color="#16162A", corner_radius=14,
                            border_width=1, border_color="#2A2A4A")
        card.pack(fill="both", expand=True); self.card_widgets.append(card)
        h = ctk.CTkFrame(card, fg_color="transparent")
        h.pack(fill="x", padx=18, pady=(14, 6))
        ctk.CTkLabel(h, text=icon, font=("Segoe UI Emoji", 22)).pack(side="left", padx=(0, 10))
        ctk.CTkLabel(h, text=prov_label, font=self.FONT_TITLE, text_color="#E0E0F0").pack(side="left")

        if api_ok == True: status_color = "#22C55E"
        elif api_ok == "pending": status_color = "#F59E0B"
        elif api_ok == "special": status_color = "#3B82F6"
        else: status_color = "#6B7280"
        dot = ctk.CTkFrame(h, width=8, height=8, corner_radius=4, fg_color=status_color)
        dot.pack(side="right", padx=(0, 8))
        sep = ctk.CTkFrame(card, fg_color="#2A2A4A", height=1)
        sep.pack(fill="x", padx=18, pady=(2, 6))
        for label, value, val_color in rows:
            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=18, pady=(6, 0))
            ctk.CTkLabel(row, text=label, font=self.FONT_LABEL, text_color="#94A3B8").pack(side="left")
            ctk.CTkLabel(row, text=value, font=self.FONT_VALUE, text_color=val_color).pack(side="right")
        if prov_note:
            if api_ok == True: note_color = "#6B7280"
            elif api_ok == "pending": note_color = "#F59E0B"
            elif api_ok == "special": note_color = "#3B82F6"
            else: note_color = "#EF4444"
            nr = ctk.CTkFrame(card, fg_color="transparent")
            nr.pack(fill="x", padx=18, pady=(10, 6))
            ctk.CTkLabel(nr, text=f"📋 {prov_note}", font=self.FONT_TINY, text_color=note_color).pack(side="left")
        ctk.CTkFrame(card, fg_color="transparent", height=8).pack()

    def _resize_window(self):
        provider = ""
        if self._current_slot is not None and self._current_slot < len(self.config.get("slots", [])):
            provider = self.config["slots"][self._current_slot].get("provider", "")
        h = 470 if provider == "kimi" else 400
        x, y = self.winfo_x(), self.winfo_y()
        if x < 0: x = 0
        if y < 0: y = 0
        self.geometry(f"460x{h}+{x}+{y}")

    def _open_settings(self):
        SettingsDialog(self, self.config, self._on_config_saved)

    def _on_config_saved(self):
        self.config = load_config()
        self._refresh_dropdown()
        self._resize_window()
        self.tip_label.configure(text="✅ 配置已保存 | 正在查询 API...")
        self.update_idletasks()
        self._show_progress()
        self._fetch_all_data()

    def _refresh_rankings(self, on_done=None):
        """从 llm-stats.com 刷新排名。on_done 可选回呼 (count, updated)"""
        if on_done is None:
            self._show_progress()
            self.tip_label.configure(text="🏆 正在从 llm-stats.com 抓取最新排名...")
            self.update_idletasks()
        def _do():
            try:
                ranks, site_date = fetch_rankings_from_web()
                if ranks:
                    save_ranking_cache(ranks, site_date)
                    apply_rankings(ranks)
                    updated, source, _ = get_ranking_meta()
                    self._ranking_updated = updated
                    self._ranking_source = source
                    if on_done:
                        self.after(0, lambda: on_done(len(ranks), updated))
                    else:
                        self.after(0, lambda: self._on_rankings_updated(len(ranks), updated))
                else:
                    if on_done:
                        self.after(0, lambda: on_done(0, ""))
                    else:
                        def _fail():
                            self._hide_progress()
                            self.tip_label.configure(text="❌ 排名抓取失败，请检查网络")
                            self.update_idletasks()
                        self.after(0, _fail)
            except Exception as e:
                if on_done:
                    self.after(0, lambda: on_done(-1, str(e)))
                else:
                    def _err():
                        self._hide_progress()
                        self.tip_label.configure(text=f"❌ 排名更新出错: {e}")
                        self.update_idletasks()
                    self.after(0, _err)
        threading.Thread(target=_do, daemon=True).start()

    def _on_rankings_updated(self, count, updated):
        self._hide_progress()
        _, _, site_updated = get_ranking_meta()
        site_info = f" (网站: {site_updated})" if site_updated else ""
        self.tip_label.configure(text=f"✅ 排名已更新 ({count} 家) @ {updated}{site_info}")
        self.update_idletasks()
        self._refresh_dropdown()
        self._rebuild_card()
        self._resize_window()

    def _fetch_all_data(self):
        self._last_fetch = time.time()
        if self._fetching:
            self.tip_label.configure(text="⏳ 上次查询尚未完成，请稍候...")
            self.update_idletasks()
            return
        self._fetching = True
        self._show_progress()
        self.tip_label.configure(text="🔄 正在查询各 API 余额...")
        self.update_idletasks()
        self.api_dot.configure(text="◉", text_color="#F59E0B")
        def _fetch():
            try:
                slots = self.config.get("slots", [])
                ts = list(self.model_data.get("slots", []))
                while len(ts) < MAX_SLOTS: ts.append(dict(DEFAULT_DATA))
                # 并发查询所有有效槽位
                tasks = []
                for i, s in enumerate(slots):
                    key = s.get("key", "").strip()
                    prov = s.get("provider", "").strip()
                    if not key: continue
                    pinfo = PROVIDERS.get(prov, {})
                    if not pinfo.get("balance_url") and not pinfo.get("api_ok"): continue
                    tasks.append((i, prov, key))
                updated = False
                if tasks:
                    with ThreadPoolExecutor(max_workers=min(len(tasks), 5)) as ex:
                        futures = {ex.submit(fetch_provider_data, p, k): (i, p) for i, p, k in tasks}
                        for f in as_completed(futures):
                            i, prov = futures[f]
                            try:
                                result = f.result()
                            except:
                                continue
                            while len(ts) <= i: ts.append(dict(DEFAULT_DATA))
                            if result.get("balance"):
                                ts[i]["balance"] = result["balance"]; updated = True
                            if result.get("extra"):
                                ts[i]["extra"] = result["extra"]; updated = True
                if updated:
                    self.model_data["slots"] = ts[:MAX_SLOTS]
                    save_model_data(self.model_data)
            finally:
                self._fetching = False
                self.after(0, lambda u=updated: self._on_fetch_done(u))
        threading.Thread(target=_fetch, daemon=True).start()

    def _on_fetch_done(self, updated=False):
        self._hide_progress()
        self.api_dot.configure(text="●", text_color="#22C55E")
        if not updated:
            t = time.strftime("%H:%M:%S")
            self.tip_label.configure(text=f"✅ Key 已刷新 ({t}, 无变化)")
            self.update_idletasks()
            return
        ts = self.model_data.get("slots", [])
        balances = []
        for i, s in enumerate(self.config.get("slots", [])):
            if s.get("key") and i < len(ts) and ts[i].get("balance", "—") != "—":
                balances.append(f"{s.get('provider','?')}:{ts[i]['balance']}")
        summary = " | ".join(balances) if balances else "无有效余额"
        t = time.strftime("%H:%M:%S")
        self.tip_label.configure(text=f"✅ Key 已刷新 ({t}) | {summary}")
        self.update_idletasks()
        self._rebuild_card()
        self._update_mini()

    def _ui_timer(self):
        if not self._fetching:
            self.model_data = load_model_data()
            interval = self.config.get("fetch_interval_min", FETCH_INTERVAL_MIN) * 60
            if time.time() - self._last_fetch >= interval:
                self._fetch_all_data()
        self.after(5000, self._ui_timer)

    def _position_mini(self):
        import ctypes
        sw = ctypes.windll.user32.GetSystemMetrics(0)
        self._update_mini()
        w = self.mini.winfo_reqwidth() or 120
        self.mini.geometry(f"{w}x30+{sw-w-15}+{50}")
        self.mini.deiconify()
        self.mini.lift()
        self.mini.update_idletasks()

    def _update_mini(self):
        self.mini.update_balances(self.config, self.model_data, self._current_slot)

    def _cycle_mini_slot(self):
        """点击小视窗：轮换到下一个有资料的公司"""
        active = self.active_slots
        if not active: return
        ids = [i for i, s in active]
        if self._current_slot not in ids:
            self._current_slot = ids[0]
        else:
            idx = ids.index(self._current_slot)
            self._current_slot = ids[(idx + 1) % len(ids)]
        self._rebuild_card()
        self._resize_window()
        self._update_mini()
        # 更新下拉选单
        for vi, (i, s) in enumerate(active):
            if i == self._current_slot:
                prov = PROVIDERS.get(s.get("provider", ""), {}).get("label", "")
                icon = SLOT_ICONS[i]
                self.model_var.set(f"{icon}  {prov}")
                break

    def _bind_drag(self):
        self._drag_x = self._drag_y = 0
        self._drag_clicked = False
        def sd(e):
            self._drag_x, self._drag_y = e.x, e.y
            self._drag_clicked = True
        def dd(e):
            if abs(e.x - self._drag_x) > 3 or abs(e.y - self._drag_y) > 3:
                self._drag_clicked = False
            self.geometry(f"+{self.winfo_x()+e.x-self._drag_x}+{self.winfo_y()+e.y-self._drag_y}")
        def dc(e):
            if self._drag_clicked:
                self._fetch_all_data()
        self.bind("<Button-1>", sd)
        self.bind("<B1-Motion>", dd)
        self.bind("<Double-Button-1>", dc)

# ═══════════ 入口 ═══════════

def main():
    if not acquire_lock():
        # 已有实例在运行
        return
    try:
        app = ModelBalanceMonitor()
        app.mainloop()
    finally:
        release_lock()

if __name__ == "__main__":
    main()
