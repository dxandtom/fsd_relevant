#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fsd_watch.py — 特斯拉官网「FSD 中国落地」信号监控爬虫

监控 tesla.cn（中国官网）与 tesla.com（美国/国际官网）上与 FSD
（Full Self-Driving / 智能辅助驾驶 / 特斯拉驾驶辅助）相关的页面，
定期抓取快照并对比差异，从页面文案与前端代码两个层面提取
「FSD 在中国落地」的征兆，例如：

  * tesla.com 支持页上「currently available in ...」国家清单是否加入/移除 China
  * tesla.cn 是否上线 FSD 订阅支持页 / FSD 落地页（HTTP 404 -> 200 即为强信号）
  * 订购页中 FSD 的中文命名变化（完全自动驾驶能力 -> FSD智能辅助驾驶 -> 特斯拉驾驶辅助）
  * 订购页嵌入 JSON / JS 代码中的选装代码（如 $APF2）与含 "fsd" 的标识符增减
  * 价格与订阅（包月）字样的出现

用法：
  python fsd_watch.py snapshot            # 抓取一轮快照到 snapshots/<UTC时间戳>/
  python fsd_watch.py analyze [DIR]       # 分析某个快照目录（默认最新），生成 signals.json
  python fsd_watch.py diff [OLD] [NEW]    # 对比两个快照目录（默认最近两次），生成告警
  python fsd_watch.py run                 # snapshot + analyze + diff，并把告警写入 ALERTS.md

常用选项：
  --delay N        每个请求之间的间隔秒数（默认 4，礼貌抓取）
  --only slug ...  只抓取/分析 watchlist 中指定的条目
  --playwright     对返回 403 的页面改用 Playwright 真实浏览器重试（需已安装 playwright）
  --ignore-robots  忽略 robots.txt（默认遵守）

说明：
  * 本脚本只做低频、只读的公开页面访问，用于个人研究；请保持默认的
    低频率（建议每天 1 次），不要用于高频抓取。
  * 在无法直连特斯拉域名的受限网络环境（如部分云沙箱）中，snapshot
    会失败并记录错误；analyze/diff 可离线运行在已有快照上。
