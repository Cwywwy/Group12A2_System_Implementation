# CSMAR 数据下载指引（中文版 + English Version）

适用项目：Group12A2 · Screening Financial Disclosure Risk through Textual-Financial Feature Fusion and Explainable Anomaly Detection（2021–2023 中国 A 股制造业）。

目标数据：**财务三表（2020–2023 年，合并报表口径）**。2020 年用于计算增长率与 Beneish M-Score 的前一年值。

---

## 中文版

### 1. 进入网站

打开浏览器（推荐 Chrome 或 Edge），访问 **https://data.csmar.com**（CSMAR 数据平台）。若浏览器跳转到旧域名 cn.gtadata.com 属正常现象，平台会自动重定向。

### 2. 学校接口登录

二选一：

- **方式 A：校园网直连（推荐）**
  连接学校校园网（校内 Wi-Fi、有线网络或学校 VPN）→ 打开 data.csmar.com → 右上角点击「登录」→ 选择「机构用户 / IP 登录」。CSMAR 会按出口 IP 自动识别学校机构；识别成功后右上角会显示学校名称。
- **方式 B：图书馆数据库导航**
  打开学校图书馆官网 → 「数据库 / 电子资源导航」→ 搜索「CSMAR」或「国泰安」→ 点击图书馆提供的访问链接进入（自动携带机构权限；部分学校走统一身份认证 SSO / CARSI，用学号登录即可）。

**验证登录成功**：页面右上角出现学校机构名称。若提示无权限，请确认当前使用校内网络后重试。

### 3. 进入数据中心，定位三张财务表

首页顶部导航「**数据中心**」→「**公司研究系列**」→「**财务报表**」，本项目需要下载三张表：

| 表名 | 内容 | 口径 |
| --- | --- | --- |
| FS_Combas | 财务报表-资产负债表 | 合并报表 |
| FS_Comins | 财务报表-利润表 | 合并报表 |
| FS_Comscfd | 财务报表-现金流量表（直接法） | 合并报表 |

> 可选加分项：在数据中心搜索框输入「审计意见」，下载审计意见表（AuditOp），可作为外部基准之一。

### 4. 时间范围与口径设置

- **时间区间**：2020-01-01 至 2023-12-31（选择「报告期」/「年报」口径，即每年 12-31 这一期）。
- **报表类型**：合并报表。
- **币种**：人民币。

### 5. 勾选字段（在表内「字段检索」搜索框按关键词勾选）

**资产负债表 FS_Combas**

| 关键词（中文） | 用途 |
| --- | --- |
| 资产总计 | ROA 分母、总应计分母 |
| 负债合计 | 资产负债率 |
| 流动资产合计 | Beneish AQI |
| 流动负债合计 | Beneish LVGI |
| 应收账款净额 | 应收账款周转率、Beneish DSRI |
| 固定资产净额 | Beneish DEPI / AQI |
| 长期借款 | Beneish LVGI |

**利润表 FS_Comins**

| 关键词（中文） | 用途 |
| --- | --- |
| 营业收入 | 营收增长率、Beneish SGI/DSRI |
| 营业成本 | 毛利率、Beneish GMI |
| 销售费用 | Beneish SGAI |
| 管理费用 | Beneish SGAI |
| 净利润 | Beneish TATA、基准 |

**现金流量表 FS_Comscfd**

| 关键词（中文） | 用途 |
| --- | --- |
| 经营活动产生的现金流量净额 | 经营现金流/资产、Beneish TATA |
| 固定资产折旧 | Beneish DEPI（补充资料部分） |

> 字段代码以每张表下载时附带的《数据说明》为准，下载后我会在特征字典中固化具体字段名与公式，保证可复现。

### 6. 下载与保存

1. 点击「**下载**」→ 文件格式选 **Excel（.xlsx）**、打包下载。
2. 若提示超出单次下载记录上限：**按年份分段下载**（2020–2021 一批、2022 一批、2023 一批），下载后合并即可。
3. 命名建议（放入 `data/raw/csmar/` 目录）：
   - `FS_Combas_2020_2023.xlsx`
   - `FS_Comins_2020_2023.xlsx`
   - `FS_Comscfd_2020_2023.xlsx`
4. **同时下载每张表的《数据说明》文档**，并截屏记录检索条件与下载时间（论文「数据来源与可复现性」部分需要）。

---

## English Version

### 1. Open the Website

Open your browser (Chrome or Edge recommended) and go to **https://data.csmar.com** (the CSMAR data platform). If you are redirected to the legacy domain cn.gtadata.com, that is normal.

### 2. Institutional (School) Login

Choose one of the two paths:

- **Path A: Campus-network direct access (recommended)**
  Connect to the university network (campus Wi-Fi, wired network, or university VPN) → open data.csmar.com → click **Login** at the top-right → choose **Institutional / IP Login**. CSMAR recognises your university by the outgoing IP address; after success, the university name appears at the top-right corner.
- **Path B: University library portal**
  Open your university library website → "Databases / E-resources" → search for "CSMAR" (国泰安) → click the library-provided access link (institutional rights are carried automatically; some universities use SSO / CARSI single sign-on with your student ID).

**How to confirm success**: the university name appears at the top-right corner of the page. If you see a permission error, retry from inside the campus network.

### 3. Enter the Data Centre and Locate the Three Financial Tables

Top navigation: **Data Centre (数据中心)** → **Company Research (公司研究系列)** → **Financial Statements (财务报表)**. Download these three tables:

| Table | Content | Basis |
| --- | --- | --- |
| FS_Combas | Financial Statements – Balance Sheet | Consolidated |
| FS_Comins | Financial Statements – Income Statement | Consolidated |
| FS_Comscfd | Financial Statements – Cash Flow Statement (direct method) | Consolidated |

> Optional bonus item: search "审计意见" (Audit Opinion) in the Data Centre and download the audit-opinion table (AuditOp) as an extra external benchmark.

### 4. Time Range and Accounting Basis

- **Period**: 2020-01-01 to 2023-12-31 (select the annual reporting-date basis, i.e. the 31 December of each year).
- **Statement type**: Consolidated.
- **Currency**: CNY.

### 5. Select Fields (tick them via the built-in field-search box)

**Balance Sheet (FS_Combas)**: Total Assets (资产总计); Total Liabilities (负债合计); Total Current Assets (流动资产合计); Total Current Liabilities (流动负债合计); Net Accounts Receivable (应收账款净额); Net Fixed Assets (固定资产净额); Long-term Borrowings (长期借款).

**Income Statement (FS_Comins)**: Operating Revenue (营业收入); Operating Cost (营业成本); Selling Expenses (销售费用); General & Administrative Expenses (管理费用); Net Profit (净利润).

**Cash Flow Statement (FS_Comscfd)**: Net Cash Flow from Operating Activities (经营活动产生的现金流量净额); Depreciation of Fixed Assets (固定资产折旧, in the supplementary section).

> The exact field codes follow the 《数据说明》(data dictionary) shipped with each download. I will freeze the precise field names and formulas in our feature dictionary for reproducibility.

### 6. Download and Save

1. Click **Download (下载)** → file format **Excel (.xlsx)**, packaged download.
2. If you hit the per-download row limit: **split by year** (2020–2021, 2022, 2023) and merge afterwards.
3. Suggested names (put them into `data/raw/csmar/`):
   - `FS_Combas_2020_2023.xlsx`
   - `FS_Comins_2020_2023.xlsx`
   - `FS_Comscfd_2020_2023.xlsx`
4. **Download the data dictionary for each table as well**, and take screenshots of the search conditions and download time (needed for the "Data Sources and Reproducibility" section of the paper).
