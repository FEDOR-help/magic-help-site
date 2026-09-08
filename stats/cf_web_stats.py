#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Статистика сайта «Магическая помощь» из Cloudflare Web Analytics.

Тянет данные через официальный GraphQL API и строит графики + цифры.
Запуск:  python cf_web_stats.py [days]
"""
import argparse, os, sys, json, ssl, io
import urllib.request, urllib.error
from datetime import datetime, timedelta, timezone

# --- matplotlib, не блокирующий импорт при отсутствии ---
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import MaxNLocator

HERE = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(HERE, ".env")
if not os.path.exists(ENV_PATH):
    ENV_PATH = r"D:\.env"

def load_env(path):
    d = {}
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                d[k.strip()] = v.strip().strip('"').strip("'")
    return d

ENV = load_env(ENV_PATH)
CF_KEY = ENV.get("CLOUDFLARE_API_KEY") or os.environ.get("CLOUDFLARE_API_KEY", "")
CF_ACCT = ENV.get("CLOUDFLARE_ACCOUNT_ID") or os.environ.get("CLOUDFLARE_ACCOUNT_ID", "")
SITE_TAG = "b4a30e85650b48358223b4b0d102f7c6"
SITE_HOST = "fedor-help.github.io"

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

QUERY = """query WebAnalytics($tag: String!, $f: RumAdaptiveGroupsFilterInput) {
  viewer {
    accounts(filter: {accountTag: $tag}) {
      pageviews: rumPageloadEventsAdaptiveGroups(limit: 5000, filter: $f) {
        count
        avg { sampleInterval }
        dimensions { date }
      }
      visits: rumPageloadEventsAdaptiveGroups(limit: 5000, filter: $f) {
        count
        sum { visits }
        avg { sampleInterval }
        dimensions { date }
      }
    }
  }
}"""

def api_gql(variables):
    body = json.dumps({"query": QUERY, "variables": variables}).encode()
    req = urllib.request.Request("https://api.cloudflare.com/client/v4/graphql", data=body, method="POST")
    req.add_header("Authorization", f"Bearer {CF_KEY}")
    req.add_header("Content-Type", "application/json")
    req.add_header("User-Agent", "Mozilla/5.0")
    r = urllib.request.urlopen(req, timeout=45, context=ctx)
    return json.loads(r.read().decode("utf-8", "replace"))

def fetch_days(days):
    now = datetime.now(timezone.utc)
    gte = (now - timedelta(days=days - 1)).strftime("%Y-%m-%d") + "T00:00:00Z"
    lte = now.strftime("%Y-%m-%d") + "T23:59:59Z"
    vars_ = {
        "tag": CF_ACCT,
        "f": {"AND": [
            {"datetime_geq": gte, "datetime_leq": lte},
            {"siteTag_in": [SITE_TAG]},
            {"bot": 0},
        ]},
    }
    d = api_gql(vars_)
    if d.get("errors"):
        raise RuntimeError(json.dumps(d["errors"], ensure_ascii=False)[:400])
    acct = (d.get("data") or {}).get("viewer", {}).get("accounts", [{}])[0]
    return acct.get("pageviews", []), acct.get("visits", [])

def build_series(pageviews, visits):
    pv = {}
    for r in pageviews:
        pv[r["dimensions"]["date"]] = r["count"]
    vs = {}
    for r in visits:
        vs[r["dimensions"]["date"]] = (r["sum"] or {}).get("visits", r.get("count", 0))
    all_days = sorted(set(list(pv) + list(vs)))
    return {
        "days": all_days,
        "pageviews": [pv.get(dd, 0) for dd in all_days],
        "visits": [vs.get(dd, 0) for dd in all_days],
    }

def make_chart(series, out_png):
    days = [datetime.fromisoformat(dd) for dd in series["days"]]
    pv = series["pageviews"]
    vs = series["visits"]

    fig, ax = plt.subplots(figsize=(12, 5.5), dpi=110)
    ax.bar(days, pv, width=0.9, color="#5b4b8a", alpha=0.85, label="Просмотры страниц")
    ax.plot(days, vs, color="#e5a13a", marker="o", markersize=5, linewidth=2, label="Визиты")
    ax.set_title(f"«Магическая помощь» — посещаемость (Cloudflare Web Analytics)\n{SITE_HOST}", fontsize=13)
    ax.set_xlabel("Дата")
    ax.set_ylabel("Количество")
    ax.legend()
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d.%m"))
    ax.xaxis.set_major_locator(MaxNLocator(nbins=min(len(days), 14), integer=True))
    fig.autofmt_xdate(rotation=30)
    fig.tight_layout()
    fig.savefig(out_png)
    plt.close(fig)

def hms(sec):
    sec = int(sec)
    h, sec = divmod(sec, 3600)
    m, sec = divmod(sec, 60)
    return f"{h} ч {m} мин" if h else f"{m} мин"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("days", nargs="?", type=int, default=14, help="период в днях")
    ap.add_argument("--out", default=os.path.join(HERE, "статистика_сайта.png"))
    ap.add_argument("--json", action="store_true", help="вывести JSON вместо графика")
    args = ap.parse_args()

    if not CF_KEY or not CF_ACCT:
        print("Нет Cloudflare-ключей (D:\\.env)")
        sys.exit(1)

    try:
        pv_rows, vs_rows = fetch_days(args.days)
    except Exception as e:
        print("ОШИБКА запроса:", e)
        sys.exit(1)

    series = build_series(pv_rows, vs_rows)
    if not series["days"]:
        print("Данных за период пока нет: счётчик установлен, но посещения ещё не регистрировались.")
        print("Загляните позже или откройте сайт, чтобы появился первый визит.")
        sys.exit(0)
    total_pv = sum(series["pageviews"])
    total_visits = sum(series["visits"])
    avg_day = total_pv / len(series["days"])
    best_ix = series["pageviews"].index(max(series["pageviews"])) if series["pageviews"] else None

    print("=" * 52)
    print("СТАТИСТИКА САЙТА «МАГИЧЕСКАЯ ПОМОЩЬ»")
    print(f"Сайт:   https://{SITE_HOST}")
    print(f"Период: {series['days'][0] if series['days'] else '-'} — {series['days'][-1] if series['days'] else '-'}")
    print("-" * 52)
    print(f"Просмотры страниц (всего):   {total_pv}")
    print(f"Визиты (всего):              {total_visits}")
    if series["days"]:
        print(f"В среднем за день:           {avg_day:.1f} просмотров")
    if best_ix is not None and series["days"]:
        print(f"Лучший день:                 {series['days'][best_ix]} — {series['pageviews'][best_ix]} просмотров")
    print("=" * 52)

    if args.json:
        print(json.dumps({
            "host": SITE_HOST,
            "days": series["days"],
            "pageviews": series["pageviews"],
            "visits": series["visits"],
            "totals": {"pageviews": total_pv, "visits": total_visits},
        }, ensure_ascii=False, indent=2))
        return

    try:
        make_chart(series, args.out)
        print(f"\nГрафик сохранён: {args.out}")
    except Exception as e:
        print("Не удалось построить график:", e)

if __name__ == "__main__":
    main()