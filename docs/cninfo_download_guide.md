# 巨潮资讯网年报下载指引（中文版 + English Version）

适用项目：Group12A2 · Screening Financial Disclosure Risk through Textual-Financial Feature Fusion and Explainable Anomaly Detection（2021–2023 中国 A 股制造业）。

目标数据：**2021、2022、2023 三个年度中文年报 PDF**，用于提取「管理层讨论与分析」（MD&A）文本。

---

## 中文版

### 1. 进入网站

打开浏览器，访问 **https://www.cninfo.com.cn**（巨潮资讯网，中国证监会指定的上市公司信息披露网站，覆盖沪深北全部 A 股公告）。

浏览和下载公告**免费、无需登录**；可选注册免费账号（无必要）。

### 2. 进入公告检索页面

首页顶部导航「**公告查询**」或「**数据**」→「**信息披露**」→「**定期报告**」。

直达链接：**http://www.cninfo.com.cn/new/commonUrl/pageOfSearch?url=disclosure/list/search**

### 3. 设置检索条件

- **证券代码 / 简称**：输入要下载的公司代码（如 000001）。逐家检索。
- **公告类别**：选「定期报告」→ 勾选「**年度报告**」。**不要**勾选「年度报告摘要」或英文版年报。
- **发布时间区间**（关键，按披露年度设置）：

| 目标年报 | 发布时间区间 |
| --- | --- |
| 2021 年报 | 2022-01-01 至 2022-06-30 |
| 2022 年报 | 2023-01-01 至 2023-06-30 |
| 2023 年报 | 2024-01-01 至 2024-06-30 |

> A 股年报法定披露截止日为次年 4 月 30 日，区间放宽到 6 月底留足余量。若同一公司出现多份年度报告（修订版），下载**最新发布**的那份。

### 4. 下载 PDF

点击公告标题打开预览 → 预览页右上角「**下载**」→ 保存为：

`{证券代码}_{会计年度}_年报.pdf`，例如 `000001_2021.pdf`。

存放目录建议：`data/raw/cninfo/2021/`、`data/raw/cninfo/2022/`、`data/raw/cninfo/2023/`。

### 5. 工作量与分工（本项目最大工作量点）

- 制造业 A 股约 2,500–3,500 家 × 3 年 ≈ **7,500–10,500 份 PDF**。
- 单份年报 PDF 约 2–10 MB，总磁盘占用可能 **20–80 GB**，请提前准备空间。
- 建议分工：
  1. 先从 `STK_LISTEDCOINFOANL.xlsx` 生成制造业公司清单（2021–2023 每家公司一行）。
  2. 按年度分三批，组员每人认领一个年度。
  3. 逐家检索下载，**每完成一家在共享清单上打勾**，避免遗漏与重复。
  4. 个别公司可能缺某年报告（退市、重组等），在清单上标注「无」，后面我会统计缺失并汇报。

### 6. 下载完成后的处理

- MD&A = 年报正文「**第三节 管理层讨论与分析**」（部分公司标题略有差异，如「经营情况讨论与分析」），PDF 解析脚本会按标题定位该节。
- PDF 原文请**原样保留备查**，不要只保存导出的文本。

> 提示：巨潮网页背后有公开的查询接口（浏览器按 F12 可见），如需批量自动化我可以写脚本调用；但课程范围内手动逐家下载最稳妥、最不容易被反爬限制。

---

## English Version

### 1. Open the Website

Go to **https://www.cninfo.com.cn** (CNINFO / 巨潮资讯网, the officially designated disclosure website of the China Securities Regulatory Commission; it covers all announcements of SSE-, SZSE-, and BSE-listed A-share companies).

Browsing and downloading announcements are **free and require no login**. Registering a free account is optional and unnecessary.

### 2. Enter the Announcement Search Page

Top navigation: **公告查询 (Announcement Search)** or **数据 (Data)** → **信息披露 (Information Disclosure)** → **定期报告 (Periodic Reports)**.

Direct link: **http://www.cninfo.com.cn/new/commonUrl/pageOfSearch?url=disclosure/list/search**

### 3. Set the Search Conditions

- **Stock code / abbreviation**: enter the target company code (e.g. 000001). Search one company at a time.
- **Announcement category**: select "Periodic Reports" and tick **年度报告 (Annual Report)**. Do **not** tick "Annual Report Summary" or the English-version report.
- **Publication date range** (critical; set by disclosure year):

| Target annual report | Publication date range |
| --- | --- |
| FY2021 | 2022-01-01 to 2022-06-30 |
| FY2022 | 2023-01-01 to 2023-06-30 |
| FY2023 | 2024-01-01 to 2024-06-30 |

> The statutory deadline for A-share annual reports is 30 April of the following year; the range is extended to the end of June for safety. If a company published several versions (revised reports), download the **latest** one.

### 4. Download the PDF

Click the announcement title to open the preview → click **下载 (Download)** at the top-right of the preview page → save it as:

`{stock_code}_{fiscal_year}_annual_report.pdf`, e.g. `000001_2021.pdf`.

Suggested folders: `data/raw/cninfo/2021/`, `data/raw/cninfo/2022/`, `data/raw/cninfo/2023/`.

### 5. Workload and Division of Labour (the heaviest task of this project)

- ≈2,500–3,500 manufacturing A-share firms × 3 years ≈ **7,500–10,500 PDFs**.
- Each annual-report PDF is about 2–10 MB; total disk usage may reach **20–80 GB**. Prepare storage in advance.
- Suggested division of labour:
  1. Generate the manufacturing-firm list from `STK_LISTEDCOINFOANL.xlsx` (one row per firm-year for 2021–2023).
  2. Split the work into three batches by fiscal year; each member takes one year.
  3. Download firm by firm and **tick each completed firm on the shared list** to avoid omissions and duplicates.
  4. If a company lacks a report in some year (delisting, restructuring, etc.), mark it "missing" on the list; I will later count and report the missing cases.

### 6. After Downloading

- The MD&A section is **"第三节 管理层讨论与分析"** (Section 3: Management Discussion and Analysis) of the annual report (some companies use slightly different headings, such as "经营情况讨论与分析"). The PDF-parsing script will locate the section by its heading.
- Keep the **original PDFs for the record**; do not keep only the exported text.

> Note: CNINFO's search page is backed by public JSON endpoints (visible via F12 in the browser). If batch automation is needed, I can write a script for it; for the course scope, downloading firm by firm manually is the most robust approach and the least likely to hit anti-scraping limits.
