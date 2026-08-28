# 特斯拉 FSD 中国落地信号调研报告

**调研日期：2026-08-28** ｜ 方法：特斯拉中美官网公开页面信号 + 多方新闻交叉验证

> 说明：本次调研运行在网络受限的沙箱中，特斯拉域名被出口策略拦截，无法直接抓取
> tesla.cn / tesla.com 页面原文。官网内容结论来自搜索引擎索引到的官网页面快照
> （tesla.cn 车主手册、tesla.com 支持页均已被索引）以及多家媒体的交叉验证。
> 仓库内的 `fsd_watch.py` 爬虫可在开放网络环境中对下述每一条官网信号进行复核与持续监控。

---

## 一、结论（TL;DR）

**FSD 已经于 2026 年 5 月 21 日正式官宣落地中国，目前处于「有限试点」阶段；
全量推送卡在监管审批的最后一环，官方目标是 2026 年第三季度（还剩约一个月）。**

1. 特斯拉 2026-05-21 官宣 FSD（监督版）在包括中国在内的 10 个国家/地区可用，
   但大陆实际仅对「AI4（HW4）硬件 + 已购 6.4 万元选装包」的用户小范围开放，
   并在北京、上海、广州、深圳等城市进行员工内测。
2. 官网层面的落地准备已基本完成：简体中文车主手册已上线完整的
   「FSD 智能辅助驾驶」章节（2026.14 版起，对应 FSD V14）；订购页已按监管要求
   完成合规更名（→「特斯拉驾驶辅助」）；tesla.com 官方口径把中国列为
   FSD（Supervised）「currently available」市场。
3. 2026-08-22 tesla.com 更新的「12 个订阅市场清单」不含中国，被部分媒体解读为
   「移除中国」。核实后这是**误读**：该清单只列已开通**订阅制**的市场，
   大陆仍是买断制（6.4 万元），本就不该出现在订阅清单里；tesla.com 的可用性
   口径页面仍列有中国。
4. 主要不确定性：Q3 全面审批能否如期完成（历史上时间表多次后移：
   2026 年 2 月 → Q3）；以及大陆何时切换到订阅制（全球已于 2026-02-14 停售买断，
   港澳台 2026-06-30 完成切换，大陆是最后一个买断市场）。

---

## 二、时间线（含官网改动节点）

| 时间 | 事件 | 性质 |
|---|---|---|
| 2025-02-25 | 首次向中国车主推送「城市道路 Autopilot 自动辅助驾驶」（基于 EAP 架构的本土化简化版，使用境内数据训练） | 软件推送 |
| 2025-03 | 推送约一个月后暂停：工信部/市监总局新规要求涉及自动驾驶的 OTA 提前 60 日备案（功能边界、ODD、测试验证报告、事故应急预案等） | 监管 |
| 2026-01 | 马斯克称 FSD 监督版「最早 2026 年 2 月」获中国与欧洲批准 | 表态 |
| 2026-02 | 上海临港 AI 训练中心投运；数据境内全留存；与百度地图合作合规高精地图 | 基础设施 |
| 2026-02-14 | 全球停售 FSD 买断，转 $99/月订阅（大陆暂未跟进） | 商业模式 |
| 2026-02 | 工信部/市监总局明令禁止 L2 产品使用「自动驾驶/全自动」等误导性宣传词 | 监管 |
| 2026-04-23 | Q1 财报会：CFO Taneja 表示目标 **2026 Q3 在中国获得全面商用许可** | 官方表态 |
| 2026-05 上旬 | **【官网改动】** tesla.cn 车主手册更新至 2026.14，新增完整 FSD V14 中文章节「FSD 智能辅助驾驶」 | 官网信号 |
| 2026-05-21 | **官宣 FSD Supervised 在 10 国/地区可用，含中国**（马斯克随美方国事访问抵京一周后）；大陆限 AI4 硬件+已购用户小规模试点 | 里程碑 |
| 2026-05-23~25 | **【官网改动】** tesla.cn 订购页更名：「FSD」字样消失，统一为**「特斯拉驾驶辅助」**，价格 6.4 万元不变 | 官网信号 |
| 2026-06 | 获分阶段批准（staged approval），可向合规车辆部署 | 监管 |
| 2026-06-26 | 港澳台官宣 6-30 后下架买断、全面转订阅；大陆「尚无时间表」 | 商业模式 |
| 2026-08-10 | 韩国订阅 8-21 上线（月费折合约 ¥719）；媒体推测大陆订阅价 ¥499~949/月 | 先行指标 |
| 2026-08-22 | **【官网改动】** tesla.com 订阅可用市场清单更新为 12 个，不含中国 → 引发「移除中国」争议（实为口径差异，见下） | 官网信号 |
| 2026-08-25 | 网传「上海 FSD 数据中心人去楼空、团队撤离、FSD 数年内无法落地」 | 谣言 |
| 2026-08-26 | 特斯拉中国辟谣：数据中心正常运转、辅助驾驶相关招聘加速进行、已向公安机关报案 | 官方回应 |

