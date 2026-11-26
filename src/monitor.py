"""Daily monitoring: flag anomalous days and write a daily report.

Rule: for each metric, compare the day with the mean and standard deviation of the
previous ROLLING_DAYS days (the day itself is excluded, so a spike does not hide
itself). |z| > Z_THRESHOLD is flagged. Simple and explainable on purpose.
"""
import pandas as pd

from . import config


def detect_anomalies(daily: pd.DataFrame) -> pd.DataFrame:
    df = daily.sort_values("dt").reset_index(drop=True)
    rows = []
    for metric in config.MONITORED_METRICS:
        s = df[metric].astype(float)
        hist = s.shift(1).rolling(config.ROLLING_DAYS, min_periods=config.ROLLING_DAYS)
        mean, std = hist.mean(), hist.std()
        z = (s - mean) / std
        flagged = z.abs() > config.Z_THRESHOLD
        for i in df.index[flagged.fillna(False)]:
            rows.append({
                "dt": df.at[i, "dt"],
                "metric": metric,
                "value": s[i],
                "baseline_mean": mean[i],
                "z_score": z[i],
                "direction": "up" if z[i] > 0 else "down",
            })
    out = pd.DataFrame(rows, columns=["dt", "metric", "value", "baseline_mean", "z_score", "direction"])
    return out.sort_values(["dt", "metric"]).reset_index(drop=True)


def _fmt(metric: str, v: float) -> str:
    if pd.isna(v):
        return "-"
    if metric.endswith("rate"):
        return f"{v:.1%}"
    if metric in ("gmv", "aov"):
        return f"{v:,.0f}"
    return f"{v:,.0f}"


def _pct(a: float, b: float) -> str:
    if pd.isna(a) or pd.isna(b) or b == 0:
        return "-"
    return f"{a / b - 1:+.1%}"


def daily_report(daily: pd.DataFrame, anomalies: pd.DataFrame, day: str) -> str:
    """Markdown report for one day: value, day-over-day, week-over-week, vs 28-day mean."""
    df = daily.set_index(pd.to_datetime(daily["dt"]))
    d = pd.Timestamp(day)
    prev, last_week = d - pd.Timedelta(days=1), d - pd.Timedelta(days=7)
    window = df.loc[d - pd.Timedelta(days=config.ROLLING_DAYS): d - pd.Timedelta(days=1)]

    metrics = ["gmv", "orders", "buyers", "aov", "cancel_rate", "bad_review_rate", "late_rate"]
    names = {"gmv": "GMV", "orders": "Orders", "buyers": "Buyers", "aov": "AOV",
             "cancel_rate": "Cancel rate", "bad_review_rate": "Bad review rate (score<=2)",
             "late_rate": "Late delivery rate"}
    lines = [f"# Daily trade report: {d.date()} ({d.day_name()})", "",
             "| Metric | Value | vs prev day | vs same day last week | vs 28-day mean |",
             "|---|---|---|---|---|"]
    for m in metrics:
        v = df.at[d, m]
        lines.append(f"| {names[m]} | {_fmt(m, v)} | {_pct(v, df.at[prev, m])} | "
                     f"{_pct(v, df.at[last_week, m])} | {_pct(v, window[m].mean())} |")

    day_flags = anomalies[pd.to_datetime(anomalies["dt"]) == d]
    lines += ["", "## Alerts"]
    if day_flags.empty:
        lines.append("No metric outside the alert band.")
    else:
        for _, r in day_flags.iterrows():
            lines.append(f"- **{r.metric}** is {r.direction} (z = {r.z_score:.1f}; "
                         f"value {_fmt(r.metric, r.value)} vs 28-day mean {_fmt(r.metric, r.baseline_mean)})")
    return "\n".join(lines) + "\n"
