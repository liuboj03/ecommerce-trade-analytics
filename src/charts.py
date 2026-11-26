"""Static charts for the README. The interactive version lives on Tableau Public."""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from . import config  # noqa: E402

BLUE, GREY, RED = "#2B5C8A", "#9AA5B1", "#C0392B"


def _save(fig, path: Path) -> None:
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


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


def review_repurchase(rr: pd.DataFrame, out: Path) -> None:
    rr = rr[rr["first_order_review"] != "no review"]
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(rr["first_order_review"], rr["repurchase_rate"], color=BLUE)
    for x, v in zip(rr["first_order_review"], rr["repurchase_rate"]):
        ax.text(x, v, f"{v:.1%}", ha="center", va="bottom", fontsize=9)
    ax.set_title("Repurchase rate by first-order review score", loc="left", fontsize=12)
    ax.set_xlabel("Review score of the customer's first order")
    ax.yaxis.set_visible(False)
    ax.spines[["top", "right", "left"]].set_visible(False)
    _save(fig, out)


def campaign_decomposition(dec: pd.DataFrame, gmv_change: float, out: Path) -> None:
    labels = {"buyers": "Buyers", "orders_per_buyer": "Orders per buyer", "aov": "AOV"}
    fig, ax = plt.subplots(figsize=(6, 3.5))
    ax.bar([labels[d] for d in dec["driver"]], dec["share_of_gmv_change"], color=BLUE)
    for i, v in enumerate(dec["share_of_gmv_change"]):
        ax.text(i, v, f"{v:.0%}", ha="center", va="bottom" if v >= 0 else "top", fontsize=10)
    ax.axhline(0, color="black", lw=0.6)
    ax.set_title(f"{config.CAMPAIGN['name']}: what drove the GMV change ({gmv_change:+.0%})",
                 loc="left", fontsize=11)
    ax.yaxis.set_visible(False)
    ax.spines[["top", "right", "left"]].set_visible(False)
    _save(fig, out)