---

## 三、当前官网上可观察到的信号（爬虫可复核）

### 3.1 tesla.cn（中国官网）

| 信号 | 现状 | 解读 |
|---|---|---|
| 车主手册「FSD 智能辅助驾驶」章节（Model 3/S/Y 简中版，GUID-2CB60804…） | **已上线**：明确写明「适用于各种驾驶场景，可在任何类型的道路上使用，包括住宅区街道和城市街道」，含驾驶室摄像头注意力监控、数据不出车等说明 | 面向大陆用户的完整功能文档已就绪，落地准备完成的实锤 |
| 订购页选装包名称 | 「特斯拉驾驶辅助」（不再出现 FSD 字样），6.4 万元买断，含基础/增强辅助驾驶全部功能，页面提示「需驾驶员主动监管，尚未实现完全自动驾驶」 | 按 2026-02 新规完成合规更名 = 为全量推送扫清宣传合规障碍 |
| FSD 订阅支持页（/support/full-self-driving-subscriptions 中文版） | 未上线 | **404→200 将是大陆订阅制落地的决定性信号**（watchlist 已设探针） |

### 3.2 tesla.com（美国/国际官网）

| 信号 | 现状 | 解读 |
|---|---|---|
| FSD 可用性口径（/fsd 等页面） | 「currently available in the U.S., Canada, **China**, Mexico, Puerto Rico, Australia, New Zealand and South Korea」 | 官方仍把中国列为已可用市场 |
| 订阅市场清单（/support/full-self-driving-subscriptions，2026-08-22 更新） | 12 市场：美、加、墨、波多黎各、澳、新西兰、韩、荷、立陶宛、爱沙尼亚、丹麦、比利时——**无中国** | 只统计已开通**订阅**的市场；大陆是买断制所以不在其中。「移除中国」是误读，但也说明大陆订阅仍未就绪 |
| 港澳台订阅支持页（zh_hk 等） | 已转订阅 | 大陆商业模式切换的先行指标 |

### 3.3 两个口径不一致本身就是最有信息量的信号

tesla.com 同时存在「中国可用」（使用口径）与「订阅清单无中国」（商业口径）两个页面。
这种不一致精确刻画了现状：**技术与文档已落地、小范围可用，但商业化全量开放未完成。**
两个口径任何一侧的变动（订阅清单加入 China，或可用清单移除 China）都会立即改变判断，
这正是 `fsd_watch.py` 重点盯的两行文案。

---

## 四、判断与展望

**积极信号（支持“临近全量落地”）：**
- 官宣可用 + 员工内测 + 小规模推送已在进行（不是从零开始）；
- 合规动作密集完成：更名、数据境内留存、临港训练中心、百度高精地图、OTA 备案流程；
- CFO 给出明确的 Q3 目标，且 6 月已拿到分阶段批准；
- 辅助驾驶团队招聘在加速（特斯拉官方 8-26 表态）；
- 韩国等新市场按月上线订阅，全球推广节奏很快。

**风险信号（支持“继续延期”）：**
- 时间表已多次后移（2026-02 → Q3），Q3 只剩一个月，全量推送仍未官宣；
- 8 月下旬谣言风波说明市场对进度的耐心在下降；
- 强制性国家标准（组合驾驶辅助）与 OTA 备案流程仍是硬约束；
- 仅 AI4（HW4）车型适配，HW3 存量车主的升级方案未明。

**基准判断：** FSD 在中国已完成「落地」（可用性意义上），全量推送大概率在
2026 Q3 末～Q4 之间，伴随（或紧接着）大陆订阅制切换；若 9 月底前订阅清单仍无
中国且无全量推送公告，则应下调预期至 2026 年底~2027 年初。

---

## 五、后续 30 天监控清单（对应 watchlist.json）

按信号强度排序：

