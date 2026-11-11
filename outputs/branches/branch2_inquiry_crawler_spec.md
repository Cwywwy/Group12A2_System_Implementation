# 分支 2：年报问询函作为结果变量——数据可得性核验与爬虫设计

- 版本：v1（2026-11-11）
- 范围：`outputs/branches/positive_result_branches.md` 中"分支 2"的取数可行性部分
- 结论口径：所有接口均在本机实测（`Invoke-WebRequest`），未实测的部分明确标注"未能验证"
- 本文只做调研与设计，不改动任何既有脚本或数据文件

---

## 0. 结论摘要

| 问题 | 结论 |
| --- | --- |
| 能否自建爬虫 | **能**。深交所、北交所、上交所均有可用的结构化列表接口（JSON/JSONP），返回字段已含"公司代码 + 发函日期 + 函件类别"，无需解析 PDF 正文；巨潮可作跨市场兜底。 |
| 主源选择 | 深市 → 深交所列表接口（最干净）；北交所 → 北交所列表接口（自带函件类型字典）；**沪市 → 巨潮为主、上交所栏目为辅**（上交所监管问询栏目 2023 年后明显缺档，见 1.2 节证据）。 |
| 预计人日 | **4.5–5.0 人日**（1 人 × 6 小时/天）：爬虫 2.0 + 清洗 1.0 + 校验 1.0 + 并入现有管线 0.5–1.0。与既有估算 4–7 人日一致。 |
| 最大卡点 | **沪市覆盖不完整**：上交所"监管问询"栏目对 2023 年以后归档不全（3 家已知收函公司查得 0 条），必须用巨潮补齐；而巨潮 `searchkey` 检索结果里约 90% 是回复/延期回复公告，单页上限 30 条，2021 年"问询函"关键词共 246 页。 |
| 是否建议做 | **建议做**，但按"深市/北交所主源 + 巨潮补沪市"的双源方案，并把"沪市覆盖率 ≥ 90%"设为 go/no-go 闸门。若沪市交叉验证差异率 > 10%，退到"只做深市 + 北交所"（样本降至 3,917/6,569 ≈ 59.6%），或直接买 CNRDS/textdata。 |

---

## 1. 数据可得性核实

### 1.0 数据源入口一览

