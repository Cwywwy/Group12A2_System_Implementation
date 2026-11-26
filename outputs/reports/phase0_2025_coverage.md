# Phase 0 coverage gate: fiscal-year extension

Source intermediate file: `finance_intermediate_p2025.csv`
Gate: complete-case coverage of the newest year (FY2025) must reach 90% of the previous year.

| Fiscal year | Frame | PDF on disk | Six financial inputs | Beneish inputs | Share of frame | vs previous year |
| --- | --- | --- | --- | --- | --- | --- |
| FY2021 | 3,165 | 3,074 | 3,156 | 3,156 | 99.7% | — |
| FY2022 | 3,404 | 3,387 | 3,394 | 3,394 | 99.7% | 1.075 |
| FY2023 | 3,603 | 3,591 | 3,596 | 3,595 | 99.8% | 1.059 |
| FY2024 | 3,666 | 3,437 | 3,661 | 3,661 | 99.9% | 1.018 |
| FY2025 | 3,762 | 925 | 3,757 | 3,757 | 99.9% | 1.026 |

**Verdict: PASS** — FY2025 reaches 1.026 of the previous year's complete cases (threshold 0.90).

Notes

- FY2020 enters only as the base year for growth and Beneish components; it is not a modelling year.
- `depreciation` is absent from the direct-method cash-flow export, so the depreciation index is neutralised at 1.0 rather than imputed.
- Frame counts come from `data/processed/sample_frame.csv`; PDF counts count distinct symbols with at least one PDF on disk for that fiscal year.
