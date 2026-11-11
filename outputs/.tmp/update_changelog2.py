"""One-off: add today's second batch of changelog bullets."""

from pathlib import Path

path = Path("CHANGELOG.md")
text = path.read_text(encoding="utf-8")
header = "## 2026-11-11\n"
assert header in text

bullets = """
- 新增 `docs/csmar_event_data_guide.md`：第二轮换结果变量所需的 CSMAR 数据指引——审计意见（必下）、会计差错更正/财务重述、违规处理、特别处理（可选）四张表的库路径、时间窗口、目标字段、导出命名（`data/raw/csmar_events/`）、自检方法、七个常见坑与"按订阅权限怎么选"的决策树；同时说明问询函不在 CSMAR 及其替代来源（交易所官网爬虫 / CNRDS / textdata）。
- 新增 `scripts/run_00c_inspect_csmar_export.py`：打印任意 CSMAR 导出（xlsx/csv）的 sheet、列名、行数、证券代码样例与长度，用于下载后 5 分钟自检（前导零、行数量级、意见类型列可读性），并已用根目录 `STK_LISTEDCOINFOANL.xlsx` 验证。
- 新增 `data/raw/csmar_events/README.md`（本地目录，data/ 不入库）：规定四个文件名与《数据说明》保留规则。
- `GUIDE.md`：§1.2 数据来源表新增事件变量指引入口，§5 阶段表新增 `run_00c_inspect_csmar_export.py`。
"""
text = text.replace(header, header + bullets, 1)
path.write_text(text, encoding="utf-8")
print("changelog updated")
