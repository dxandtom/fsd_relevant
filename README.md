# fsd_relevant — 特斯拉官网 FSD 中国落地信号监控

监控特斯拉**中国官网（tesla.cn）**与**美国/国际官网（tesla.com）**上与 FSD
（Full Self-Driving / FSD 智能辅助驾驶 / 特斯拉驾驶辅助）相关的页面，
从**页面文案**和**前端代码**两个层面提取并追踪「FSD 在中国落地」的征兆。

- 📄 调研结论见 **[REPORT.md](REPORT.md)**（2026-08-28：落地时间线、官网信号盘点、后续观察点）
- 🕷️ 监控爬虫为 **[fsd_watch.py](fsd_watch.py)**，监控目标定义在 **[watchlist.json](watchlist.json)**

## 它在盯什么

| 信号类型 | 例子 | 含义 |
|---|---|---|
| 可用地区清单 | tesla.com 支持页 "currently available in …" 句子中 **China** 的进出 | 加入订阅清单 = 大陆订阅上线；移出可用清单 = 重大利空 |
| 探针页面上线 | `tesla.cn/support/full-self-driving-subscriptions` 由 404 → 200 | 大陆订阅制落地的决定性信号 |
| 文案措辞 | 订购页「完全自动驾驶能力 → FSD智能辅助驾驶 → 特斯拉驾驶辅助」的更名 | 合规准备进度 |
| 前端代码 | 订购页嵌入 JSON 里的选装代码（如 `$APF2`）、含 `fsd` 的标识符增减 | 未对外公布的功能开关/SKU 变化 |
| 价格 | 「特斯拉驾驶辅助」附近的 ¥64,000、出现「订阅/包月/每月 xx 元」 | 买断 → 订阅切换 |
| 手册版本 | 中文车主手册「FSD 智能辅助驾驶」章节内容变化 | 软件推送节奏 |

## 快速开始

```bash
pip install -r requirements.txt      # 仅需 requests；可选 playwright
python fsd_watch.py run              # 抓取快照 + 提取信号 + 与上次对比，告警写入 ALERTS.md
```

分步执行：

```bash
python fsd_watch.py snapshot                 # 抓取一轮快照到 snapshots/<UTC时间戳>/
python fsd_watch.py analyze                  # 分析最新快照 -> signals.json（含关键词命中、地区清单、选装代码、价格）
python fsd_watch.py diff                     # 对比最近两次快照 -> 输出告警并写 ALERTS.md
python fsd_watch.py snapshot --only cn-model3-design us-support-fsd-subscriptions
python fsd_watch.py snapshot --playwright    # 对被 Akamai 反爬拦截(403)的页面用真实浏览器兜底
```

首轮 `run` 只建立基线；从第二轮起才会产生对比告警。告警按信号强度分级，
其中「地区清单 ±China」「探针页 404→200」会用 🚨 标出。

## 定时监控

`.github/workflows/fsd-watch.yml` 提供了每日一次的 GitHub Actions 定时任务：
抓取 → 分析 → 对比 → 把快照与 `ALERTS.md` 提交回仓库，并把告警贴进 job summary。
也可以在任意机器上用 cron：

```cron
30 9 * * * cd /path/to/fsd_relevant && python3 fsd_watch.py run >> watch.log 2>&1
```

## 注意事项

- **低频、只读、遵守 robots.txt**（默认开启检查）。默认请求间隔 4 秒、建议每天一轮，
  仅用于个人研究，请勿改造成高频抓取。
- tesla.com 由 Akamai 提供反爬保护，纯 HTTP 抓取可能收到 403；403 本身也会被记录成状态信号，
  需要页面内容时用 `--playwright`（`pip install playwright && playwright install chromium`）。
- 订购页（design studio）是前端渲染的 SPA：requests 抓到的 HTML 里已包含嵌入的配置 JSON
  （选装代码等信号来自这里）；需要渲染后的完整文案时用 `--playwright`。
- 在无法直连特斯拉域名的受限网络（如某些云沙箱/公司内网）中 `snapshot` 会失败并把错误记入
  `meta.json`；`analyze` / `diff` 可离线运行在已有快照上。
- 快照以 gzip 存储；`run` 模式自动只保留最近 60 轮。
