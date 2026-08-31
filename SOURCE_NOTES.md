# 源码级分析笔记 — tesla.cn 实抓快照 `2026-08-28T074407Z`

> 抓取方式：GitHub Actions runner（网络不受限）运行 `fsd_watch.py run --playwright`，
> 快照已提交至 `snapshots/2026-08-28T074407Z/`。tesla.cn 全部抓取成功；
> tesla.com 各页对数据中心 IP 返回 Akamai 403（拦截本身也已记录为状态基线）。

## 1. 订购页（Model 3 / Model Y design studio）嵌入 JSON

### SKU 与定价（pricebook 原文）

| 代码 | 官方名称（`name`/`long_name`） | 价格 | 备注 |
|---|---|---|---|
| `$APBS` | 基础辅助驾驶 | 标配（base_options） | |
| `$APPB` | **增强辅助驾驶** | ¥32,000 | 与 $APF2 互斥选装 |
| `$APF2` | **特斯拉辅助驾驶** | **¥64,000** | `set_rules`: 已选 $APPB 时补差价 **¥32,000** 升级；含 `{"type":"trial","value":64000}` 试用价目类型 |

- 配置结构 `"optional":[["$APF2","$APPB"],…]`，**无任何订阅类 SKU**（无 `$APS*`）。
- 注意：live 源码中的正式名称是「特斯拉**辅助驾驶**」，而不是部分媒体报道的「特斯拉驾驶辅助」。

### 前端功能开关（当前值均为 `false`，但布线已完成）

| 开关 | 当前值 | 含义 |
|---|---|---|
| `isFsdSubscriptionStaticUrlEnabled` | `false` | FSD 订阅静态页链接开关 |
| `showFsdSubscriptionConsent` | `false` | FSD 订阅同意书弹窗（与法务 consent 列表并列） |
| `isAllowSunsetFSDinEditDesign` | `false` | 「日落 FSD」（在改配流程中下架 FSD 买断）开关 —— 对应全球 2026-02-14 起买断停售 |

⇢ 解读：订阅与「买断下架」的**代码机制已随全球配置器一起部署到中国站**，上线只差服务端把开关翻成 `true`。这是「内部已准备就绪」最直接的代码证据。

### 按车辆资格分流的文案（`App.fsdEligible` 条件渲染）

- `feature_list.default_ineligible`（`fsdEligible:false`）：
  「包括『基础辅助驾驶』和『增强辅助驾驶』套件的全部功能。**稍后推出特斯拉辅助驾驶功能**。未来您的车辆将能够在驾驶员极少干预的情况下完成绝大多数的驾驶任务。」
- `feature_list.default_eligible`（`fsdEligible:true`）：
  「……以及特斯拉辅助驾驶功能。」（当下即含，不再是「稍后推出」）
- 免责声明（两种变体共用主体）：「目前可用的功能需要驾驶员主动进行监管，车辆尚未实现完全自动驾驶。未来推出的功能的激活和可用性还有赖于进一步研发及**行政审批**（可能会需要较长的时间）。」

⇢ 解读：**「仅部分（AI4）车辆可用」的分流逻辑就写在页面代码里**；「行政审批」四个字白纸黑字挂在订购页免责声明中。

### 命名的双轨状态（代码 vs 文案）

- 代码内部键名全部仍是 FSD：`FSD_FEATURES`、`FSD_GALLERY`、`add_fsd_package`、`fsd_supervised`（内容组，挂 DailyDrive 视频素材）、`FSD_AUTOPARK_CARD` 等。
- 用户可见文案：选装包名「特斯拉辅助驾驶」；功能面板 `panelName` 为「智能辅助驾驶」（智能辅助导航驾驶 / 车道变换 / 智能泊车）。
- 页面中「订阅」字样共 8 处，**全部**属于「车载娱乐服务包」（联网服务），与 FSD 无关。

## 2. 车主手册（`GUID-2CB60804…`，简中）

- `<title>` 即「FSD 智能辅助驾驶」，正文 94 处提及；含「城市街道」「住宅区」等 V14 场景措辞。
- 手册用名「FSD 智能辅助驾驶」与订购页「特斯拉辅助驾驶」**并存**——官网命名尚未统一，典型的过渡期痕迹。
- 手册章节于 2026-05 上旬（手册版 2026.14）加入 FSD V14 完整说明（Not a Tesla App 5-11 报道），早于 5-21 官宣与 5-23 订购页更名。

## 3. 页面存在性地图（HTTP 状态基线）

