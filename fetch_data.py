#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AI理财面板 · 行情抓取：读 watchlist.json -> data.json（GitHub Actions 每15分钟运行）"""
import json, re, time, urllib.request, datetime

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120", "Referer": "https://finance.sina.com.cn"}

def http(url, ref=None, timeout=20, enc="utf-8"):
    h = dict(UA)
    if ref: h["Referer"] = ref
    return urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=timeout).read().decode(enc, "ignore")

def fund_name(code):
    for url in [f"http://fund.eastmoney.com/pingzhongdata/{code}.js",
                f"https://fund.eastmoney.com/pingzhongdata/{code}.js"]:
        try:
            t = http(url, ref="http://fund.eastmoney.com/")
            m = re.search(r'fS_name\s*=\s*"([^"]+)"', t)
            if m: return m.group(1)
        except Exception:
            continue
    return code

def fund_data(code):
    try:
        rows = []
        for pg in range(1, 6):
            d = json.loads(http(f"https://api.fund.eastmoney.com/f10/lsjz?fundCode={code}&pageIndex={pg}&pageSize=20",
                                ref="https://fundf10.eastmoney.com/"))
            lst = d["Data"]["LSJZList"]
            rows.extend(lst)
            if len(lst) < 20: break
        hist = []
        for r in reversed(rows):
            try:
                ts = int(datetime.datetime.strptime(r["FSRQ"], "%Y-%m-%d").timestamp() * 1000)
                hist.append([ts, float(r["DWJZ"])])
            except Exception: pass
        latest = rows[0]
        nav = float(latest["DWJZ"])
        pct = float(latest["JZZZL"]) if latest.get("JZZZL") else 0.0
        return {"name": fund_name(code), "nav": nav, "navDate": latest["FSRQ"], "pct": pct, "hist": hist}
    except Exception as e:
        return {"name": code, "error": str(e)[:60]}

def stocks_batch(codes):
    out = {}
    for i in range(0, len(codes), 40):
        chunk = codes[i:i+40]
        t = None
        for attempt in range(3):
            try:
                t = http("https://hq.sinajs.cn/list=" + ",".join(chunk), enc="gbk"); break
            except Exception:
                time.sleep(2)
        if t is None: continue
        for m in re.finditer(r'hq_str_(\w+)="([^"]*)"', t):
            code, payload = m.groups()
            if not payload: continue
            f = payload.split(",")
            try:
                out[code] = {"name": f[0], "prev": float(f[2]), "price": float(f[3]),
                             "time": f[30] if len(f) > 30 else ""}
            except Exception: pass
    return out

def stock_hist(code):
    try:
        t = http(f"https://quotes.sina.cn/cn/api/jsonp_v2.php/var%20x=/CN_MarketDataService.getKLineData?symbol={code}&scale=240&ma=no&datalen=90")
        m = re.search(r'x=\((.*)\)', t, re.S)
        rows = json.loads(m.group(1))
        return [[int(datetime.datetime.strptime(r["day"], "%Y-%m-%d").timestamp() * 1000), float(r["close"])] for r in rows]
    except Exception:
        return []

def main():
    wl = json.load(open("watchlist.json", encoding="utf-8"))
    data = {"updated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "funds": {}, "stocks": {}}
    for c in wl.get("funds", []):
        data["funds"][c] = fund_data(c); time.sleep(0.3)
    snap = stocks_batch(wl.get("stocks", []))
    for c in wl.get("stocks", []):
        if c in snap:
            s = dict(snap[c])
            s["pct"] = round((s["price"] - s["prev"]) / s["prev"] * 100, 2) if s["prev"] else 0
            s["hist"] = stock_hist(c); time.sleep(0.3)
            data["stocks"][c] = s
    json.dump(data, open("data.json", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print("更新于", data["updated"], "| 基金", len(data["funds"]), "| 股票", len(data["stocks"]))

if __name__ == "__main__":
    main()