1. 🚨 `us-support-fsd-subscriptions` 的国家清单出现 **China** → 大陆订阅上线，全量落地；
2. 🚨 `cn-support-fsd-subscriptions` / `cn-fsd-landing` 探针 404→200 → 订阅/落地页上线；
3. `cn-model3-design` / `cn-modely-design` 出现「订阅/包月」字样，或 6.4 万价格变动/下架；
4. `cn-home` 出现全量推送公告或新版本发布活动；
5. 车主手册章节内容与版本号更新（推送节奏）；
6. 订购页嵌入代码中新增订阅类选装代码（对照美国订购页的订阅 SKU）；
7. 反向信号：tesla.com 可用清单若移除 China → 重大利空，需人工核实。

---

## 六、主要信息来源

**官网（信号原文出处）**
- tesla.cn 车主手册 FSD 章节：`https://www.tesla.cn/ownersmanual/model3/zh_cn_us/GUID-2CB60804-9CEA-4F4B-8B04-09B991368DC5.html`
- tesla.com FSD 订阅支持页：`https://www.tesla.com/support/full-self-driving-subscriptions`
- tesla.com FSD 落地页：`https://www.tesla.com/fsd`

**5·21 官宣与试点**
- CNBC: [Tesla brings 'Full Self-Driving (Supervised)' to China after years of delays](https://www.cnbc.com/2026/05/21/tesla-full-self-driving-china-launch-fsd.html)
- CnEVPost: [Tesla says FSD Supervised now available in countries including China](https://cnevpost.com/2026/05/21/tesla-says-fsd-supervised-available-in-china/)
- 虎嗅: [特斯拉监督版FSD在中国试点启动，2026年第三季度或全面获批](https://www.huxiu.com/article/4860646.html)
- 证券时报: [特斯拉监督版FSD登陆中国，仅适配部分AI4硬件车型](https://www.stcn.com/article/detail/3920442.html)

**官网更名（合规）**
- CnEVPost: [Tesla renames FSD again in China ahead of software roll-out](https://cnevpost.com/2026/05/22/tesla-renames-fsd-again-in-china/)
- 观察者网: [迎合监管趋势，特斯拉FSD在华更名为"特斯拉辅助驾驶"](https://www.guancha.cn/qiche/2026_05_25_818288.shtml)
- 腾讯新闻: [特斯拉中国官网更新：FSD更名为"特斯拉辅助驾驶" 售价仍为6.4万元](https://news.qq.com/rain/a/20260524A05E4500)

**8·22 清单风波与辟谣**
- iChongqing: [Tesla's FSD China Rollout Faces New Uncertainty as China Disappears From Availability List](https://www.ichongqing.info/2026/08/27/teslas-fsd-china-rollout-faces-new-uncertainty-as-china-disappears-from-availability-list/)
- Electrek: [Tesla denies rumors it's abandoning 'Full Self-Driving' push in China](https://electrek.co/2026/08/26/tesla-denies-china-fsd-data-center-pullout/)
- CnEVPost: [Tesla denies rumors of China FSD pullout, but roll-out timing remains unclear](https://cnevpost.com/2026/08/26/tesla-denies-rumors-china-fsd-pullout/)
- 每经网: [数据中心关停？FSD入华无望？特斯拉中国辟谣](https://www.nbd.com.cn/articles/2026-08-26/4558286.html)
- IT之家: [特斯拉中国再回应 FSD 上海数据中心"撤离"传闻](https://www.ithome.com/0/994/711.htm)

**订阅制转型**
- 21财经/每经: [特斯拉FSD全面由买断制转向订阅制！港澳台地区买断版6月30日后下架，内地尚无明确时间表](https://www.nbd.com.cn/articles/2026-06-26/4438456.html)
- 新浪科技: [特斯拉韩国FSD月费719元，21日上线，中国949元？](https://finance.sina.com.cn/tech/roll/2026-08-10/doc-inimuzxp1281974.shtml)

**监管背景**
- 财新: [特斯拉FSD在中国暂停试用需获得监管部门批准](https://m.caixin.com/m/2025-03-25/102301993.html)
- 赛文交通网: [特斯拉FSD进入中国需要闯过的六道关口](https://www.7its.com/?m=home&c=View&a=index&aid=29940)

**财报口径**
- Investing.com: [Tesla Q2 2026 earnings call transcript](https://www.investing.com/news/transcripts/earnings-call-transcript-tesla-q2-2026-revenue-beats-eps-misses-as-stock-falls-93CH-4807216)
- Not a Tesla App: [Summary of Tesla's 2026 Q2 Earnings Call](https://www.notateslaapp.com/news/4481/summary-of-teslas-2026-q2-earnings-call-cybercab-fsd-ai4-and-more)