| URL | 状态 | 意义 |
|---|---|---|
| `tesla.cn/model3/design`、`/modely/design`、`/`、手册两页 | 200 | 已入基线 |
| `tesla.cn/support/autopilot` | **404** | 中国站无此路径（正确路径为 `/autopilot`，watchlist 已修正） |
| `tesla.cn/support/fsd` | 404 | 探针：变 200 即强信号 |
| `tesla.cn/support/full-self-driving-subscriptions` | **404** | 探针：变 200 = 大陆订阅上线 |
| `tesla.cn/fsd` | 404 | 探针 |
| `tesla.com/*`（US/HK 各页） | 403（Akamai 拦数据中心 IP） | runner 侧无法取 US 内容；国家清单监控需本地网络运行 |

## 4. 首页

- 首页存在 `id="FSD"` 的内容锚点区块，当前内容仅为「查看所有现行活动规则」→ `/campaign/sales-promo-overview`。该槽位历史上承载 FSD 权益/转移活动，已加入 watchlist。

## 5. 与「App 订阅发票」传闻的交叉印证

- tesla.cn 存在[「增强版自动辅助驾驶 月包/季包」支持页](https://www.tesla.cn/support/enhanced-autopilot-trial)：**EAP 已在中国以月包/季包形式通过 Tesla App「升级」标签销售**——即 App 内周期性付费与开票链路在中国已为 EAP 打通。
- 因此「FSD 订阅」发票类目在 App 短暂出现再消失，从基础设施角度完全可行（把现成的 EAP 月包链路复制到 FSD 商品上）；但该传闻本身未见可靠信源报道，且 5 月已有「月费 599 元」假截图被辟谣的先例，**按未证实处理**。

## 6. 下一步监控要点（源码层）

1. 三个 `false` 开关任何一个变 `true`（尤其 `isFsdSubscriptionStaticUrlEnabled` / `showFsdSubscriptionConsent`）；
2. 配置器 JSON 出现 `$APS*` 类订阅 SKU，或 `$APF2` 的 `pricing` 出现按月计价类型；
3. `feature_list.default_ineligible` 中「稍后推出」措辞消失（= 全量可用）；
4. 探针页 404→200；
5. `enhanced-autopilot-trial` 页面出现 FSD 字样或新月包条目。

---

# 监控日志 · 2026-08-31（第 4 轮每日快照后）

**结论：8/28 → 8/31 四轮快照，所有核心信号原地踏步，无实质进展。**

| 信号 | 8/28 基线 | 8/31 现状 | 变化 |
|---|---|---|---|
| 三个订阅/日落开关（订购页源码） | 均 `false` | 均 `false` | 无 |
| `$APF2`「特斯拉辅助驾驶」¥64,000 / 无订阅 SKU | ✓ | ✓ | 无 |
| 「稍后推出」资格分流措辞 | 存在（8 处） | 存在（8 处） | 无 |
| 三个探针页（/fsd、/support/fsd-subscriptions 等） | 404 | 404 | 无 |
| 车主手册 FSD 章节（M3/MY，GUID-2CB60804） | 200 | 200 | **sha256 逐字节相同，四天零改动** |
| tesla.com 各页 | Akamai 403 | Akamai 403 | 无法观测 |

**误报排除**：8/31 告警中 `cn-autopilot`、`cn-support-eap-trial` 的「[代码-] 移除 fsd 标识符」
系两页面当日临时 503 所致；所谓消失的 `//www.tesla.cn/fsd`、`/zh_cn/fsd/safety` 链接
实为 404/403 页面骨架中的 hreflang 语言标记，自首轮快照起就存在（顺带确认了
`/zh_cn/fsd/safety` 这一 FSD 安全报告页路径已在站点骨架中预留）。正常 200 页面
（首页、autopilot-notes、活动页）中不含任何真实 fsd 链接。

**新闻面核查（8/29-8/31）**：无新事件。「中国已完成审批」的全球名单实为 6 月 8 日
CVPR 大会上特斯拉 AI 负责人 Ashok Elluswamy 展示的幻灯片（近日被自媒体再传播）；
「车主手册更新」指的是 5 月 2026.14 版更新（Not a Tesla App 5-11 报道）。周末英文媒体
（Benzinga round-up 等）仅复盘 8/25-26 谣言与辟谣。距 Q3 审批窗口关闭还有 30 天。

**监控升级**：watchlist 新增旧款 Model Y（2020-2024，HW3 为主）手册章节
（现标题「完全自动驾驶能力（监控版本）」，更新为完整 FSD 章节即旧硬件适配信号）
与 Model 3 手册首页（捕捉 2026.14 → 2026.20 版本跳变）。
