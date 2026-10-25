# gen2.py - AlgoNova daily signal generator v2 (paper-only, data-only, no keys)
# Drop-in for skinterior/algonova-data gen.py. Swing strategy preserved; fields additive.
# Adds: (1) price ALERT LEVELS at +10/+15/+20% from ref - Boss's existing profit-alert
#         thresholds. These are alert levels, NOT validated strategy exits; the only
#         validated exit remains the 8% stop (repo gen.py: stop = ref*0.92).
#       (2) Replay stats per signal (method documented in "replayMethod" of output).
import requests, pandas as pd, json, statistics
U="ASIANPAINT AXISBANK BAJFINANCE BHARTIARTL COALINDIA HCLTECH HDFCBANK HINDUNILVR ICICIBANK INFY KOTAKBANK LT M&M RELIANCE SBIN TATASTEEL TITAN ITC TCS NTPC ONGC SUNPHARMA MARUTI ULTRACEMCO POWERGRID".split()
H={"User-Agent":"Mozilla/5.0"}
def get(t,f="adjclose"):
    r=requests.get("https://query1.finance.yahoo.com/v8/finance/chart/"+requests.utils.quote(t)+"?range=2y&interval=1d",headers=H,timeout=30).json()["chart"]["result"][0]
    q=r["indicators"]["quote"][0]
    ix=pd.to_datetime(r["timestamp"],unit="s").normalize()
    return pd.DataFrame({"c":r["indicators"]["adjclose"][0]["adjclose"] if f=="adjclose" else q["close"],"o":q["open"],"rc":q["close"]},index=ix).dropna()
P=pd.DataFrame({u:get(u+".NS")["c"] for u in U}).ffill(); n=get("^NSEI"); v=get("^INDIAVIX")
d=P.index[-1]; nc=n["c"]; m200=nc.rolling(200).mean().iloc[-1]; m20=nc.rolling(20).mean().iloc[-1]
gap=(n["o"].iloc[-1]/n["rc"].iloc[-2]-1)*100; vix=v["rc"].iloc[-1]
a50=P.rolling(50).mean(); last=P.iloc[-1]; br=int((last>a50.iloc[-1]).sum())
checks=[["Nifty above 200-day average",bool(nc.iloc[-1]>m200),f"{nc.iloc[-1]:.0f} vs {m200:.0f}"],["Nifty above 20-day average",bool(nc.iloc[-1]>m20),f"{nc.iloc[-1]:.0f} vs {m20:.0f}"],["India VIX between 12 and 20",bool(12<=vix<=20),f"{vix:.1f}"],["Opening gap under 1%",bool(abs(gap)<1),f"{gap:+.2f}% (last day open vs prior close)"],["Breadth: 50%+ stocks above 50-day avg",br>=13,f"{br}/25"]]
mom=(P/P.shift(126)-1); c=mom.iloc[-1][last>a50.iloc[-1]].sort_values(ascending=False).head(3)

# --- Replay: setup knowable only AFTER close of day t -> entry at close t+1,
# exit 20 trading days later (close t+21). GROSS of costs/slippage.
# A symbol can qualify on consecutive days -> windows overlap (not independent bets).
HOR=20; LAG=1
def replay(sym):
    s=P[sym]; wins=[]
    for i in range(127, len(P)-(HOR+LAG)):
        elig=P.iloc[i]>a50.iloc[i]
        top3=mom.iloc[i][elig].sort_values(ascending=False).head(3)
        if sym in top3.index:
            wins.append(s.iloc[i+LAG+HOR]/s.iloc[i+LAG]-1)
    if len(wins)<3: return {"n":len(wins),"note":"too few replay windows to say anything"}
    return {"n":len(wins),
            "winPct":round(100*sum(1 for w in wins if w>0)/len(wins)),
            "median20dGrossPct":round(100*statistics.median(wins),1)}

sig=[]
for s,x in c.items():
    ref=round(float(last[s]),1)
    sig.append({"sym":s,"mom6m":round(float(x)*100,1),"ref":ref,"qty":0,
        "stop":round(ref*0.92,2),
        "alertLevels":{"a10":round(ref*1.10,2),"a15":round(ref*1.15,2),"a20":round(ref*1.20,2)},
        "replay":replay(s),
        "date":str(d.date())})
label="Trade" if checks[0][1] else "No-trade"
out={"asof":str(d.date()),"label":label,"checks":checks,"signals":sig,
 "replayMethod":"Setup = symbol in daily 6m-momentum top3 among universe members above their own 50dma, computed from close of day t. Entry at close t+1 (signal is only knowable after close t), exit at close 20 trading days later. GROSS of costs and slippage - the app applies 0.25% cost at open in paper P&L. A symbol can qualify on many consecutive days, so windows overlap and n overstates the number of independent bets. winPct = share of windows with positive GROSS return over 20 trading days; it is NOT the odds of hitting an alert level and NOT an expected profit. Small sample, 2y Yahoo data only.",
 "alertNote":"alertLevels are price-alert thresholds (+10/+15/+20% from ref) matching the app's profit alerts. They are NOT validated strategy exits; the only strategy exit remains the 8% stop.",
 "notes":"Paper-only. News/earnings monitor: no reliable free NSE source - not included."}
json.dump(out,open("data.json","w"),indent=1)
print(json.dumps(out,indent=1))