| 源 | 入口页 | 接口主机 | 本分支角色 |
| --- | --- | --- | --- |
| 上交所监管问询 | [sse.com.cn/disclosure/credibility/supervision/inquiries](https://www.sse.com.cn/disclosure/credibility/supervision/inquiries/) | `query.sse.com.cn` | 沪市辅助（栏目缺档） |
| 深交所监管问询 | [szse.cn/disclosure/supervision/inquire](https://www.szse.cn/disclosure/supervision/inquire/index.html) | `www.szse.cn` + `reportdocs.static.szse.cn` | 深市主源 |
| 北交所问询函件 | [bse.cn/disclosure/enquiry_letter.html](https://www.bse.cn/disclosure/enquiry_letter.html) | `www.bse.cn` | 北交所主源 |
| 巨潮资讯公告检索 | [cninfo.com.cn/new/commonUrl?url=disclosure/list/notice](https://www.cninfo.com.cn/new/commonUrl?url=disclosure/list/notice) | `www.cninfo.com.cn` + `static.cninfo.com.cn` | 沪市主源 / 跨市场兜底 |
| CNRDS CRID | [CNRDS 监管问询数据库-CRID（介绍）](https://cloud.tencent.com/developer/news/293112) | 订阅制 | 降级方案 C |
| textdata.cn | [监管问询函数据集](https://textdata.cn/blog/2023-04-17-china-a-market-inquiry-letter-datasets/) | 付费下载 | 降级方案 D |

### 1.1 本地已有的与缺的

| 位置 | 内容 | 对本分支的作用 |
| --- | --- | --- |
| `data/processed/manufacturing_sample_frame.csv` | 10,172 行，`symbol｜short_name｜fiscal_year｜industry_code_d｜industry_name_d｜end_date` | 事件表的分母；按年 2021=3,165、2022=3,404、2023=3,603；按板块见下表 |
| `data/processed/event_table.csv` | 8,140 行，含 `symbol｜fiscal_year｜audit_type｜opinion_class｜mod_opinion｜mod_opinion_wide｜auditor｜big4｜audit_fee｜announce_date｜violation_*_t1｜violation_*_t｜has_audit_record` | 现成控制变量 + `announce_date`（年报公告日）可直接用于 t 年报→t+1 函的时间锚点 |
| `data/raw/csmar_events/` | 仅 `FIN_Audit.xlsx`、`STK_Violation_Main.xlsx` | **没有问询函库**，必须自建或外购 |
| `data/raw/cninfo/` | 2021–2023 年报 PDF（含 8xxxxx/920xxx 北交所代码） | 可复用为"公司—代码"映射校验 |

样本按板块拆分（用于估算覆盖率分母）：

| 年报年度 | 合计 | 上交所（6 开头） | 深交所（0/3 开头） | 北交所/原新三板（8/4/92） |
| --- | --- | --- | --- | --- |
| 2021 | 3,165 | 1,275 | 1,759 | 131 |
| 2022 | 3,404 | 1,377 | 1,870 | 157 |
| 2023 | 3,603 | 1,443 | 1,956 | 204 |

样本期前移后（2020–2022 年报）实际可用分母为 **6,569** 个公司—年度（2021+2022）。

### 1.2 上交所（SSE）——JSONP 接口可用，但栏目有缺档

**接口（实测可用）**

```
GET https://query.sse.com.cn/commonSoaQuery.do
    ?jsonCallBack=cb
    &isPagination=true
    &pageHelp.pageSize=25
    &pageHelp.pageNo=1
    &pageHelp.beginPage=1
    &pageHelp.cacheSize=1
    &pageHelp.endPage=1
    &sqlId=BS_KCB_GGLL_NEW
    &siteId=28
    &channelId=10743,10744,10012
    &type=
    &stockcode=
    &extGGDL=2
    &createTime=2021-01-01%2000:00:00
    &createTimeEnd=2021-12-31%2023:59:59
    &order=createTime%7Cdesc,stockcode%7Casc
    &_=<毫秒时间戳>
```

| 项 | 实测结果 |
| --- | --- |
| 必需 Header | `Referer: https://www.sse.com.cn/disclosure/credibility/supervision/inquiries/`（缺 Referer 不可用）；UA 普通 Chrome 即可 |
| Cookie / 签名 | 不需要 Cookie，无动态签名 |
| 返回格式 | `application/json`，内容为 JSONP 包裹 `cb({...})`，去掉 `cb(` `)` 后 `ConvertFrom-Json` 可用 |
| 分页 | `pageHelp.pageSize` 默认 25（可调）；`pageHelp.{total,pageCount,pageNo,pageSize}` |
| 板块 | `type=4` 主板、`type=0` 科创板、留空=全部 |
| 函件类别 | `extGGDL`：`1`=问询函、`2`=定期报告信息披露监管问询函、`3`=重大资产重组预案审核意见函 |
| 栏目 | `channelId`：`10743`（问询函）、`10744`（定期报告）、`10012` |

**返回样例（截断到关键字段）**

```json
{"pageHelp":{"pageSize":25,"pageNo":1,"total":157,"pageCount":7,"beginPage":1,"endPage":1},
 "result":[{"stockcode":"600145","extGSJC":"*ST新亿","extWTFL":"问询函","extGGDL":"1",
            "docTitle":"关于对新疆亿路万源实业投资控股股份有限公司的问询函",
            "createTime":"2021-03-12 00:00:00","cmsOpDate":"2021-03-12 00:00:00",
            "docType":"pdf","docId":"10109905",
            "docURL":"www.sse.com.cn/disclosure/credibility/supervision/inquiries/opinion/c/10109905/files/3c129f7ebdb240b1bdf12f442a3d1bbf.pdf",
            "channelId":"10743","siteId":"28","extNAME":"..."}]}
```

`result` 每行 58 个字段，对本分支有用的 6 个已在上例中：`stockcode`、`extWTFL`（函件类型名）、`docTitle`、`createTime`（发函/挂网日期）、`docId`、`docURL`。

**PDF 可下载性**：`docURL` 补 `http://` 后 HEAD 返回 `200`、`application/pdf`、236,295 字节（无需 Cookie，只需 Referer）。

**实测条数（`pageHelp.total`）**

| 年度 | `extGGDL=1` 问询函 | `extGGDL=2` 定期报告类 |
| --- | --- | --- |
| 2020 | 148 | 162 |
| 2021 | 157 | 38 |
| 2022 | 147 | 33 |
| 2023 | 73 | 21 |
| 2024 | 50 | 20 |

**两项关键坑**

1. **时间参数必须带时分秒**。`createTime=2021-01-01`（只给日期）时接口不报错但返回 `total=0`——静默空结果，极易被误读为"该年无函件"。必须写成 `2021-01-01%2000:00:00`。
2. **2023 年后归档不完整（决定性证据）**。用 `stockcode` 单票查询：

   | 公司 | 全时段命中 | 说明 |
   | --- | --- | --- |
   | 600145 | 35 条 | 栏目对老公司有效 |
   | 600190 | 1 条（2018-12-07，重组类） | 稀疏 |
   | 600302 | 0 条 | 巨潮明确显示其收到 2023 年年报问询函并已答复 |
   | 688669 | 0 条 | 同上 |
   | 688793 | 0 条 | 同上 |

   → **上交所栏目不能作为沪市唯一主源**，否则会系统性低估事件率，且低估集中在最近年份，与"t 年报→t+1 函"的窗口正好重叠。

### 1.3 深交所（SZSE）——最优源，结构化字段几乎为订制

**接口（实测可用）**

```
GET https://www.szse.cn/api/report/ShowReport/data
    ?SHOWTYPE=JSON
    &CATALOGID=main_wxhj
    &TABKEY=tab2
    &PAGENO=1
    &txtStart=2021-01-01
    &txtEnd=2021-12-31
    &selecthjlb=年报问询函
    &random=0.31
```

| 项 | 实测结果 |
| --- | --- |
| 必需 Header | `Referer: https://www.szse.cn/disclosure/supervision/inquire/index.html` |
| Cookie / 签名 | 不需要；`random` 仅为防缓存，可任意小数 |
| 返回格式 | `application/json`，顶层数组 `[{metadata:{...},data:[...]}]`（非 JSONP） |
| 分页 | `PAGENO` 从 1 起；单页 **20** 条（`metadata.pagesize`）；`metadata.{recordcount,pagecount,pageno,catalogid,name}` |
| 板块 | `TABKEY=tab2` 主板、`tab3` 创业板（`tab1` 只回主板，**漏掉创业板一半样本**） |
| 过滤 | `txtZqdm`（代码或简称）、`selecthjlb`（函件类别）、`txtStart`、`txtEnd` |

**返回样例（完整行，仅 6 个字段）**

```json
{"metadata":{"catalogid":"main_wxhj","name":"主板监管问询","pageno":1,"pagesize":20,
             "recordcount":274,"pagecount":14},
 "data":[{"gsdm":"002269","gsjc":"美邦服饰","fhrq":"2024-06-01","hjlb":"年报问询函",
          "ck":"<a href='javascript:void(0)' encode-open='/UpFiles/zqjghj/sup_jghj_0001900F507C933FA6682E6CF2F0C03F.pdf'>详细内容</a>",
          "hfck":"<a href='javascript:void(0)' encode-open='/UpFiles/zqjghj/sup_jgdxhh_....pdf'>回复的公告</a>"}]}
```

`gsdm`=公司代码、`gsjc`=简称、`fhrq`=发函日期（`YYYY-MM-DD`）、`hjlb`=函件类别、`ck`=正函 PDF、`hfck`=**回复函 PDF（可能为空）**。所需三个字段（代码/日期/类型）全部结构化，`hfck` 空/非空可直接作为"是否已回复"标记。

`hjlb` 枚举（实测下拉框）：年报问询函、半年报问询函、非许可类重组问询函、许可类重组问询函、并购重组问询函、监管函（会计师事务所模板）、提请关注函、向中介机构发函、关注函、公司部函、问询函。

**PDF 直链（已验证）**：`encode-open` 的相对路径需拼到 **`https://reportdocs.static.szse.cn`**：

```
https://reportdocs.static.szse.cn/UpFiles/zqjghj/sup_jghj_0001900F507C933FA6682E6CF2F0C03F.pdf
→ HEAD 200, application/pdf, 168,255 字节
```

（同一路径拼在 `www.szse.cn`、`disc.static.szse.cn` 下均 404，只有 `reportdocs.static.szse.cn` 有效。）

**实测条数（`selecthjlb=年报问询函`）**

| 年度 | 主板 tab2 | 创业板 tab3 | 合计 |
| --- | --- | --- | --- |
| 2021 | 274 | 221 | 495 |
| 2022 | 266 | 198 | 464 |
| 2023 | 241 | 185 | 426 |
| 2024 | 147 | 177 | 324 |
| 2025 | 0 | 0 | 0 |

全类型（不限 `selecthjlb`）主板累计 7,389 条 = 370 页（20 条/页）。

### 1.4 北交所（BSE）——JSONP over POST，需先建会话

**接口（实测可用）**

```
POST https://www.bse.cn/inquiryLetterController/infoResultse.do
Content-Type: application/x-www-form-urlencoded

page=0&sortfield=bean.send_date&sorttype=desc&letterType=&companyCode=
&startTime=2021-01-01&endTime=2021-12-31&keyword=&xxfcbj=2&isNewThree=3
&status=0&callback=cb
```

| 项 | 实测结果 |
| --- | --- |
| 会话 | 必须先 `GET https://www.bse.cn/disclosure/enquiry_letter.html`（下发 `HMY_JC`/`C3VK`/`HMF_CI`），否则返回空 |
| Header | `Referer: https://www.bse.cn/disclosure/enquiry_letter.html` |
| 返回格式 | JSONP：`cb([{"page":{"content":[...],"totalElements":N}}])` |
| 分页 | `page` **从 0 起**，20 条/页 |
| 编码 | 响应声明 GBK，`Invoke-WebRequest` 已正确解码，直接取 `$r.Content` 即可 |

**返回样例（关键字段）**

```json
{"companyCode":"430047","companyName":"诺思兰德",
 "letterType":"3","letterTypeValue":"年报问询函",
 "letterNumber":"...","sendDate":{"date":15,"time":0,"year":2022,"month":5,...},
 "letterContent":"/uploads/1/file/public/202205/....pdf","letterContentName":"...",
 "companyReply":"/uploads/1/file/public/202206/....pdf","companyReplyName":"...",
 "year":"2022","createTime":{...}}
```

**函件类型字典**（`POST https://www.bse.cn/inquiryLetterController/getLetterType.do`，form：`page=0&sortfield=bean.create_time&sorttype=desc&status=0&callback=cb`）：年报问询函=**3**、半年报问询函=5、季报问询函=8、问询函=4、并购重组类问询函=7。→ 北交所可按 `letterType=3` 直接过滤，**无需标题正则**。

**实测条数**：2021=3、2022=26、2023=53、2024=72（体量极小，一次全量拉完即可）。

### 1.5 巨潮资讯（cninfo）——跨市场兜底，回复函污染严重

**接口（实测可用）**

```
POST https://www.cninfo.com.cn/new/hisAnnouncement/query
Content-Type: application/x-www-form-urlencoded; charset=UTF-8

pageNum=1&pageSize=30&column=szse&tabName=fulltext&plate=&stock=&searchkey=年报问询函
&secid=&category=&trade=&seDate=2021-01-01~2021-12-31&sortName=&sortType=&isHLtitle=true
```

| 项 | 实测结果 |
| --- | --- |
| 必需 Header | `Referer: https://www.cninfo.com.cn/new/commonUrl?url=disclosure/list/notice`、`X-Requested-With: XMLHttpRequest` |
| Cookie / 签名 | 不需要；`column=szse` 可查沪市（配 `plate=sh`） |
| 返回格式 | `application/json`（`totalAnnouncement`、`totalpages`、`hasMore`、`announcements[]`） |
| 分页 | `pageSize` **上限 30**（传 50/100 仍只回 30）；`pageNum` 从 1 起 |
| 过滤 | `plate`=空/`sh`/`sz`、`searchkey`（标题模糊匹配）、`seDate=起~止`、`stock`/`secid`（单票） |

**返回样例（关键字段）**

```json
{"totalAnnouncement":2344,"totalpages":79,"hasMore":true,
 "announcements":[{"id":null,"secCode":"600052","secName":"浙江广厦","orgId":"gssh0600052",
  "announcementId":"1212062444",
  "announcementTitle":"关于收到上海证券交易所监管工作函的公告",
  "announcementTime":1640678400000,"adjunctUrl":"finalpage/2021-12-31/1212062444.PDF",
  "adjunctSize":142,"adjunctType":"PDF","columnId":"1001","announcementType":"..."}]}
```

附件直链 `https://static.cninfo.com.cn/{adjunctUrl}` HEAD 返回 `200`、`application/pdf`、140,943 字节，**无需 Cookie**。

**实测条数（`searchkey=年报问询函`，含回复函与延期回复）**

| 年度 | 合计 | 沪市（`plate=sh`） | 深市 |
| --- | --- | --- | --- |
| 2021 | 2,344 | 402 | 1,936 |
| 2022 | 2,380 | 521 | 1,817 |
| 2023 | 2,102 | 518 | 1,511 |
| 2024 | 1,717 | 620 | 961 |

`searchkey=问询函` 时 2021 年共 7,399 条 = **246 页**（按 30 条/页）。

**回复函污染率（实测）**：2021 年 `searchkey=年报问询函` 第 1 页 30 条中，**27 条**标题含"回复/延期回复/核查意见"，仅 3 条是原始问询函。→ 巨潮必须做标题净化，且抽取能力取决于标题规范程度，不能当唯一主源。

### 1.6 商业源（未采购，仅核实字段与覆盖）

| 源 | 规模 | 字段 | 备注 |
| --- | --- | --- | --- |
| [CNRDS 监管问询数据库-CRID](https://cloud.tencent.com/developer/news/293112) | 2014-12 起 | 股票代码、公司简称、函件类别、问询标题、**问询内容**、**公司回复内容**、发函日期、限期回复日期、公司回复日期 | 官方手册称已从 PDF 抽取并结构化；有校内权限则半小时可拿全量。见 [CNRDS 产品手册 2023 版](https://www.lib.szu.edu.cn/sites/szulib/files/er/%E4%B8%AD%E5%9B%BD%E7%A0%94%E7%A9%B6%E6%95%B0%E6%8D%AE%E6%9C%8D%E5%8A%A1%E5%B9%B3%E5%8F%B0%28CNRDS%29%E4%BA%A7%E5%93%81%E6%89%8B%E5%86%8C2023%E7%89%88.pdf) |
| [textdata.cn 监管问询函数据集](https://textdata.cn/blog/2023-04-17-china-a-market-inquiry-letter-datasets/) | 14,730 条，2014.12–2023.12，xlsx 约 159 MB | 同上量级 | 付费；覆盖期正好含 2021–2024 事件窗 |

### 1.7 反爬与合规评估

| 站点 | 验证码 | IP 限流 | 动态签名 | 登录 | 结论 |
| --- | --- | --- | --- | --- | --- |
| 上交所 query.sse.com.cn | 无 | 未触发（数十次串行请求正常） | 无 | 无 | 只需 Referer；建议间隔 ≥1.5 s |
| 深交所 szse.cn | 无 | 未触发 | 无（`random` 是防缓存） | 无 | 最友好，建议间隔 ≥1 s |
| 北交所 bse.cn | 无 | 未触发 | 无 | 无（但要页面会话 Cookie） | 需 `requests.Session` 先访问列表页 |
| 巨潮 cninfo.com.cn | 无 | 未触发 | 无 | 无 | 高频会返回空 `announcements`，建议 ≥2 s 且遇空重试 |
| reportdocs / static.cninfo | 无 | 未触发 | 无 | 无 | PDF 直链可直下 |

合规：均为公开披露信息，仅用于学术研究；控制并发为 1 请求/站点、夜间跑批、总量 < 3,000 请求/天，不触发任何限流阈值。

### 1.8 PDF 字段可抽性（结论：本设计不需要解析 PDF）

| 需要的字段 | 深交所 | 北交所 | 上交所 | 巨潮 |
| --- | --- | --- | --- | --- |
| 公司代码 | `gsdm` | `companyCode` | `stockcode` | `secCode` |
| 发函日期 | `fhrq` | `sendDate` | `createTime` | `announcementTime` |
| 函件类型 | `hjlb` | `letterTypeValue` | `extWTFL` + `extGGDL` | 仅标题文本 |
| 是否针对年报 | `hjlb=年报问询函` 直接判定 | `letterType=3` 直接判定 | `extGGDL=2` 或标题含"年度报告" | 需正则，必要时回落到 PDF 首页 |

→ 三家交易所**全部结构化**给出前三个字段；"是否针对年报"在深、北两市可由类型字段直接判定，沪市需 `extGGDL`+标题双重判断。PDF 解析只作为**沪市标题歧义时的兜底**（下载首页抽"年度报告"字样与年份），不进入主链路。

### 1.9 覆盖率实测推算

按交易所列表实测条数推算"每年发出的年报类问询函"基数：

| 事件年（针对 t 年报） | 深市 | 北交所 | 沪市（上交所栏目，仅下限） | 合计（下限） |
| --- | --- | --- | --- | --- |
| 2021（t=2020） | 495 | 3 | 157+38=195 | ≈693 |
| 2022（t=2021） | 464 | 26 | 147+33=180 | ≈670 |
| 2023（t=2022） | 426 | 53 | 73+21=94 | ≈573（沪市缺档，实际更高） |
| 2024（t=2023） | 324 | 72 | 50+20=70 | ≈466 |

全 A 股 2021 年约 4,600 家，事件率下限 ≈ 670/4,600 ≈ **14.6%**，落在文献常见的 12%–18% 区间内 → 与验收标准自洽。注意 2023 行的沪市数字明显偏低（缺档），说明**沪市必须用巨潮补**，否则事件率会被系统性低估。

---

## 2. 可执行爬虫设计

### 2.1 模块划分

| 模块 | 文件（建议） | 职责 | 输入 | 输出 | 状态 |
| --- | --- | --- | --- | --- | --- |
| M1 深市采集 | `scripts/run_14a_crawl_szse_inquiry.py` | 按 `TABKEY∈{tab2,tab3}` × 年度 分页拉全类型 | 年度区间 | `data/raw/inquiry/szse/{year}/page_*.jsonl` | 新增 |
| M2 沪市采集 | `scripts/run_14b_crawl_sse_inquiry.py` | `channelId`×`extGGDL`×年度，带完整时间戳 | 年度区间 | `data/raw/inquiry/sse/{year}/page_*.jsonl` | 新增 |
| M3 北交所采集 | `scripts/run_14c_crawl_bse_inquiry.py` | 先建会话，再按 `letterType` 分页（`page` 从 0） | 年度区间 | `data/raw/inquiry/bse/{year}/page_*.jsonl` | 新增 |
| M4 巨潮补采 | `scripts/run_14d_crawl_cninfo_inquiry.py` | 关键词×年度×板块扫，外加"缺票补齐"单票查询 | 缺票清单 | `data/raw/inquiry/cninfo/{year}/page_*.jsonl` | 新增 |
| M5 归一与去重 | `scripts/run_15_build_inquiry_events.py` | 四源合并、字段映射、去重、标题分类、回复剔除 | M1–M4 | `data/interim/inquiry_events.csv` | 新增 |
| M6 事件表构建 | `scripts/run_15b_build_inquiry_event_table.py` | t 年报→t+1 函对齐、右删失、并入既有控制变量 | M5 + `event_table.csv` | `data/processed/inquiry_event_table.csv` | 新增 |
| M7 校验 | `scripts/run_16_qc_inquiry.py` | 覆盖率、交叉源差异、抽样清单、已知阳性对照 | M5/M6 | `outputs/tables/inquiry_qc.md` | 新增 |

> 现有流水线（`run_01`…`run_13`、`run_99_full_pipeline.py`）**不改动**，M1–M7 作为独立分支挂到 `run_99` 的可选阶段。

### 2.2 请求节流与重试

| 参数 | 取值 | 说明 |
| --- | --- | --- |
| 单站点并发 | 1 | 串行，避免触发风控 |
| 请求间隔 | SZSE 1.0 s / SSE 1.5 s / BSE 1.5 s / cninfo 2.0 s（±30% 抖动） | 抖动降低指纹特征 |
| 超时 / 重试 | 30 s；指数退避 2→4→8→16 s，最多 5 次 | 仅对 5xx、超时、空 `announcements` 重试 |
| 限流信号 | 403/429/验证码页 → 睡眠 120 s 后单次重试；连续 3 次失败 → 中止并保留断点 | 不硬扛 |
| UA | 固定一个 Chrome UA | 不轮换，避免反而异常 |
| 日预算 | < 3,000 请求 | 全量四源约 2,000 请求，一晚可跑完 |

### 2.3 增量落盘与断点

- **落盘粒度**：`data/raw/inquiry/{source}/{year}/page_{pageno:04d}.jsonl`，一页一文件，原样保存响应体（含 `metadata`），**不做就地改写**。
- **断点文件**：`data/raw/inquiry/{source}/_checkpoint.json`：
  ```json
  {"source":"szse","tabkey":"tab2","year":2021,"last_page":14,"pagecount":14,
   "recordcount":274,"finished":true,"updated_at":"2026-11-11T22:10:03"}
  ```
- **幂等**：启动时读断点，跳过已有 `page_*.jsonl` 且可正常 `json.loads` 的页；`finished=true` 直接跳过该 (source, tab, year) 组合。重跑只补缺口。
- **失败记录**：`_failed.jsonl` 追加 `{url, params, ts, err}`，收尾时单独重试。

### 2.4 归一化字段表（`data/interim/inquiry_events.csv`）

| 字段 | 类型 | 来源映射 |
| --- | --- | --- |
| `sec_code` | str(6) | `gsdm` / `companyCode` / `stockcode` / `secCode` |
| `sec_name` | str | `gsjc` / `companyName` / `extGSJC` / `secName` |
| `send_date` | date | `fhrq` / `sendDate{year,month,date}` / `createTime[:10]` / `announcementTime` |
| `letter_type_raw` | str | `hjlb` / `letterTypeValue` / `extWTFL` / 标题推断 |
| `letter_type_norm` | str | {年报类, 半年报类, 季报类, 重组类, 再融资类, 其他/未知} |
| `title` | str | `letterContentName` / `docTitle` / `announcementTitle` |
| `doc_url` | str | `reportdocs.static.szse.cn+ck` / `bse.cn+letterContent` / `docURL` / `static.cninfo.com.cn+adjunctUrl` |
| `reply_url` | str\|null | `hfck` / `companyReply` / 空 |
| `has_reply` | bool | `reply_url` 非空 |
| `source` | str | szse / sse / bse / cninfo |
| `source_rank` | int | szse=1, bse=2, sse=3, cninfo=4（去重时留最小） |
| `crawl_ts` | datetime | 采集时刻，便于追溯 |

### 2.5 去重

- **主键**：`(sec_code, letter_type_norm, send_date)`；同一主键多条时按 `source_rank` 保留交易所官方记录，其余写入 `dup_log`。
- **次级判重**：`(sec_code, send_date)` 且标题相似度 > 0.9 → 视为同函（应对同一函件在不同源日期差 1 天的情况，例如挂网日 vs 发函日）。日期容差 ±2 天。
- **预期去重率**：深市/北交所与巨潮重叠处约 15%–25%（回复函另计）。

### 2.6 标题/类型分类规则

优先用结构化类型字段；仅当字段缺失或为"问询函/关注函"这类泛型时回落标题正则。**判定顺序即优先级**（先剔除、再细分）：

| 顺序 | 标签 | 正则（兼顾大小写与全角） | 处理 |
| --- | --- | --- | --- |
| 0 | 回复函 | `回复｜答复｜延期回复｜核查意见｜专项说明｜之法律意见书` | **剔除**（不进入事件） |
| 1 | 重组类 | `重组｜并购｜重大资产｜发行股份购买资产｜换股吸收合并` | 剔除/安慰剂 |
| 2 | 再融资类 | `向特定对象发行｜非公开发行｜可转债｜再融资｜配股` | 剔除 |
| 3 | 半年报类 | `半年报｜半年度报告` | 剔除 |
| 4 | 季报类 | `季报｜季度报告` | 剔除 |
| 5 | 年报类 | `年度报告｜年报｜定期报告.*信息披露.*问询` 且不含上面 1–4 | **命中事件** |
| 6 | 泛型问询 | `问询函｜关注函｜监管工作函｜公司部函` 无年份信息 | 待人工/PDF 兜底判定 |

结构化字段优先映射：

| 源 | 年报类直接判定条件 |
| --- | --- |
| 深交所 | `hjlb == "年报问询函"` |
| 北交所 | `letterType == "3"` |
| 上交所 | `extGGDL == "2"` 且标题不含半年报/重组/融资关键词 |
| 巨潮 | 仅标题；`年度报告`/`年报` 命中且不含回复/重组/半年报关键词 |

### 2.7 回复函剔除规则

1. 交易所结构化字段：深市 `hfck` 指向的文件属回复公告，**正函事件只看 `ck`**；北交所同理只看 `letterContent`，`companyReply` 只作 `has_reply` 标记。
2. 巨潮侧：`announcementTitle` 命中第 2.6 节第 0 行正则即剔除（实测第 1 页 27/30 命中）。
3. 公司自行发布的"关于收到问询函的公告"**保留为辅助召回**（可补交易所缺档），但标记 `source=cninfo_receipt`，在稳健性检验中开关。
4. 剔除统计必须落表：`outputs/tables/inquiry_qc.md` 中报"剔除回复函 N 条 / 保留正函 M 条 / 剔除率"。

### 2.8 时间对齐与右删失

- **事件定义**：`inquiry_{i,t} = 1` 当且仅当存在一条 `letter_type_norm=年报类`、`sec_code=i`、`send_date ∈ (announce_date_{i,t}, announce_date_{i,t} + 300 天]` 的函件，且该函针对 t 年年报（标题含 t 年份或无年份时按窗口推断）。
- **主窗口**：年报公告日 +1 天 → +300 天（覆盖绝大多数"年报后 4–9 个月"的发函节奏）。
- **稳健窗口**：① 自然年 `[t+1-01-01, t+1-12-31]`；② `(announce_date, announce_date+180]`；③ 剔除 t 年内已收任何函件的公司。
- **右删失**：t=2022 的函件可能延至 2024 年才发出（延期回复、二次问询）。处理：**采集截止日固定为 2025-06-30**，把 2023 年报（t=2023）整体排除，只用 t=2020/2021/2022（对应 2021–2024 发函）。若某 t 年样本在截止日仍无函件，记 0 并在文中说明"右删失概率 < 3%（以 2021 年函件在 2023 年后的补发量实测校准）"。
- **反向因果**：只用 t 年年报 MD&A 文本预测 t+1 年函件；控制变量全部取 t 年值；另加 t+2 安慰剂（t 文本不应预测 t+2 函）与"剔除 t 年已收函"样本。

### 2.9 与现有管线集成

| 步骤 | 命令（拟） | 产出 |
| --- | --- | --- |
| 采集 | `python scripts/run_14a..14d_*.py --years 2021 2022 2023 2024` | `data/raw/inquiry/**` |
| 归一 | `python scripts/run_15_build_inquiry_events.py` | `data/interim/inquiry_events.csv` |
| 事件表 | `python scripts/run_15b_build_inquiry_event_table.py` | `data/processed/inquiry_event_table.csv`（6,569 行 × 事件列） |
| 校验 | `python scripts/run_16_qc_inquiry.py` | `outputs/tables/inquiry_qc.md` |
| 建模 | 复用 `run_07b` 框架，换 `y=inquiry_{i,t+1}` | `outputs/tables/branch2_*` |

---

## 3. 成本与风险

### 3.1 工作量（1 人 × 6 小时/天）

| 工作包 | 内容 | 人日 |
| --- | --- | --- |
| 爬虫开发 | 4 个采集模块 + 节流/重试/断点 + 首次全量跑通 | 2.0 |
| 清洗归一 | 字段映射、去重、标题分类、回复剔除、异常值排查 | 1.0 |
| 校对各 | 交叉源比对（深市 vs 巨潮）、30 条人工抽样、已知阳性对照、覆盖率报告 | 1.0 |
| 并入管线 | 事件表构建、与 `event_table.csv` 合并、跑描述统计与 AUC 基线 | 0.5–1.0 |
| **合计** | | **4.5–5.0** |

若已有 CNRDS 权限：取数 0.5 天 + 清洗校验 1.5 天 = **2.0 人日**，但需额外核对 2023+ 覆盖与"是否年报类"字段口径，故实际节省约 2.5 人日。

### 3.2 三个最可能的卡点

| # | 卡点 | 证据 | 后果 | 应对 |
| --- | --- | --- | --- | --- |
| 1 | **沪市覆盖不完整** | 上交所栏目 600302/688669/688793 在 2024 年 `total=0`，而巨潮显示其已收 2023 年报问询函；2023 年沪市仅 94 条，明显低于深市 426 条 | 沪市事件被系统性低估，行业×年 FE 下沪市系数失真 | 巨潮按"缺票清单"逐票补；沪市覆盖率 ≥90% 作为闸门 |
| 2 | **巨潮回复函污染 + 分页成本** | 2021 年报问询函第 1 页 30 条中 27 条为回复；`pageSize` 上限 30，`searchkey=问询函` 246 页 | 误把回复当事件 → 事件率虚高；页数多 → 工时与风控风险 | 只对"交易所未命中"的票做单票 `stock`/`secid` 查询（3,694 票分批），避免全量关键词翻页 |
| 3 | **"是否针对年报"的判定缺口** | 上交所/巨潮部分标题为"定期报告信息披露监管问询函"或"问询函"，不含年份 | 事件标签噪声，直接影响 AUC | 优先用 `extGGDL=2`；无年份时按发函日落在年报公告后 300 天内推断；仍歧义者下载 PDF 首页抽"年度报告"字样与年份（预计 < 5% 样本） |

### 3.3 降级方案

| 方案 | 触发条件 | 覆盖 | 代价 |
| --- | --- | --- | --- |
| A. 深市 + 北交所，弃沪市 | 沪市交叉验证差异率 >10% 且时间不足 | 3,917/6,569 ≈ **59.6%** 样本（完全外生，仍可做行业×年 FE） | 样本减 40%，外部效度下降，需在限制中说明 |
| B. 只做 2022 单年 | 工时压缩到 2 人日 | 3,404 行，事件约 450–500 | 无法做年度 FE 的时序稳健性 |
| C. 买 CNRDS CRID | 有校内订阅 | 全量 + 问询内容文本（可做函件强度/问题分类） | 0.5 天取数；需核对 2023+ 覆盖 |
| D. 买 textdata.cn | 无订阅但预算允许 | 14,730 条至 2023.12（含 2024 事件窗） | 付费；字段口径需自行核对 |

---

## 4. 验收标准（可量化）

| # | 指标 | 阈值 | 检验方法 |
| --- | --- | --- | --- |
| 1 | 覆盖率（交易所主源） | 2021–2022 年报制造业样本中 **≥ 90%** 的公司被至少一个源覆盖（有记录或确认无函） | `run_16_qc_inquiry.py` 输出覆盖矩阵 |
| 2 | 交叉源一致率 | 深市"深交所 vs 巨潮"在同一 (代码, 日期±2 天, 年报类) 上差异率 **≤ 5%** | 集合差集统计 |
| 3 | 人工抽样一致率 | 随机 30 条，"代码/发函日期/函件类型/是否年报类"四项全对 **≥ 95%**（即 ≤1 条错） | 双人独立核对，记录分歧 |
| 4 | 已知阳性召回 | 3 家已知收函公司（600302、688669、688793 对应年度）**全部命中**；再补 10 家巨潮随机抽出的沪市公司，召回 ≥ 9/10 | 对照清单 |
| 5 | 事件率 | 落在 **12%–18%**（分市场：深市约 18%–19%，沪市 8%–12%，全样本 13%–16%） | 描述统计；偏离即回查沪市缺档 |
| 6 | 去重后唯一性 | `(sec_code, letter_type_norm, send_date)` 重复率 **= 0** | 主键断言 |
| 7 | 回复函误入 | 事件集内标题含"回复/延期/核查意见"的比例 **≤ 1%** | 正则复扫 |
| 8 | 可复现 | 全量重跑 ≤ 3 小时；断点续跑丢页 **= 0**；`_checkpoint.json` 与落盘文件数一致 | 清空一页后重跑验证 |

**go/no-go 闸门**：指标 1、3、4、5 任一不达标即暂停建模，先修数据；指标 2 不达标 → 走降级方案 A。

---

## 5. 文献衔接（用于方法章节引用）

| # | 文献 | 期刊/年份 | 事件窗口定义 | 反向因果处理 | 对本项目的用法 |
| --- | --- | --- | --- | --- | --- |
| 1 | Cassell, C. A., Dreher, L. M., & Myers, L. A. — *Reviewing the SEC's Review Process: 10-K Comment Letters and the Cost of Remediation* | The Accounting Review, 2013, 88(6): 1875–1908 | 以财年 t 的 10-K 提交为起点，考察"是否收到评论函"及其整改成本；因变量为 0/1 | 把评论函视为 t 期披露质量的**结果**，用 t 期公司特征（规模、亏损、审计所规模）解释收函概率 | 本项目"收函概率"建模范式的直接模板；控制变量集参考其设定 |
| 2 | Johnston, R., & Petacchi, R. — *Regulatory Oversight of Financial Reporting: SEC Comment Letters* | Contemporary Accounting Research, 2017, 34(2): 1128–1155 | 函件公开日 t=0，看 `[0,3]` 与 `[0,90]` 的 CAR 与后续披露修正 | 把函件作为**信息事件**（处理变量），用事件窗隔离同期混杂；承认函件本身内生于披露质量 | 说明"函件是结果变量而非外生冲击"的边界，为本项目的方向固定提供依据 |
| 3 | Bozanic, Z., Dietrich, J. R., & Johnson, B. A. — *SEC Comment Letters and Firm Disclosure* | Journal of Accounting and Public Policy, 2017, 36(5) | 函件后 1–2 年的披露改善（信息不对称、诉讼风险） | 用函件前趋势与公司固定效应吸收选择效应 | 支持"t 文本 → t+1 函"的时序设定，并提示需控制 t 年已收函 |
| 4 | 陈运森、邓祎璐、李哲 —《非处罚性监管具有信息含量吗？——基于问询函的证据》 | 《金融研究》2018 年第 4 期 | 问询函公告日为事件日，`[-1,+1]`、`[0,3]` 超额收益 | 事件研究法，以市场反应识别信息含量，规避反向因果 | 中文文献中"问询函=监管事件"的标准定义来源 |
| 5 | 陈运森 —《证券交易所一线监管的有效性研究：基于财务报告问询函的证据》 | 《管理世界》2019 年第 3 期 | `INQUIRY`：**当年或前一年收到问询函 = 1**，否则 0 | 用 t 期函件解释 t+1 盈余管理，配 PSM 与前置趋势检验 | 给出可直接复用的 0/1 定义；其"当年或前一年"口径提醒我们**必须收紧到"仅 t+1 年、仅年报类"**，否则会与他文口径混淆 |
| 6（补充） | 《财务问询函能够提高年报可读性吗？》 | 上海财经大学期刊社（《财经研究》），2020 | 收函年 t → 次年 t+1 年报可读性 | 明确"收函 → 次年文本改善"的通道 | **反向因果的直接依据**：证明文本与函件互为因果，故本项目只能固定 t 文本 → t+1 函，并把"剔除 t 年已收函"列为必备稳健性 |
| 7（补充，项目内已引） | Yang, Huang & Cai | Emerging Markets Finance and Trade, 2022, 58(2): 417–427 | — | — | `positive_result_branches.md` 已引用，作为"中文语境文本特征—监管关注"的先例 |

> 标注：以上 1–7 均为**未获取全文**（仅摘要/正文片段/二次引用核实）。第 5 篇的 `INQUIRY` 定义与第 6 篇的"收函→次年可读性"结论已在公开页面正文中直接核对到，可直接引用；其余在写方法章节前建议补 PDF 核对页码。

**写作提示（方法章节可直接用）**：中文文献里"文本特征 → 收函概率"的正向预测研究很少，绝大多数是"收函 → 文本变化"。这既是本项目的边际贡献点，也是必须在文中显式处理的方向性问题——所以事件窗必须锁死在 t 年年报公告之后，且样本要剔除 t 年内已收函的公司。

---

## 附录 A：已验证请求示例（curl 形态，便于复现）

```bash
# 深交所：2021 年年报问询函（主板）
curl -s 'https://www.szse.cn/api/report/ShowReport/data?SHOWTYPE=JSON&CATALOGID=main_wxhj&TABKEY=tab2&PAGENO=1&txtStart=2021-01-01&txtEnd=2021-12-31&selecthjlb=%E5%B9%B4%E6%8A%A5%E9%97%AE%E8%AF%A2%E5%87%BD&random=0.31' \
  -H 'Referer: https://www.szse.cn/disclosure/supervision/inquire/index.html' \
  -H 'User-Agent: Mozilla/5.0 ... Chrome/131.0.0.0 Safari/537.36'

# 上交所：2021 年定期报告类（注意时间戳必须带时分秒）
curl -s 'https://query.sse.com.cn/commonSoaQuery.do?jsonCallBack=cb&isPagination=true&pageHelp.pageSize=25&pageHelp.pageNo=1&pageHelp.beginPage=1&pageHelp.cacheSize=1&pageHelp.endPage=1&sqlId=BS_KCB_GGLL_NEW&siteId=28&channelId=10743,10744,10012&type=&stockcode=&extGGDL=2&createTime=2021-01-01%2000:00:00&createTimeEnd=2021-12-31%2023:59:59&order=createTime%7Cdesc,stockcode%7Casc&_=1700000000000' \
  -H 'Referer: https://www.sse.com.cn/disclosure/credibility/supervision/inquiries/'

# 北交所：2021 年全部类型（先访问页面拿 Cookie）
curl -s -c jar.txt 'https://www.bse.cn/disclosure/enquiry_letter.html' -H 'User-Agent: Mozilla/5.0 ...'
curl -s -b jar.txt -X POST 'https://www.bse.cn/inquiryLetterController/infoResultse.do' \
  -H 'Referer: https://www.bse.cn/disclosure/enquiry_letter.html' \
  --data 'page=0&sortfield=bean.send_date&sorttype=desc&letterType=&companyCode=&startTime=2021-01-01&endTime=2021-12-31&keyword=&xxfcbj=2&isNewThree=3&status=0&callback=cb'

# 巨潮：沪市 2021 年"年报问询函"关键词第 1 页
curl -s 'https://www.cninfo.com.cn/new/hisAnnouncement/query' \
  -H 'Referer: https://www.cninfo.com.cn/new/commonUrl?url=disclosure/list/notice' \
  -H 'X-Requested-With: XMLHttpRequest' \
  -H 'Content-Type: application/x-www-form-urlencoded; charset=UTF-8' \
  --data 'pageNum=1&pageSize=30&column=szse&tabName=fulltext&plate=sh&stock=&searchkey=%E5%B9%B4%E6%8A%A5%E9%97%AE%E8%AF%A2%E5%87%BD&secid=&category=&trade=&seDate=2021-01-01~2021-12-31&sortName=&sortType=&isHLtitle=true'
```

## 附录 B：未能验证的事项

| 事项 | 状态 | 影响 |
| --- | --- | --- |
| 巨潮 `secid` 单票查询的完整参数（`orgId` 获取方式） | 仅验证 `stock`+`searchkey` 可用，`secid` 未完整验证 | 单票补齐可能需先取 `orgId`（可从任一公告的 `orgId` 字段拿到） |
| 上交所 `docURL` 之外的问询函附件类型（如 zip） | 未发现 zip | 无 |
| 巨潮附件为扫描件的比例 | 未统计 | 若沪市需 PDF 抽年份，扫描件需 OCR（预计少数） |
| CNRDS/textdata 的实际字段缺失率与 2023+ 覆盖 | 无订阅，未验证 | 决定降级方案 C/D 的可行性 |
