"""Generate a small SYNTHETIC dataset with the same files and columns as the Olist data.

It exists so the pipeline can be tested (and run in CI) without downloading anything.
The numbers mean nothing: real results come from the Kaggle data in data/raw/.
Built-in patterns, so the monitoring has something to catch:
  - weekly seasonality and slow growth
  - a Black Friday spike on 2017-11-24
  - a simulated order-pipeline outage on 2018-05-15 (very few orders)
  - late deliveries get worse reviews
"""
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parents[1] / "data" / "sample"
rng = np.random.default_rng(42)

CATEGORIES = {  # Portuguese name -> (English name, typical price)
    "cama_mesa_banho": ("bed_bath_table", 90), "beleza_saude": ("health_beauty", 120),
    "esporte_lazer": ("sports_leisure", 110), "moveis_decoracao": ("furniture_decor", 140),
    "informatica_acessorios": ("computers_accessories", 160), "utilidades_domesticas": ("housewares", 85),
    "relogios_presentes": ("watches_gifts", 200), "telefonia": ("telephony", 70),
    "brinquedos": ("toys", 95), "automotivo": ("auto", 130), "perfumaria": ("perfumery", 105),
    "pet_shop": ("pet_shop", 100), "fashion_bolsas_e_acessorios": ("fashion_bags_accessories", 80),
}
STATES = ["SP", "RJ", "MG", "RS", "PR", "SC", "BA", "DF", "GO", "ES"]
STATE_P = np.array([42, 13, 12, 6, 5, 4, 3, 2, 2, 2], float)


