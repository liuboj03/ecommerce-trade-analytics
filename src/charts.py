"""Static charts for the README. The interactive version lives on Tableau Public."""
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
matplotlib.rcParams["svg.fonttype"] = "none"   # keep text as text: smaller files, selectable labels
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from . import config  # noqa: E402

BLUE, GREY, RED = "#2B5C8A", "#9AA5B1", "#C0392B"


def _save(fig, path: Path) -> None:
    fig.tight_layout()
    fig.savefig(path, metadata={"Date": None})   # no timestamp: re-runs give identical files
    plt.close(fig)
    # round coordinates to 1 decimal: same picture, much smaller file
    svg = path.read_text(encoding="utf-8")
    path.write_text(re.sub(r"(\d+\.\d)\d+", r"\1", svg), encoding="utf-8")


def daily_gmv(daily: pd.DataFrame, anomalies: pd.DataFrame, out: Path) -> None:
    d = daily.assign(dt=pd.to_datetime(daily["dt"]))
    flags = anomalies[anomalies["metric"] == "gmv"].assign(dt=lambda x: pd.to_datetime(x["dt"]))
    fig, ax = plt.subplots(figsize=(11, 4))
    ax.plot(d["dt"], d["gmv"], color=GREY, lw=0.8, label="Daily GMV")
    ax.plot(d["dt"], d["gmv"].rolling(7).mean(), color=BLUE, lw=1.8, label="7-day average")
    ax.scatter(flags["dt"], flags["value"], color=RED, s=28, zorder=3,
               label=f"Alert (|z| > {config.Z_THRESHOLD:g} vs previous {config.ROLLING_DAYS} days)")
    ax.set_title("Daily GMV with automatic alerts", loc="left", fontsize=12)
    ax.set_ylabel("GMV (BRL)")
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, fontsize=9)
    _save(fig, out)


def category_share(cat_month: pd.DataFrame, out: Path, top: int = 10) -> None:
    total = cat_month.groupby("category")["gmv"].sum().sort_values()
    share = (total / total.sum()).tail(top)
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.barh(share.index, share.values, color=BLUE)
    for y, v in enumerate(share.values):
        ax.text(v, y, f" {v:.1%}", va="center", fontsize=9)
    ax.set_title(f"Top {top} categories by share of GMV", loc="left", fontsize=12)
    ax.xaxis.set_visible(False)
    ax.spines[["top", "right", "bottom"]].set_visible(False)
    _save(fig, out)


def campaign_decomposition(dec: pd.DataFrame, gmv_change: float, out: Path) -> None:
    labels = {"buyers": "Buyers", "orders_per_buyer": "Orders per buyer", "aov": "AOV"}
    vals = dec["share_of_gmv_change"].to_numpy()
    fig, ax = plt.subplots(figsize=(6.5, 3.8))
    ax.bar([labels[d] for d in dec["driver"]], vals, color=[BLUE if v >= 0 else RED for v in vals], width=0.55)
    pad = 0.03 * max(abs(vals).max(), 0.01)
    for i, v in enumerate(vals):
        text = "0%" if abs(v) < 0.005 else f"{v:+.0%}"
        ax.text(i, v + pad if v >= 0 else v - pad, text, ha="center",
                va="bottom" if v >= 0 else "top", fontsize=10)
    ax.axhline(0, color="black", lw=0.6)
    ax.set_ylim(min(vals.min(), 0) - 8 * pad, vals.max() + 8 * pad)
    ax.set_title(f"{config.CAMPAIGN['name']}: GMV {gmv_change:+.0%} vs baseline week\n"
                 "Share of the change explained by each driver (log decomposition)", loc="left", fontsize=10.5)
    ax.yaxis.set_visible(False)
    ax.tick_params(axis="x", length=0)
    ax.spines[["top", "right", "left", "bottom"]].set_visible(False)
    _save(fig, out)


def delivery_review(dr: pd.DataFrame, out: Path) -> None:
    fig, ax = plt.subplots(figsize=(6, 3.5))
    colors = [BLUE if d == "on time" else RED for d in dr["delivery"]]
    ax.bar(dr["delivery"], dr["bad_review_rate"], color=colors, width=0.5)
    for x, v, n in zip(dr["delivery"], dr["bad_review_rate"], dr["orders"]):
        ax.text(x, v, f"{v:.1%}\n({n:,} orders)", ha="center", va="bottom", fontsize=9)
    ax.set_title("Bad review rate (score <= 2): on-time vs late delivery", loc="left", fontsize=11)
    ax.set_ylim(0, dr["bad_review_rate"].max() * 1.3)
    ax.yaxis.set_visible(False)
    ax.spines[["top", "right", "left"]].set_visible(False)
    _save(fig, out)
