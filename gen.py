import requests,pandas as pd,json
U="ASIANPAINT AXISBANK BAJFINANCE BHARTIARTL COALINDIA HCLTECH HDFCBANK HINDUNILVR ICICIBANK INFY KOTAKBANK LT M&M RELIANCE SBIN TATASTEEL TITAN ITC TCS NTPC ONGC SUNPHARMA MARUTI ULTRACEMCO POWERGRID".split()
H={"User-Agent":"Mozilla/5.0"}
def get(t,f="adjclose"):
    r=requests.get("https://query1.finance.yahoo.com/v8/finance/chart/"+requests.utils.quote(t)+"?range=2y&interval=1d",headers=H,timeout=30).json()["chart"]["result"][0]
    q=r["indicators"]["quote"][0]
    ix=pd.to_datetime(r["timestamp"],unit="s").normalize()
    return pd.DataFrame({"c":r["indicators"]["adjclose"][0]["adjclose"] if f=="adjclose" else q["close"],"o":q["open"],"rc":q["close"]},index=ix).dropna()
P=pd.DataFrame({u:get(u+".NS")["c"] for u in U}).ffill();n=get("^NSEI");v=get("^INDIAVIX")
d=P.index[-1];nc=n["c"];m200=nc.rolling(200).mean().iloc[-1];m20=nc.rolling(20).mean().iloc[-1]
gap=(n["o"].iloc[-1]/n["rc"].iloc[-2]-1)*100;vix=v["rc"].iloc[-1]
a50=P.rolling(50).mean().iloc[-1];last=P.iloc[-1];br=int((last>a50).sum())
checks=[["Nifty above 200-day average",bool(nc.iloc[-1]>m200),f"{nc.iloc[-1]:.0f} vs {m200:.0f}"],["Nifty above 20-day average",bool(nc.iloc[-1]>m20),f"{nc.iloc[-1]:.0f} vs {m20:.0f}"],["India VIX between 12 and 20",bool(12<=vix<=20),f"{vix:.1f}"],["Opening gap under 1%",bool(abs(gap)<1),f"{gap:+.2f}% (last day open vs prior close)"],["Breadth: 50%+ stocks above 50-day avg",br>=13,f"{br}/25"]]
mom=(P/P.shift(126)-1).iloc[-1];c=mom[last>a50].sort_values(ascending=False).head(3)
sig=[{"sym":s,"mom6m":round(float(x)*100,1),"ref":round(float(last[s]),1),"qty":0,"stop":round(float(last[s])*0.92,2),"date":str(d.date())} for s,x in c.items()]
label="Trade" if checks[0][1] else "No-trade"
json.dump({"asof":str(d.date()),"label":label,"checks":checks,"signals":sig},open("data.json","w"),indent=1);print(open("data.json").read()[:900])