def uid(prefix: str, n: int) -> list[str]:
    return [f"{prefix}{i:08x}" for i in rng.permutation(16**6)[:n]]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    days = pd.date_range("2016-10-01", "2018-09-15", freq="D")
    t = np.arange(len(days))
    base = 8 + 22 * t / len(days)                                  # growth
    weekly = np.where(days.dayofweek >= 5, 0.8, 1.05)              # weekends quieter
    lam = base * weekly
    lam[days == "2017-11-24"] *= 4.5                               # Black Friday
    lam[(days >= "2017-11-20") & (days <= "2017-11-27")] *= 1.4
    lam[days == "2018-05-15"] *= 0.1                               # outage
    n_per_day = rng.poisson(lam)

    n_orders = int(n_per_day.sum())
    purchase = np.repeat(days.values, n_per_day) + pd.to_timedelta(rng.uniform(0, 86400, n_orders), unit="s")
    purchase = pd.to_datetime(purchase).sort_values()

    # customers: most buy once; ~4% of orders come from someone who bought before
    n_people = n_orders
    people = uid("u", n_people)
    person_idx = np.arange(n_orders)
    repeat = np.flatnonzero(rng.random(n_orders) < 0.04)
    repeat = repeat[repeat > 0]
    person_idx[repeat] = rng.integers(0, repeat)   # an earlier customer
    order_ids, customer_ids = uid("o", n_orders), uid("c", n_orders)
    person_state = rng.choice(STATES, n_people, p=STATE_P / STATE_P.sum())

    status = rng.choice(["delivered", "shipped", "canceled", "unavailable", "invoiced"],
                        n_orders, p=[0.95, 0.02, 0.012, 0.008, 0.01])
    est = purchase + pd.to_timedelta(rng.integers(15, 30, n_orders), unit="D")
    late = rng.random(n_orders) < 0.08
    deliv = est + pd.to_timedelta(np.where(late, rng.integers(1, 15, n_orders), -rng.integers(1, 12, n_orders)), unit="D")
    deliv = pd.Series(deliv).where(status == "delivered")

    orders = pd.DataFrame({
        "order_id": order_ids, "customer_id": customer_ids, "order_status": status,
        "order_purchase_timestamp": purchase, "order_approved_at": purchase + pd.Timedelta(hours=1),
        "order_delivered_carrier_date": (purchase + pd.Timedelta(days=2)).where(status == "delivered"),
        "order_delivered_customer_date": deliv, "order_estimated_delivery_date": est.normalize(),
    })
    customers = pd.DataFrame({
        "customer_id": customer_ids, "customer_unique_id": np.array(people)[person_idx],
        "customer_zip_code_prefix": rng.integers(1000, 99999, n_orders),
        "customer_city": "sample_city", "customer_state": person_state[person_idx],
    })

    pt_names = list(CATEGORIES)
    products = pd.DataFrame({"product_id": uid("p", 600),
                             "product_category_name": rng.choice(pt_names, 600)})
    products["product_name_lenght"] = rng.integers(20, 60, 600)
    products["product_description_lenght"] = rng.integers(100, 2000, 600)
    products["product_photos_qty"] = rng.integers(1, 6, 600)
    products["product_weight_g"] = rng.integers(100, 5000, 600)
    for c in ("product_length_cm", "product_height_cm", "product_width_cm"):
        products[c] = rng.integers(10, 60, 600)
    sellers = pd.DataFrame({"seller_id": uid("s", 120), "seller_zip_code_prefix": rng.integers(1000, 99999, 120),
                            "seller_city": "sample_city", "seller_state": rng.choice(STATES, 120)})

    n_items = rng.choice([1, 1, 1, 1, 2, 3], n_orders)
    item_order = np.repeat(order_ids, n_items)
    item_no = np.concatenate([np.arange(1, k + 1) for k in n_items])
    prod_pick = rng.integers(0, len(products), len(item_order))
    typical = products["product_category_name"].map(lambda c: CATEGORIES[c][1]).to_numpy()[prod_pick]
    price = np.round(rng.lognormal(np.log(typical), 0.5), 2)
    order_items = pd.DataFrame({
        "order_id": item_order, "order_item_id": item_no, "product_id": products["product_id"].to_numpy()[prod_pick],
        "seller_id": rng.choice(sellers["seller_id"], len(item_order)),
        "shipping_limit_date": np.repeat(purchase + pd.Timedelta(days=3), n_items),
        "price": price, "freight_value": np.round(rng.uniform(8, 40, len(item_order)), 2),
    })

    totals = order_items.groupby("order_id")[["price", "freight_value"]].sum().sum(axis=1).reindex(order_ids)
    payments = pd.DataFrame({
        "order_id": order_ids, "payment_sequential": 1,
        "payment_type": rng.choice(["credit_card", "boleto", "voucher", "debit_card"], n_orders, p=[.74, .19, .05, .02]),
        "payment_installments": rng.integers(1, 10, n_orders), "payment_value": np.round(totals.values, 2),
    })

    reviewed = rng.random(n_orders) < 0.97
    score = np.where(late,
                     rng.choice([1, 2, 3, 4, 5], n_orders, p=[0.30, 0.15, 0.15, 0.15, 0.25]),
                     rng.choice([1, 2, 3, 4, 5], n_orders, p=[0.06, 0.03, 0.08, 0.20, 0.63]))
    reviews = pd.DataFrame({
        "review_id": uid("r", n_orders), "order_id": order_ids, "review_score": score,
        "review_comment_title": None, "review_comment_message": None,
        "review_creation_date": (est + pd.Timedelta(days=1)).normalize(),
        "review_answer_timestamp": est + pd.Timedelta(days=2),
    })[reviewed]

    translation = pd.DataFrame({"product_category_name": pt_names,
                                "product_category_name_english": [CATEGORIES[c][0] for c in pt_names]})

    files = {
        "olist_orders_dataset.csv": orders, "olist_customers_dataset.csv": customers,
        "olist_order_items_dataset.csv": order_items, "olist_order_payments_dataset.csv": payments,
        "olist_order_reviews_dataset.csv": reviews, "olist_products_dataset.csv": products,
        "olist_sellers_dataset.csv": sellers, "product_category_name_translation.csv": translation,
    }
    for name, df in files.items():
        df.to_csv(OUT / name, index=False)
    print(f"Wrote {len(files)} synthetic files to {OUT} ({n_orders:,} orders)")


if __name__ == "__main__":
    main()