"""

import argparse
import difflib
import gzip
import hashlib
import html as html_lib
import json
import re
import sys
import time
import urllib.robotparser
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

try:
    import requests
except ImportError:  # 允许在只跑 analyze/diff 的环境里没有 requests
    requests = None

ROOT = Path(__file__).resolve().parent
SNAP_ROOT = ROOT / "snapshots"
WATCHLIST_PATH = ROOT / "watchlist.json"

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)

# ---------------------------------------------------------------------------
# 信号定义
# ---------------------------------------------------------------------------

# 页面文案 / 代码中值得追踪的关键词（中英文）
KEYWORDS = [
    # 中文命名的历史演变，任何一个的出现/消失都值得关注
    "完全自动驾驶",
    "全自动驾驶",
    "FSD智能辅助驾驶",
    "FSD 智能辅助驾驶",
    "智能辅助驾驶",
    "特斯拉驾驶辅助",
    "增强版自动辅助驾驶",
    "自动辅助驾驶",
    "城市道路",
    "监督",           # 监督版 / 受监督
    "订阅",
    "包月",
    "买断",
    "敬请期待",
    "即将推出",
    "稍后推出",
    "转移",           # FSD 权益转移活动
    # 英文
    "FSD",
    "Full Self-Driving",
    "Supervised",
    "subscription",
    "currently available",
    "China",
    "Mainland China",
    "coming soon",
    "robotaxi",
]

# 选装/SKU 代码（特斯拉订购页嵌入 JSON 里的 option codes）
OPTION_CODE_RE = re.compile(r"\$AP[A-Z0-9]{2,6}")

# 前端代码中含 fsd 的标识符（JS 变量、JSON 键、CSS 类、接口路径等）
FSD_IDENT_RE = re.compile(r"[A-Za-z0-9_$./-]*fsd[A-Za-z0-9_$./-]*", re.I)

# 价格模式（¥64,000 / 6.4万 / $99/month / 每月xx元 等）
PRICE_RE = re.compile(
    r"(?:¥|￥|RMB\s?|人民币\s?)[\d,，.]+万?|[\d.]+\s*万元?|"
    r"\$\s?[\d,]+(?:\.\d+)?(?:\s*/\s*(?:mo|month))?|"
    r"每月\s*[\d,，.]+\s*元|[\d,，.]+\s*元\s*/\s*月"
)

# tesla.com 英文支持页的国家清单句式（如 "currently available in the U.S., Canada, China ..."）
AVAIL_PHRASE_RE = re.compile(r"(?:currently|now)\s+available\s+in\s+", re.I)


def extract_avail_lists(text: str):
    """从去标签文本中提取可用地区清单。要能容忍 'the U.S.' 这类缩写句点。"""
    out = []
    for m in AVAIL_PHRASE_RE.finditer(text):
        seg = text[m.end(): m.end() + 400]
        # 句子终止：句号后跟 空白+大写字母/左括号，或句号处于段末/行末
        end = len(seg)
        stop = re.search(r"[.。](?=\s+[A-Z(])|[.。]\s*$|[.。](?=\s*\n)", seg)
        if stop:
            end = stop.start()
        parts = re.split(r",|\band\b|、|和", seg[:end])
        countries = [re.sub(r"\s+", " ", p).strip(" .。") for p in parts]
        countries = [c for c in countries if c and len(c) < 40]
        if len(countries) >= 2:
            out.append(countries)
    return out

# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------


def utcnow_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")


def load_watchlist():
    with open(WATCHLIST_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["targets"]


def read_html(snap_dir: Path, slug: str):
    """读取快照中某个条目的 HTML（gz 优先）。不存在返回 None。"""
    gz = snap_dir / f"{slug}.html.gz"
    plain = snap_dir / f"{slug}.html"
    if gz.exists():
        with gzip.open(gz, "rt", encoding="utf-8", errors="replace") as f:
            return f.read()
    if plain.exists():
        return plain.read_text(encoding="utf-8", errors="replace")
    return None


def read_meta(snap_dir: Path):
    p = snap_dir / "meta.json"
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {}


SCRIPT_RE = re.compile(r"<script\b[^>]*>(.*?)</script>", re.S | re.I)
STYLE_RE = re.compile(r"<(style|noscript)\b[^>]*>.*?</\1>", re.S | re.I)
TAG_RE = re.compile(r"<[^>]+>")
# 疑似构建哈希/base64 的噪音行（diff 时过滤）
NOISE_LINE_RE = re.compile(r"^[A-Za-z0-9+/=_.-]{40,}$")


def split_page(html: str):
    """把页面拆成 (可见文本, 脚本代码)。"""
    scripts = "\n".join(m.group(1) for m in SCRIPT_RE.finditer(html))
    no_script = SCRIPT_RE.sub(" ", html)
    no_style = STYLE_RE.sub(" ", no_script)
    text = TAG_RE.sub(" ", no_style)
    text = html_lib.unescape(text)
    lines = []
    for raw_line in re.split(r"[\r\n]+", text):
        line = re.sub(r"[ \t　]+", " ", raw_line).strip()
        if line and not NOISE_LINE_RE.match(line):
            lines.append(line)
    return "\n".join(lines), scripts


def keyword_contexts(content: str, source: str, max_per_kw: int = 5):
    """扫描关键词，返回 {kw: {"count": n, "contexts": [...]}}。"""
    out = {}
    for kw in KEYWORDS:
        hits = []
        for m in re.finditer(re.escape(kw), content, re.I):
            s = max(0, m.start() - 60)
            e = min(len(content), m.end() + 60)
            ctx = re.sub(r"\s+", " ", content[s:e]).strip()
            hits.append(ctx)
        if hits:
            out[kw] = {
                "count": len(hits),
                "source": source,
                "contexts": hits[:max_per_kw],
            }
    return out


def extract_signals(html: str):
    """从一张页面提取全部信号。"""
    text, scripts = split_page(html)

    signals = {
        "keywords_text": keyword_contexts(text, "text"),
        "keywords_code": keyword_contexts(scripts, "code", max_per_kw=3),
        "option_codes": sorted(set(OPTION_CODE_RE.findall(html))),
        "fsd_identifiers": [],
        "availability_lists": [],
        "mentions_china": bool(re.search(r"China|中国大陆|中国内地", html)),
        "price_mentions": [],
    }

    idents = set()
    for m in FSD_IDENT_RE.finditer(html):
        tok = m.group(0)
        if 3 <= len(tok) <= 60:
            idents.add(tok)
    signals["fsd_identifiers"] = sorted(idents)[:200]

    signals["availability_lists"] = extract_avail_lists(text)

    # 关键词上下文附近的价格
    seen_prices = set()
    for bucket in ("keywords_text", "keywords_code"):
        for kw, info in signals[bucket].items():
            for ctx in info["contexts"]:
                for pm in PRICE_RE.findall(ctx):
                    key = (kw, pm)
                    if key not in seen_prices:
                        seen_prices.add(key)
                        signals["price_mentions"].append(
                            {"near": kw, "price": pm}
                        )

    return signals, text


# ---------------------------------------------------------------------------
# snapshot
# ---------------------------------------------------------------------------


class RobotsCache:
    def __init__(self, enabled: bool):
        self.enabled = enabled
        self._cache = {}

    def allowed(self, url: str) -> bool:
        if not self.enabled:
            return True
        origin = "{0.scheme}://{0.netloc}".format(urlsplit(url))
        rp = self._cache.get(origin)
        if rp is None:
            rp = urllib.robotparser.RobotFileParser()
            try:
                resp = requests.get(
                    origin + "/robots.txt",
                    headers={"User-Agent": UA},
                    timeout=20,
                )
                if resp.status_code == 200:
                    rp.parse(resp.text.splitlines())
                else:
                    rp = None  # 无法获取则默认放行
            except Exception:
                rp = None
            self._cache[origin] = rp if rp is not None else False
            rp = self._cache[origin]
        if rp is False:
            return True
        return rp.can_fetch(UA, url)


def fetch_requests(url: str, lang: str):
    headers = {
        "User-Agent": UA,
        "Accept": (
            "text/html,application/xhtml+xml,application/xml;q=0.9,"
            "application/json;q=0.8,*/*;q=0.7"
        ),
        "Accept-Language": lang,
        "Cache-Control": "no-cache",
    }
    last_err = None
    for attempt in range(3):
        try:
            resp = requests.get(url, headers=headers, timeout=45)
            hdrs = {
                k: resp.headers.get(k)
                for k in ("Last-Modified", "ETag", "X-Cache", "Age")
                if resp.headers.get(k)
            }
            return resp.status_code, resp.text, None, hdrs
        except Exception as e:  # 网络错误重试
            last_err = str(e)
            time.sleep(2 * (attempt + 1))
    return None, None, last_err, {}


def fetch_playwright(url: str, lang: str):
    """403/反爬时的浏览器兜底。需要 pip install playwright && playwright install chromium"""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return None, None, "playwright 未安装"
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            ctx = browser.new_context(user_agent=UA, locale=lang.split(",")[0])
            page = ctx.new_page()
            resp = page.goto(url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(4000)  # 等待前端渲染出订购页数据
            content = page.content()
            status = resp.status if resp else None
            browser.close()
            return status, content, None
    except Exception as e:
        return None, None, str(e)


def cmd_snapshot(args):
    if requests is None:
        print("错误：需要先 pip install requests", file=sys.stderr)
        return 2
    targets = load_watchlist()
    if args.only:
        targets = [t for t in targets if t["slug"] in set(args.only)]
    robots = RobotsCache(enabled=not args.ignore_robots)

    snap_dir = SNAP_ROOT / utcnow_stamp()
    snap_dir.mkdir(parents=True, exist_ok=True)
    meta = {}
    for i, t in enumerate(targets):
        slug, url = t["slug"], t["url"]
        lang = t.get("lang", "en-US,en;q=0.9")
        if i:
            time.sleep(max(args.delay, 1))
        if not robots.allowed(url):
            print(f"[skip ] {slug}: robots.txt 不允许抓取 {url}")
            meta[slug] = {"url": url, "status": None, "error": "robots_disallow"}
            continue
        status, body, err, hdrs = fetch_requests(url, lang)
        engine = "requests"
        if args.playwright and (status in (403, 429) or status is None):
            s2, b2, e2 = fetch_playwright(url, lang)
            if b2:
                status, body, err, engine = s2, b2, e2, "playwright"
        entry = {
            "url": url,
            "note": t.get("note", ""),
            "status": status,
            "engine": engine,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "error": err,
        }
        if hdrs:
            entry["headers"] = hdrs
        if body is not None:
            data = body.encode("utf-8", errors="replace")
            entry["bytes"] = len(data)
            entry["sha256"] = hashlib.sha256(data).hexdigest()
            with gzip.open(snap_dir / f"{slug}.html.gz", "wb") as f:
                f.write(data)
        meta[slug] = entry
        print(f"[{str(status):>5}] {slug}: {url}" + (f"  !! {err}" if err else ""))
    (snap_dir / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\n快照已保存到 {snap_dir}")
    return 0


# ---------------------------------------------------------------------------
# analyze
# ---------------------------------------------------------------------------


def snapshot_dirs():
    if not SNAP_ROOT.exists():
        return []
    return sorted(d for d in SNAP_ROOT.iterdir() if d.is_dir())


def resolve_dir(name):
    if name:
        p = Path(name)
        if not p.exists():
            p = SNAP_ROOT / name
        if not p.exists():
            raise SystemExit(f"找不到快照目录: {name}")
        return p
    dirs = snapshot_dirs()
    if not dirs:
        raise SystemExit("snapshots/ 下还没有任何快照，请先运行 snapshot")
    return dirs[-1]


def cmd_analyze(args):
    snap_dir = resolve_dir(args.dir)
    meta = read_meta(snap_dir)
    result = {}
    for slug, m in meta.items():
        if args.only and slug not in set(args.only):
            continue
        html = read_html(snap_dir, slug)
        entry = {"url": m.get("url"), "status": m.get("status")}
        if html:
            signals, _text = extract_signals(html)
            entry["signals"] = signals
        result[slug] = entry
    out = snap_dir / "signals.json"
    out.write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"信号分析已写入 {out}\n")
    # 摘要
    for slug, entry in result.items():
        sig = entry.get("signals")
        if not sig:
            print(f"- {slug}: HTTP {entry['status']}（无内容）")
            continue
        kws = sorted(
            set(sig["keywords_text"]) | set(sig["keywords_code"])
        )
        lists = sig["availability_lists"]
        line = f"- {slug}: HTTP {entry['status']}, 命中关键词 {len(kws)} 个"
        if sig["option_codes"]:
            line += f", 选装代码 {sig['option_codes']}"
        if lists:
            for lst in lists:
                cn = "含中国" if any("China" in c or "中国" in c for c in lst) else "不含中国"
                line += f"\n    可用地区清单({cn}): {', '.join(lst)}"
        print(line)
    return 0


# ---------------------------------------------------------------------------
# diff
# ---------------------------------------------------------------------------


def flatten_avail(sig):
    out = set()
    for lst in sig.get("availability_lists", []):
        for c in lst:
            out.add(c.strip())
    return out


def cmd_diff(args):
    dirs = snapshot_dirs()
    if args.old and args.new:
        old_dir, new_dir = resolve_dir(args.old), resolve_dir(args.new)
    elif len(dirs) >= 2:
        old_dir, new_dir = dirs[-2], dirs[-1]
    else:
        print("快照不足两次，无法对比（首轮快照将作为后续对比基线）。")
        return 0

    old_meta, new_meta = read_meta(old_dir), read_meta(new_dir)
    alerts = []
    details = []

    for slug in sorted(set(old_meta) | set(new_meta)):
        om, nm = old_meta.get(slug), new_meta.get(slug)
        o_status = om.get("status") if om else None
        n_status = nm.get("status") if nm else None

        if om is None:
            alerts.append(f"**[新监控项]** `{slug}` 首次出现，HTTP {n_status}")
            continue
        if nm is None:
            alerts.append(f"**[移除监控项]** `{slug}` 本轮未抓取")
            continue
        if o_status != n_status:
            hint = ""
            if o_status in (404, 403, None) and n_status == 200:
                hint = " —— 页面上线，强信号！"
            elif o_status == 200 and n_status in (404, 410):
                hint = " —— 页面下线，值得关注！"
            alerts.append(
                f"**[状态]** `{slug}`: HTTP {o_status} → {n_status}{hint}"
            )

        o_html, n_html = read_html(old_dir, slug), read_html(new_dir, slug)
        if not o_html or not n_html:
            continue
        if hashlib.sha256(o_html.encode()).digest() == hashlib.sha256(
            n_html.encode()
        ).digest():
            continue

        o_sig, o_text = extract_signals(o_html)
        n_sig, n_text = extract_signals(n_html)

        # 1) 可用地区清单变化（最高优先级）
        o_av, n_av = flatten_avail(o_sig), flatten_avail(n_sig)
        added_c, removed_c = n_av - o_av, o_av - n_av
        for c in sorted(added_c):
            mark = " 🚨" if ("China" in c or "中国" in c) else ""
            alerts.append(f"**[地区清单+]** `{slug}`: 新增 **{c}**{mark}")
        for c in sorted(removed_c):
            mark = " 🚨" if ("China" in c or "中国" in c) else ""
            alerts.append(f"**[地区清单-]** `{slug}`: 移除 **{c}**{mark}")

        # 2) 选装代码 / fsd 标识符（代码层面改动）
        for name, key in (("选装代码", "option_codes"), ("fsd标识符", "fsd_identifiers")):
            o_set, n_set = set(o_sig[key]), set(n_sig[key])
            add, rem = sorted(n_set - o_set), sorted(o_set - n_set)
            if add:
                alerts.append(f"**[代码+]** `{slug}` 新增{name}: {add[:15]}")
            if rem:
                alerts.append(f"**[代码-]** `{slug}` 移除{name}: {rem[:15]}")

        # 3) 价格变化
        o_prices = {(p["near"], p["price"]) for p in o_sig["price_mentions"]}
        n_prices = {(p["near"], p["price"]) for p in n_sig["price_mentions"]}
        for near, price in sorted(n_prices - o_prices):
            alerts.append(f"**[价格+]** `{slug}`: “{near}”附近出现 {price}")
        for near, price in sorted(o_prices - n_prices):
            alerts.append(f"**[价格-]** `{slug}`: “{near}”附近的 {price} 消失")

        # 4) 含关键词的文案行增删
        diff_lines = list(
            difflib.unified_diff(
                o_text.splitlines(), n_text.splitlines(), lineterm="", n=0
            )
        )
        kw_changes = []
        for dl in diff_lines:
            if dl[:1] in "+-" and dl[:3] not in ("+++", "---"):
                if any(re.search(re.escape(k), dl, re.I) for k in KEYWORDS):
                    kw_changes.append(dl)
        if kw_changes:
            alerts.append(
                f"**[文案]** `{slug}` 有 {len(kw_changes)} 行含关键词的文案变动"
            )
            details.append(
                "### `%s` 文案变动（含关键词的行）\n```diff\n%s\n```"
                % (slug, "\n".join(kw_changes[:40]))
            )

    report = [
        "# FSD Watch 对比告警",
        "",
        f"- 旧快照: `{old_dir.name}`",
        f"- 新快照: `{new_dir.name}`",
        f"- 生成时间: {datetime.now(timezone.utc).isoformat()}",
        "",
    ]
    if alerts:
        report.append("## 告警")
        report += [f"- {a}" for a in alerts]
    else:
        report.append("本轮对比未发现值得关注的变化。")
    if details:
        report += ["", "## 明细"] + details

    out_text = "\n".join(report) + "\n"
    (ROOT / "ALERTS.md").write_text(out_text, encoding="utf-8")
    print(out_text)
    return 0


def cmd_run(args):
    rc = cmd_snapshot(args)
    if rc:
        return rc
    args.dir = None
    cmd_analyze(args)

    class D:
        old = None
        new = None
        only = args.only

    cmd_diff(D)
    # 清理过老的快照，避免仓库无限膨胀（保留最近 60 个）
    dirs = snapshot_dirs()
    for d in dirs[:-60]:
        for f in d.iterdir():
            f.unlink()
        d.rmdir()
    return 0


# ---------------------------------------------------------------------------


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_snap = sub.add_parser("snapshot", help="抓取一轮快照")
    p_ana = sub.add_parser("analyze", help="分析快照，提取信号")
    p_diff = sub.add_parser("diff", help="对比两个快照")
    p_run = sub.add_parser("run", help="snapshot + analyze + diff")

    for p in (p_snap, p_run):
        p.add_argument("--delay", type=float, default=4)
        p.add_argument("--playwright", action="store_true")
        p.add_argument("--ignore-robots", action="store_true")
    for p in (p_snap, p_ana, p_run):
        p.add_argument("--only", nargs="*", default=None)
    p_ana.add_argument("dir", nargs="?", default=None)
    p_diff.add_argument("old", nargs="?", default=None)
    p_diff.add_argument("new", nargs="?", default=None)
    p_diff.add_argument("--only", nargs="*", default=None)

    args = ap.parse_args()
    fn = {
        "snapshot": cmd_snapshot,
        "analyze": cmd_analyze,
        "diff": cmd_diff,
        "run": cmd_run,
    }[args.cmd]
    raise SystemExit(fn(args))


if __name__ == "__main__":
    main()
