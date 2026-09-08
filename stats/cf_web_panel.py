#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Локальная HTML-панель статистики «Магическая помощь».

Запускает мини-сервер на localhost, открывает страницу в браузере.
Панель показывает цифры + график и кнопку «Обновить» (тянет свежие данные
через Cloudflare GraphQL API без браузера).

Использование:
  python cf_web_panel.py [--days 30] [--port 8543]
"""
import argparse, io, json, os, socket, ssl, sys, threading, webbrowser, urllib.request, urllib.error
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import cf_web_stats as cws  # переиспользуем fetch_days/build_series/ENV

PORT = 8543
DAYS = 30

PAGE = r"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<title>Магическая помощь — статистика сайта</title>
<style>
  :root{--bg:#0f1220;--card:#1a1f35;--line:#2b3350;--txt:#e8eaf6;--mut:#9aa3c7;
        --pv:#7c6fd0;--vs:#e5a13a;--good:#5fd07c;--bad:#e56a6a;}
  *{box-sizing:border-box}
  body{margin:0;font:15px/1.45 "Segoe UI",Arial,sans-serif;background:var(--bg);color:var(--txt)}
  .wrap{max-width:1080px;margin:0 auto;padding:24px}
  h1{font-size:22px;margin:0 0 4px}
  .sub{color:var(--mut);margin-bottom:18px}
  .cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin-bottom:18px}
  .card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px 16px}
  .card .lbl{color:var(--mut);font-size:12px;text-transform:uppercase;letter-spacing:.4px}
  .card .val{font-size:26px;font-weight:600;margin-top:4px}
  .card .val.small{font-size:18px}
  .toolbar{display:flex;gap:10px;align-items:center;margin-bottom:14px;flex-wrap:wrap}
  button{background:var(--pv);border:0;color:#fff;font:600 14px "Segoe UI";padding:9px 18px;border-radius:8px;cursor:pointer}
  button:hover{filter:brightness(1.12)}
  button:disabled{opacity:.55;cursor:default}
  #status{color:var(--mut);font-size:13px}
  .panel{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px}
  canvas{width:100%;height:340px}
  .legend{display:flex;gap:18px;margin:6px 0 10px;color:var(--mut);font-size:13px}
  .lg{display:inline-flex;align-items:center;gap:7px}
  .sw{width:12px;height:12px;border-radius:3px;display:inline-block}
  table{width:100%;border-collapse:collapse;margin-top:14px}
  th,td{padding:8px 10px;text-align:right;border-bottom:1px solid var(--line)}
  th:first-child,td:first-child{text-align:left}
  thead th{color:var(--mut);font-size:12px;text-transform:uppercase;letter-spacing:.4px;position:sticky;top:0;background:var(--card)}
  .scroll{max-height:340px;overflow:auto}
  .empty{color:var(--mut);padding:20px;text-align:center}
  .foot{color:var(--mut);font-size:12px;margin-top:16px}
  .err{color:var(--bad)}
</style>
</head>
<body>
<div class="wrap">
  <h1>«Магическая помощь» — статистика сайта</h1>
  <div class="sub" id="meta">Загрузка…</div>

  <div class="cards">
    <div class="card"><div class="lbl">Просмотры (всего)</div><div class="val" id="cPv">—</div></div>
    <div class="card"><div class="lbl">Визиты (всего)</div><div class="val" id="cVs">—</div></div>
    <div class="card"><div class="lbl">В среднем / день</div><div class="val small" id="cAvg">—</div></div>
    <div class="card"><div class="lbl">Дней в периоде</div><div class="val small" id="cDays">—</div></div>
    <div class="card"><div class="lbl">Лучший день</div><div class="val small" id="cBest">—</div></div>
  </div>

  <div class="toolbar">
    <button id="btn">Обновить</button>
    <span id="status"></span>
  </div>

  <div class="panel">
    <div class="legend">
      <span class="lg"><span class="sw" style="background:var(--pv)"></span>Просмотры страниц</span>
      <span class="lg"><span class="sw" style="background:var(--vs)"></span>Визиты</span>
    </div>
    <canvas id="chart" width="1000" height="340"></canvas>
  </div>

  <div class="panel scroll">
    <table>
      <thead><tr><th>Дата</th><th>Визиты</th><th>Просмотры</th></tr></thead>
      <tbody id="rows"><tr><td colspan="3" class="empty">Нет данных</td></tr></tbody>
    </table>
  </div>

  <div class="foot">Источник: Cloudflare Web Analytics (GraphQL API). Обновляется кнопкой «Обновить».</div>
</div>

<script>
"use strict";
const mono = v => v.toLocaleString("ru-RU");
let chartData = null;

function draw(data){
  const c = document.getElementById("chart");
  const ctx = c.getContext("2d");
  const W = c.width, H = c.height, PAD = {l:46, r:16, t:16, b:34};
  ctx.clearRect(0,0,W,H);

  if(!data || !data.days || !data.days.length){
    ctx.fillStyle = "rgba(154,163,199,.7)";
    ctx.font = "15px Segoe UI";
    ctx.textAlign = "center";
    ctx.fillText("Посещений пока нет — счётчик установлен, ждём первый визит", W/2, H/2);
    return;
  }

  const days = data.days, pv = data.pageviews, vs = data.visits;
  const maxV = Math.max(1, ...pv, ...vs);
  const pw = (W - PAD.l - PAD.r) / days.length;
  const plotH = H - PAD.t - PAD.b;
  const X = i => PAD.l + pw*i + pw/2;
  const Y = v => PAD.t + plotH - (v / maxV) * plotH;

  // grid + y labels
  ctx.strokeStyle = "rgba(255,255,255,.08)";
  ctx.fillStyle = "#9aa3c7"; ctx.font = "11px Segoe UI";
  for(let g=0; g<=4; g++){
    const val = maxV * g/4;
    const yy = Y(val);
    ctx.beginPath(); ctx.moveTo(PAD.l, yy); ctx.lineTo(W-PAD.r, yy); ctx.stroke();
    ctx.textAlign = "right"; ctx.fillText(Math.round(val).toLocaleString("ru-RU"), PAD.l-8, yy+4);
  }

  // bars
  pv.forEach((v,i)=>{
    const bh = (v/maxV)*plotH;
    ctx.fillStyle = "rgba(124,111,208,.75)";
    ctx.fillRect(PAD.l + pw*i + pw*0.14, PAD.t+plotH-bh, pw*0.72, bh);
  });

  // visits line
  ctx.strokeStyle = "#e5a13a"; ctx.lineWidth = 2.2; ctx.lineJoin = "round";
  ctx.beginPath();
  vs.forEach((v,i)=>{ const x=X(i), y=Y(v); i?ctx.lineTo(x,y):ctx.moveTo(x,y); });
  ctx.stroke();
  vs.forEach((v,i)=>{
    ctx.fillStyle = "#e5a13a";
    ctx.beginPath(); ctx.arc(X(i),Y(v),3.4,0,7); ctx.fill();
  });

  // x labels
  ctx.fillStyle = "#9aa3c7"; ctx.textAlign = "center";
  const step = Math.max(1, Math.ceil(days.length/14));
  const fmt = d => { const p = d.split("-"); return p[2]+"."+p[1]; };
  for(let i=0; i<days.length; i+=step){
    ctx.fillText(fmt(days[i]), X(i), H-12);
  }
}

function renderTable(data){
  const tbody = document.getElementById("rows");
  if(!data || !data.days || !data.days.length){
    tbody.innerHTML = '<tr><td colspan="3" class="empty">Нет данных за период</td></tr>';
    return;
  }
  tbody.innerHTML = data.days.map((d,i)=>{
    const dt = d.split("-"), fmt = dt[2]+"."+dt[1]+"."+dt[0];
    return '<tr><td>'+fmt+'</td><td>'+mono(data.visits[i])+'</td><td>'+mono(data.pageviews[i])+'</td></tr>';
  }).join("");
}

function render(data){
  const totalPv = (data.totals||{}).pageviews ?? 0;
  const totalVs = (data.totals||{}).visits ?? 0;
  const daysN = (data.days||[]).length;
  document.getElementById("cPv").textContent = mono(totalPv);
  document.getElementById("cVs").textContent = mono(totalVs);
  document.getElementById("cAvg").textContent = daysN ? (totalPv/daysN).toFixed(1) : "—";
  document.getElementById("cDays").textContent = daysN ? mono(daysN) : "—";
  let best = "—";
  if(daysN && totalPv>0){
    const ix = data.pageviews.indexOf(Math.max(...data.pageviews));
    const dt = data.days[ix].split("-");
    best = dt[2]+"."+dt[1]+"."+dt[0]+" ("+mono(data.pageviews[ix])+" просм.)";
  }
  document.getElementById("cBest").textContent = best;
  const meta = document.getElementById("meta");
  if(daysN){
    const d0 = data.days[0], d1 = data.days[daysN-1];
    meta.textContent = "Сайт: fedor-help.github.io  ·  период: "+d0+" … "+d1+"  ·  историк: Cloudflare Web Analytics";
  } else {
    meta.textContent = "Сайт: fedor-help.github.io  ·  Cloudflare Web Analytics";
  }
  draw(data);
  renderTable(data);
}

function load(){
  document.getElementById("btn").disabled = true;
  document.getElementById("status").textContent = "Загрузка…";
  fetch("/data", {cache:"no-store"})
    .then(r=>r.json())
    .then(d=>{
      if(d.error){ throw new Error(d.error); }
      chartData = d;
      render(d);
      document.getElementById("status").textContent = "Обновлено: "+new Date().toLocaleTimeString("ru-RU");
    })
    .catch(e=>{
      document.getElementById("status").innerHTML = '<span class="err">Ошибка: '+e.message+'</span>';
    })
    .finally(()=>{ document.getElementById("btn").disabled = false; });
}

document.getElementById("btn").addEventListener("click", load);
load();
</script>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        if self.path.rstrip("/") == "/data" or self.path == "/data/":
            try:
                pv_rows, vs_rows = cws.fetch_days(DAYS)
                series = cws.build_series(pv_rows, vs_rows)
                payload = {
                    "host": cws.SITE_HOST,
                    "days": series["days"],
                    "pageviews": series["pageviews"],
                    "visits": series["visits"],
                    "totals": {
                        "pageviews": sum(series["pageviews"]),
                        "visits": sum(series["visits"]),
                    },
                }
            except Exception as e:
                payload = {"error": str(e)[:300]}
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)
        else:
            body = PAGE.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)


def free_port(preferred):
    s = socket.socket()
    try:
        s.bind(("127.0.0.1", preferred))
    except OSError:
        try:
            s.bind(("127.0.0.1", 0))
            return s.getsockname()[1]
        finally:
            s.close()
    s.close()
    return preferred


def main():
    global PORT, DAYS
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--port", type=int, default=8543)
    args = ap.parse_args()
    DAYS = args.days
    PORT = free_port(args.port)

    if not cws.CF_KEY or not cws.CF_ACCT:
        print("Нет Cloudflare-ключей (D:\\.env)")
        sys.exit(1)

    srv = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    url = f"http://127.0.0.1:{PORT}/"
    threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    print(f"Панель статистики: {url}")
    print("Закрыть — Ctrl+C")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nОстановлено")
        srv.shutdown()


if __name__ == "__main__":
    main()