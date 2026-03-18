"""
Stock Dashboard
===============
Run with:  python MIM_Dashboard_VS.py
Then open: http://127.0.0.1:8051

Dependencies (install once):
    pip install dash dash-bootstrap-components yfinance pandas feedparser requests plotly
"""

import datetime
import os
import feedparser
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output, State

# ─────────────────────────────────────────────────────────────────────────────
# App
# ─────────────────────────────────────────────────────────────────────────────
app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.CYBORG,
        "https://fonts.googleapis.com/css2?family=Nunito+Sans:wght@300;400;600;700;800&display=swap",
    ],
    title="Stock Dashboard",
    suppress_callback_exceptions=True,
)

# ─────────────────────────────────────────────────────────────────────────────
# Theme
# ─────────────────────────────────────────────────────────────────────────────
C = {
    "bg":      "#0d1117",
    "panel":   "#161b22",
    "border":  "#21262d",
    "accent":  "#f0b429",
    "green":   "#3fb950",
    "red":     "#f85149",
    "blue":    "#58a6ff",
    "muted":   "#484f58",
    "text":    "#e6edf3",
    "subtext": "#8b949e",
}

FONT = "'Nunito Sans', 'Segoe UI', sans-serif"

PANEL = {
    "backgroundColor": C["panel"],
    "border": f"1px solid {C['border']}",
    "borderRadius": "10px",
    "padding": "1.25rem",
    "marginBottom": "1.25rem",
}

LBL = {
    "fontFamily": FONT,
    "fontWeight": "700",
    "fontSize": "0.65rem",
    "letterSpacing": "0.08em",
    "textTransform": "uppercase",
    "color": C["subtext"],
    "marginBottom": "0.6rem",
}

NAV_BTN = {
    "backgroundColor": "transparent",
    "border": f"1px solid {C['border']}",
    "borderRadius": "6px",
    "color": C["subtext"],
    "padding": "0.45rem 1rem",
    "fontFamily": FONT,
    "fontSize": "0.82rem",
    "cursor": "pointer",
    "fontWeight": "600",
}

NAV_BTN_ACTIVE = {
    **NAV_BTN,
    "backgroundColor": C["accent"],
    "color": "#000",
    "border": f"1px solid {C['accent']}",
}

MAIN_MENU_BTN = {
    "width": "100%",
    "textAlign": "left",
    "backgroundColor": "transparent",
    "border": f"1px solid {C['border']}",
    "borderRadius": "8px",
    "color": C["subtext"],
    "padding": "0.6rem 0.85rem",
    "fontFamily": FONT,
    "fontSize": "0.82rem",
    "fontWeight": "700",
    "cursor": "pointer",
}

MAIN_MENU_BTN_ACTIVE = {
    **MAIN_MENU_BTN,
    "backgroundColor": C["accent"],
    "color": "#000",
    "border": f"1px solid {C['accent']}",
}

INDICES = {"S&P 500": "^GSPC", "NASDAQ": "^IXIC", "DOW": "^DJI", "VIX": "^VIX"}
PERIODS = ["1mo", "3mo", "6mo", "1y", "2y", "5y"]

# ─────────────────────────────────────────────────────────────────────────────
# Screener universe (~200 major US + International stocks)
# ─────────────────────────────────────────────────────────────────────────────
_RAW_UNIVERSE = [
    "AAPL","MSFT","NVDA","AMZN","GOOGL","META","TSLA","BRK-B","JPM","V",
    "XOM","UNH","MA","JNJ","PG","HD","AVGO","MRK","LLY","ABBV",
    "CVX","PEP","KO","COST","WMT","BAC","MCD","CRM","ACN","TMO",
    "CSCO","ABT","NKE","NFLX","ADBE","AMD","QCOM","TXN","DHR","LIN",
    "NEE","PM","RTX","AMGN","SPGI","HON","UPS","INTC","CAT","INTU",
    "IBM","GS","MS","BLK","SCHW","AXP","C","WFC","USB","PNC",
    "DE","MMM","BA","GE","LMT","NOC","GD","PFE","GILD","BIIB",
    "REGN","VRTX","ISRG","SYK","ZTS","BSX","MDT","AMT","PLD","CCI",
    "EQIX","SPG","O","DLR","WELL","PSA","DIS","CMCSA","T","VZ",
    "CVS","CI","HUM","ELV","HCA","F","GM","WM","RSG","ECL",
    "EMR","ETN","PH","ROK","PYPL","SQ","COIN","MELI","SE","GRAB",
    "SBUX","CMG","DRI","SNOW","PLTR","DDOG","NET","CRWD","ZS","PANW",
    "FTNT","OKTA","UBER","LYFT","ABNB","BKNG","EXPE","DASH","RBLX",
    "ORCL","NOW","WDAY","HUBS","TEAM","VEEV","CDNS","SNPS",
    # International ADRs
    "ASML","TSM","BABA","JD","PDD","BIDU","NIO","XPEV","TCEHY",
    "SONY","SNY","NVS","RHHBY","AZN","GSK","BP","SHEL",
    "HSBC","UBS","DB","BCS","SAN","ING",
    "SAP","SHOP","ENB","TD","RY","BNS","BMO","CM","MFC",
    "INFY","WIT","HDB","IBN","VALE","ITUB","NU",
    "RIO","BHP","GLEN",
]
_seen_u = set()
SCREENER_UNIVERSE = [t for t in _RAW_UNIVERSE if not (t in _seen_u or _seen_u.add(t))]

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def parse_tickers(raw):
    import re
    if not raw:
        return []
    return [t for t in re.split(r"[\s,;]+", raw.upper().strip()) if t]


def fetch_earnings(tickers):
    rows = []
    today  = datetime.date.today()
    cutoff = today + datetime.timedelta(days=30)
    for ticker in tickers:
        try:
            info = yf.Ticker(ticker).info
            ts = info.get("earningsTimestamp") or info.get("earningsTimestampStart")
            if ts:
                dt = datetime.date.fromtimestamp(ts)
                if today <= dt <= cutoff:
                    rows.append({"Ticker": ticker,
                                 "Earnings Date": dt.strftime("%d %b %Y"),
                                 "Days Away": (dt - today).days,
                                 "_date": dt})
        except Exception:
            pass
    if not rows:
        return pd.DataFrame(columns=["Ticker", "Earnings Date", "Days Away"])
    df = pd.DataFrame(rows).sort_values("_date")
    return df.drop(columns=["_date"]).reset_index(drop=True)


def fetch_prices(tickers):
    rows = []
    for ticker in tickers:
        try:
            fi    = yf.Ticker(ticker).fast_info
            price = round(fi.last_price, 2)
            prev  = round(fi.previous_close, 2)
            chg   = round(price - prev, 2)
            pct   = round((chg / prev) * 100, 2) if prev else 0
            mc    = fi.market_cap
            cap   = (f"${mc/1e9:.1f}B" if mc and mc >= 1e9
                     else f"${mc/1e6:.1f}M" if mc else "—")
            rows.append({"Ticker": ticker,
                         "Price":   f"${price:,.2f}",
                         "Change":  f"{'+' if chg>=0 else ''}{chg:.2f}",
                         "Chg %":   f"{'+' if pct>=0 else ''}{pct:.2f}%",
                         "Mkt Cap": cap,
                         "_chg":    chg})
        except Exception:
            rows.append({"Ticker": ticker, "Price": "—", "Change": "—",
                         "Chg %": "—", "Mkt Cap": "—", "_chg": 0})
    return pd.DataFrame(rows)


def fetch_index_data():
    results = []
    for name, sym in INDICES.items():
        try:
            fi  = yf.Ticker(sym).fast_info
            p   = fi.last_price
            prv = fi.previous_close
            chg = p - prv
            pct = (chg / prv) * 100 if prv else 0
            results.append({"name": name, "price": p, "chg": chg, "pct": pct})
        except Exception:
            results.append({"name": name, "price": None, "chg": 0, "pct": 0})
    return results


def fetch_news(tickers, max_per=3):
    articles = []
    for ticker in tickers:
        url = (f"https://feeds.finance.yahoo.com/rss/2.0/headline"
               f"?s={ticker}&region=US&lang=en-US")
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:max_per]:
                articles.append({"ticker":    ticker,
                                  "title":     entry.get("title", ""),
                                  "link":      entry.get("link", "#"),
                                  "published": entry.get("published", "")})
        except Exception:
            pass
    return articles


def build_correlation_data(tickers, frequency):
    freq_map = {
        "daily":   {"interval": "1d",  "period": "1y"},
        "weekly":  {"interval": "1wk", "period": "5y"},
        "monthly": {"interval": "1mo", "period": "10y"},
    }
    cfg = freq_map.get(frequency, freq_map["daily"])

    # yfinance returns a Series for a single ticker; force DataFrame shape.
    close = yf.download(
        tickers=tickers,
        period=cfg["period"],
        interval=cfg["interval"],
        auto_adjust=True,
        progress=False,
    )

    if close is None or close.empty:
        return None, []

    if isinstance(close.columns, pd.MultiIndex):
        price_df = close.get("Close")
    else:
        price_df = close

    if isinstance(price_df, pd.Series):
        price_df = price_df.to_frame(name=tickers[0])

    # Keep only requested tickers that actually returned data.
    available = [t for t in tickers if t in price_df.columns]
    if not available:
        return None, []

    price_df = price_df[available].dropna(how="all")
    returns = price_df.pct_change().dropna(how="all")
    if returns.empty:
        return None, available

    corr = returns.corr().round(3)
    return corr, available


def build_portfolio_performance_data(tickers, weights, frequency):
    freq_map = {
        "daily":   {"interval": "1d",  "period": "1y"},
        "weekly":  {"interval": "1wk", "period": "5y"},
        "monthly": {"interval": "1mo", "period": "10y"},
    }
    cfg = freq_map.get(frequency, freq_map["weekly"])

    close = yf.download(
        tickers=tickers,
        period=cfg["period"],
        interval=cfg["interval"],
        auto_adjust=True,
        progress=False,
    )

    if close is None or close.empty:
        return None, None, None

    if isinstance(close.columns, pd.MultiIndex):
        price_df = close.get("Close")
    else:
        price_df = close

    if isinstance(price_df, pd.Series):
        price_df = price_df.to_frame(name=tickers[0])

    available = [t for t in tickers if t in price_df.columns]
    if not available:
        return None, None, None

    weight_series = pd.Series(weights, index=tickers)
    weight_series = weight_series.reindex(available).dropna()
    if weight_series.empty or weight_series.sum() <= 0:
        return None, None, None

    # Re-normalize so weights always add to 100% after any missing tickers are removed.
    weight_series = weight_series / weight_series.sum()

    aligned_prices = price_df[weight_series.index].dropna(how="any")
    if aligned_prices.empty:
        return None, None, None

    rebased_components = aligned_prices.divide(aligned_prices.iloc[0]).mul(100)
    portfolio_index = rebased_components.mul(weight_series, axis=1).sum(axis=1)
    return portfolio_index, rebased_components, weight_series


def build_price_chart(ticker, period="6mo"):
    try:
        df = yf.Ticker(ticker).history(period=period)
        if df.empty:
            return go.Figure()
        color    = C["green"] if df["Close"].iloc[-1] >= df["Close"].iloc[0] else C["red"]
        rgb      = "63,185,80" if color == C["green"] else "248,81,73"
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df.index, y=df["Close"],
            mode="lines",
            line=dict(color=color, width=2),
            fill="tozeroy",
            fillcolor=f"rgba({rgb},0.07)",
            name="Price",
            hovertemplate="$%{y:.2f}<extra></extra>",
        ))
        fig.add_trace(go.Bar(
            x=df.index, y=df["Volume"],
            name="Volume",
            marker_color="rgba(88,166,255,0.2)",
            yaxis="y2",
        ))
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family=FONT, color=C["subtext"], size=11),
            margin=dict(l=0, r=0, t=10, b=0),
            xaxis=dict(showgrid=False, color=C["muted"], linecolor=C["border"]),
            yaxis=dict(showgrid=True, gridcolor=C["border"], color=C["subtext"],
                       tickprefix="$", side="right"),
            yaxis2=dict(overlaying="y", side="left", showgrid=False,
                        showticklabels=False,
                        range=[0, df["Volume"].max() * 6]),
            legend=dict(orientation="h", yanchor="bottom", y=1,
                        font=dict(size=10, family=FONT)),
            hovermode="x unified",
        )
        return fig
    except Exception:
        return go.Figure()


def build_valuation_table(ticker):
    try:
        info = yf.Ticker(ticker).info
        metrics = {
            "P/E Ratio (TTM)":        info.get("trailingPE"),
            "Forward P/E":            info.get("forwardPE"),
            "PEG Ratio":              info.get("pegRatio"),
            "Price / Book":           info.get("priceToBook"),
            "Price / Sales (TTM)":    info.get("priceToSalesTrailing12Months"),
            "EV / EBITDA":            info.get("enterpriseToEbitda"),
            "EV / Revenue":           info.get("enterpriseToRevenue"),
            "Market Cap":             info.get("marketCap"),
            "Enterprise Value":       info.get("enterpriseValue"),
            "Beta":                   info.get("beta"),
            "52w High":               info.get("fiftyTwoWeekHigh"),
            "52w Low":                info.get("fiftyTwoWeekLow"),
            "Dividend Yield":         info.get("dividendYield"),
            "Return on Equity":       info.get("returnOnEquity"),
            "Return on Assets":       info.get("returnOnAssets"),
            "Profit Margin":          info.get("profitMargins"),
            "Gross Margin":           info.get("grossMargins"),
            "Revenue Growth (YoY)":   info.get("revenueGrowth"),
            "Earnings Growth (YoY)":  info.get("earningsGrowth"),
            "Debt / Equity":          info.get("debtToEquity"),
        }

        pct_keys = {"Dividend Yield", "Return on Equity", "Return on Assets",
                    "Profit Margin", "Gross Margin", "Revenue Growth (YoY)",
                    "Earnings Growth (YoY)"}
        big_keys = {"Market Cap", "Enterprise Value"}

        def fmt(k, v):
            if v is None:
                return "—"
            if k in pct_keys:
                return f"{v*100:.2f}%"
            if k in big_keys:
                return f"${v/1e9:.2f}B" if v >= 1e9 else f"${v/1e6:.1f}M"
            if k in {"52w High", "52w Low"}:
                return f"${v:,.2f}"
            return f"{v:.2f}"

        rows = []
        keys = list(metrics.keys())
        # Two-column layout
        for i in range(0, len(keys), 2):
            cells = []
            for j in range(2):
                if i + j < len(keys):
                    k = keys[i + j]
                    v = fmt(k, metrics[k])
                    cells += [
                        html.Td(k, style={"color": C["subtext"], "padding": "0.42rem 0.75rem",
                                           "borderBottom": f"1px solid {C['border']}",
                                           "fontSize": "0.8rem", "fontFamily": FONT,
                                           "width": "30%"}),
                        html.Td(v, style={"color": C["text"], "fontWeight": "600",
                                           "padding": "0.42rem 0.75rem",
                                           "borderBottom": f"1px solid {C['border']}",
                                           "fontSize": "0.8rem", "textAlign": "right",
                                           "fontFamily": FONT, "width": "20%"}),
                    ]
                else:
                    cells += [html.Td(), html.Td()]
            rows.append(html.Tr(cells))

        return html.Table(html.Tbody(rows),
                          style={"width": "100%", "borderCollapse": "collapse"})
    except Exception as e:
        return html.Div(f"Could not load valuation data: {e}",
                        style={"color": C["muted"], "fontSize": "0.82rem", "fontFamily": FONT})


# Preferred row order for each statement type
INCOME_ORDER = [
    "Total Revenue", "Revenue", "Gross Profit", "Cost Of Revenue",
    "Operating Revenue", "Operating Income", "Operating Expense",
    "Selling General Administrative", "Research And Development",
    "Depreciation Amortization Depletion", "Depreciation And Amortization In Income Statement",
    "Ebit", "Ebitda", "Interest Expense", "Interest Income",
    "Pretax Income", "Tax Provision", "Net Income",
    "Net Income Common Stockholders", "Diluted EPS", "Basic EPS",
    "Diluted Average Shares", "Basic Average Shares",
]

BALANCE_ORDER = [
    "Total Assets", "Current Assets", "Cash And Cash Equivalents",
    "Cash Cash Equivalents And Short Term Investments",
    "Receivables", "Inventory", "Other Current Assets",
    "Non Current Assets", "Net PPE", "Goodwill", "Intangible Assets",
    "Other Non Current Assets",
    "Total Liabilities Net Minority Interest", "Current Liabilities",
    "Accounts Payable", "Current Debt", "Other Current Liabilities",
    "Non Current Liabilities", "Long Term Debt", "Other Non Current Liabilities",
    "Total Equity Gross Minority Interest", "Stockholders Equity",
    "Common Stock", "Retained Earnings",
]

CASHFLOW_ORDER = [
    "Operating Cash Flow", "Cash Flow From Continuing Operating Activities",
    "Net Income From Continuing Operations",
    "Depreciation Amortization Depletion", "Change In Working Capital",
    "Change In Receivables", "Change In Inventory", "Change In Payables",
    "Investing Cash Flow", "Cash Flow From Continuing Investing Activities",
    "Capital Expenditure", "Purchase Of Investment", "Sale Of Investment",
    "Financing Cash Flow", "Cash Flow From Continuing Financing Activities",
    "Repayment Of Debt", "Issuance Of Debt", "Common Stock Issuance",
    "Repurchase Of Capital Stock", "Cash Dividends Paid",
    "Free Cash Flow", "Changes In Cash",
]


def get_edgar_10k_url(ticker):
    """Look up the latest 10-K filing URL on SEC EDGAR."""
    try:
        import requests as req
        # Get CIK from ticker
        r = req.get(
            f"https://efts.sec.gov/LATEST/search-index?q=%22{ticker}%22&dateRange=custom"
            f"&startdt=2020-01-01&forms=10-K",
            headers={"User-Agent": "stock-dashboard contact@example.com"},
            timeout=5,
        )
        # Simpler: use the EDGAR company search
        r2 = req.get(
            f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&company="
            f"&CIK={ticker}&type=10-K&dateb=&owner=include&count=1&search_text=",
            headers={"User-Agent": "stock-dashboard contact@example.com"},
            timeout=5,
        )
        # Return the EDGAR full-text search URL — always works as a fallback
        return (f"https://efts.sec.gov/LATEST/search-index?q=%22{ticker}%22"
                f"&forms=10-K&dateRange=custom&startdt=2022-01-01")
    except Exception:
        return None


def get_edgar_filing_url(ticker):
    """Return the URL for the most recent 10-K filing viewer on EDGAR."""
    try:
        import requests as req
        # EDGAR full-text search — reliable public endpoint
        url = (f"https://efts.sec.gov/LATEST/search-index?q=%22{ticker}%22"
               f"&forms=10-K")
        # Better: use the EDGAR company facts / submissions endpoint
        # First get CIK
        r = req.get(
            "https://efts.sec.gov/LATEST/search-index?q="
            f"&forms=10-K&dateRange=custom&startdt=2023-01-01",
            headers={"User-Agent": "stock-dashboard contact@example.com"},
            timeout=4,
        )
        # Most reliable: direct EDGAR search link that always resolves
        return (f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany"
                f"&CIK={ticker}&type=10-K&dateb=&owner=include&count=5")
    except Exception:
        return f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={ticker}&type=10-K&dateb=&owner=include&count=5"


def fetch_latest_10k_url(ticker):
    """
    Use SEC EDGAR submissions API to get the actual 10-K filing document URL.
    Returns a direct link to the filing index page.
    """
    try:
        import requests as req

        # Step 1: get CIK from EDGAR company search
        search_url = f"https://efts.sec.gov/LATEST/search-index?q=%22{ticker}%22&forms=10-K"
        headers    = {"User-Agent": "stock-dashboard research@example.com"}

        # Use the submissions endpoint — need CIK first
        # Try ticker → CIK mapping via EDGAR
        tickers_json = req.get(
            "https://www.sec.gov/files/company_tickers.json",
            headers=headers, timeout=6
        ).json()

        cik = None
        for entry in tickers_json.values():
            if entry.get("ticker", "").upper() == ticker.upper():
                cik = str(entry["cik_str"]).zfill(10)
                break

        if not cik:
            return f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={ticker}&type=10-K&dateb=&owner=include&count=5"

        # Step 2: get submissions for this CIK
        subs = req.get(
            f"https://data.sec.gov/submissions/CIK{cik}.json",
            headers=headers, timeout=6
        ).json()

        filings = subs.get("filings", {}).get("recent", {})
        forms   = filings.get("form", [])
        accNums = filings.get("accessionNumber", [])
        dates   = filings.get("filingDate", [])

        for form, acc, date in zip(forms, accNums, dates):
            if form == "10-K":
                acc_clean = acc.replace("-", "")
                filing_url = (f"https://www.sec.gov/Archives/edgar/data/"
                              f"{int(cik)}/{acc_clean}/{acc}-index.htm")
                return filing_url

        # Fallback to browse page
        return f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&type=10-K&dateb=&owner=include&count=5"

    except Exception:
        return f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={ticker}&type=10-K&dateb=&owner=include&count=5"


def reorder_df(df, preferred_order):
    """Reorder DataFrame rows to match preferred_order, appending any extras at the end."""
    existing = list(df.index)
    ordered  = [r for r in preferred_order if r in existing]
    extras   = [r for r in existing if r not in ordered]
    return df.loc[ordered + extras]


def build_financials(ticker, stmt_type="income"):
    try:
        t = yf.Ticker(ticker)
        label_map = {
            "income":   ("Income Statement",     t.financials,   INCOME_ORDER),
            "balance":  ("Balance Sheet",         t.balance_sheet, BALANCE_ORDER),
            "cashflow": ("Cash Flow Statement",   t.cashflow,     CASHFLOW_ORDER),
        }
        title, df, preferred_order = label_map[stmt_type]

        if df is None or df.empty:
            return html.Div("No data available.",
                            style={"color": C["muted"], "fontSize": "0.82rem", "fontFamily": FONT})

        df   = df.dropna(how="all")
        df   = reorder_df(df, preferred_order)
        cols = [str(c)[:10] for c in df.columns]

        # Get EDGAR 10-K link (only fetch once per call)
        edgar_url = fetch_latest_10k_url(ticker)
        show_link = stmt_type == "income"   # show link hint on income stmt

        def fmt_val(v):
            try:
                v = float(v)
                if abs(v) >= 1e9:
                    return f"${v/1e9:.2f}B"
                if abs(v) >= 1e6:
                    return f"${v/1e6:.1f}M"
                return f"${v:,.0f}"
            except Exception:
                return "—"

        th_style = {"padding": "0.35rem 0.75rem", "fontSize": "0.65rem",
                    "textTransform": "uppercase", "letterSpacing": "0.07em",
                    "borderBottom": f"2px solid {C['border']}", "fontFamily": FONT}

        header = html.Thead(html.Tr(
            [html.Th("", style={**th_style, "color": C["muted"]})] +
            [html.Th(c,  style={**th_style, "color": C["subtext"], "textAlign": "right"})
             for c in cols]
        ))

        # Rows that get a clickable EDGAR link on their values
        LINKABLE_ROWS = {
            "Total Revenue", "Revenue", "Gross Profit", "Net Income",
            "Operating Income", "Ebitda", "Operating Cash Flow", "Free Cash Flow",
            "Total Assets", "Total Liabilities Net Minority Interest",
        }

        body_rows = []
        for idx, row in df.iterrows():
            is_linkable  = str(idx) in LINKABLE_ROWS
            is_highlight = str(idx) in {"Total Revenue", "Revenue", "Gross Profit",
                                         "Net Income", "Operating Income"}

            label_cell = html.Td(
                str(idx),
                style={"color": C["accent"] if is_highlight else C["subtext"],
                       "padding": "0.38rem 0.75rem",
                       "borderBottom": f"1px solid {C['border']}",
                       "fontSize": "0.78rem", "fontFamily": FONT,
                       "whiteSpace": "nowrap",
                       "fontWeight": "700" if is_highlight else "400"},
            )

            value_cells = []
            for v in row:
                formatted = fmt_val(v)
                if is_linkable and edgar_url and formatted != "—":
                    cell = html.Td(
                        html.A(
                            formatted,
                            href=edgar_url,
                            target="_blank",
                            title="Open latest 10-K on SEC EDGAR",
                            style={
                                "color": C["blue"],
                                "textDecoration": "none",
                                "fontWeight": "600",
                                "borderBottom": f"1px dashed {C['blue']}",
                                "cursor": "pointer",
                            },
                        ),
                        style={"padding": "0.38rem 0.75rem", "textAlign": "right",
                               "borderBottom": f"1px solid {C['border']}",
                               "fontSize": "0.78rem", "fontFamily": FONT},
                    )
                else:
                    cell = html.Td(
                        formatted,
                        style={"color": C["text"] if formatted != "—" else C["muted"],
                               "fontWeight": "600" if is_highlight else "400",
                               "padding": "0.38rem 0.75rem", "textAlign": "right",
                               "borderBottom": f"1px solid {C['border']}",
                               "fontSize": "0.78rem", "fontFamily": FONT},
                    )
                value_cells.append(cell)

            body_rows.append(html.Tr(
                [label_cell] + value_cells,
                style={"backgroundColor": "rgba(88,166,255,0.04)" if is_highlight else "transparent"},
            ))

        hint = html.Div(
            [html.Span("🔗 ", style={"fontSize": "0.7rem"}),
             html.Span("Blue figures link directly to the latest 10-K filing on SEC EDGAR.",
                       style={"color": C["muted"], "fontSize": "0.68rem", "fontFamily": FONT})],
            style={"marginBottom": "0.65rem"}
        ) if show_link else html.Div()

        return html.Div([
            html.Div(title, style=LBL),
            hint,
            html.Div(
                html.Table([header, html.Tbody(body_rows)],
                           style={"width": "100%", "borderCollapse": "collapse"}),
                style={"overflowX": "auto"},
            ),
        ])
    except Exception as e:
        return html.Div(f"Could not load data: {e}",
                        style={"color": C["muted"], "fontSize": "0.82rem", "fontFamily": FONT})


# ─────────────────────────────────────────────────────────────────────────────
# Layout helpers
# ─────────────────────────────────────────────────────────────────────────────

def index_card(name, price, chg, pct):
    col  = C["green"] if chg >= 0 else C["red"]
    sign = "▲" if chg >= 0 else "▼"
    ps   = f"{price:,.2f}" if price else "—"
    return html.Div([
        html.Div(name, style={"color": C["subtext"], "fontSize": "0.7rem",
                               "fontFamily": FONT, "marginBottom": "4px"}),
        html.Div(ps,   style={"color": C["text"], "fontSize": "1.2rem",
                               "fontWeight": "700", "fontFamily": FONT}),
        html.Div(f"{sign} {abs(pct):.2f}%",
                 style={"color": col, "fontSize": "0.75rem", "fontFamily": FONT}),
    ], style={"backgroundColor": C["bg"], "border": f"1px solid {C['border']}",
              "borderRadius": "10px", "padding": "1rem",
              "flex": "1", "minWidth": "130px"})


# ─────────────────────────────────────────────────────────────────────────────
# Layout
# ─────────────────────────────────────────────────────────────────────────────
app.layout = html.Div(style={
    "backgroundColor": C["bg"],
    "minHeight": "100vh",
    "padding": "1.75rem 2rem",
    "fontFamily": FONT,
    "color": C["text"],
}, children=[

    # Title bar
    html.Div([
        html.Div("📈", style={"fontSize": "1.9rem"}),
        html.Div([
            html.H1("Stock Dashboard",
                    style={"margin": 0, "fontFamily": FONT, "fontWeight": "800",
                           "fontSize": "1.7rem", "color": C["text"]}),
            html.Div("Live market · Earnings · News · Stock Analyser",
                     style={"color": C["subtext"], "fontSize": "0.75rem",
                            "marginTop": "2px", "fontFamily": FONT}),
        ]),
        html.Div(id="last-updated",
                 style={"marginLeft": "auto", "color": C["muted"],
                        "fontSize": "0.7rem", "alignSelf": "flex-end", "fontFamily": FONT}),
    ], style={"display": "flex", "alignItems": "center", "gap": "1rem", "marginBottom": "1.5rem"}),

    # Holdings input (global)
    html.Div([
        html.Div("Your Holdings", style=LBL),
        html.Div([
            dcc.Input(id="ticker-input", type="text",
                      placeholder="e.g. AAPL, MSFT, TSLA, NVDA", debounce=False,
                      style={"backgroundColor": C["bg"], "border": f"1px solid {C['accent']}",
                             "borderRadius": "8px", "color": C["text"],
                             "padding": "0.55rem 1rem", "fontFamily": FONT,
                             "fontSize": "0.85rem", "flex": "1", "outline": "none"}),
            html.Button("Refresh", id="refresh-btn", n_clicks=0,
                        style={"backgroundColor": C["accent"], "color": "#000",
                               "border": "none", "borderRadius": "8px",
                               "padding": "0.55rem 1.4rem", "fontFamily": FONT,
                               "fontWeight": "700", "fontSize": "0.85rem", "cursor": "pointer"}),
        ], style={"display": "flex", "gap": "0.75rem"}),
        html.Div("Enter tickers separated by commas, then click Refresh.",
                 style={"color": C["muted"], "fontSize": "0.68rem",
                        "marginTop": "0.4rem", "fontFamily": FONT}),
    ], style=PANEL),

    # Main menu + section container
    html.Div([
        html.Div([
            html.Div("Menu", style={**LBL, "marginBottom": "0.5rem"}),
            html.Button("Dashboard", id="menu-dashboard", n_clicks=0, style=MAIN_MENU_BTN_ACTIVE),
            html.Button("News", id="menu-news", n_clicks=0, style=MAIN_MENU_BTN),
            html.Button("Stock Analyser", id="menu-analyser", n_clicks=0, style=MAIN_MENU_BTN),
            html.Button("Screener", id="menu-screener", n_clicks=0, style=MAIN_MENU_BTN),
            html.Button("Correlation", id="menu-correlation", n_clicks=0, style=MAIN_MENU_BTN),
            html.Button("Performance", id="menu-performance", n_clicks=0, style=MAIN_MENU_BTN),
            dcc.Store(id="active-main-menu", data="dashboard"),
        ], style={**PANEL, "width": "220px", "padding": "0.9rem", "display": "flex",
                  "flexDirection": "column", "gap": "0.45rem", "position": "sticky", "top": "1rem"}),

        html.Div([
            html.Div([
                html.Div([
                    html.Div("Market Overview", style=LBL),
                    html.Div(id="index-cards",
                             style={"display": "flex", "gap": "0.75rem", "flexWrap": "wrap"}),
                ], style=PANEL),

                html.Div([
                    html.Div([
                        html.Div("Upcoming Earnings · Next 30 Days", style=LBL),
                        html.Div(id="earnings-legend", style={"marginBottom": "0.65rem"}),
                        html.Div(id="earnings-table"),
                    ], style={**PANEL, "flex": "1", "minWidth": "280px"}),
                    html.Div([
                        html.Div("Portfolio Summary", style=LBL),
                        html.Div(id="portfolio-table"),
                    ], style={**PANEL, "flex": "1", "minWidth": "280px"}),
                ], style={"display": "flex", "gap": "1.25rem", "flexWrap": "wrap"}),
            ], id="section-dashboard", style={"display": "block"}),

            html.Div([
                html.Div([
                    html.Div("News Feed · Your Holdings", style=LBL),
                    html.Div(id="news-feed"),
                ], style=PANEL),
            ], id="section-news", style={"display": "none"}),

            html.Div([
                html.Div([
                    html.Div("Stock Analyser", style={**LBL, "color": C["accent"], "fontSize": "0.72rem"}),

                    html.Div([
                        dcc.Input(id="lookup-input", type="text",
                                  placeholder="Enter a ticker  e.g. NKE, AAPL, TSLA",
                                  debounce=False,
                                  style={"backgroundColor": C["bg"],
                                         "border": f"1px solid {C['blue']}",
                                         "borderRadius": "8px", "color": C["text"],
                                         "padding": "0.55rem 1rem", "fontFamily": FONT,
                                         "fontSize": "0.85rem", "flex": "1", "outline": "none"}),
                        html.Button("Search", id="lookup-btn", n_clicks=0,
                                    style={"backgroundColor": C["blue"], "color": "#000",
                                           "border": "none", "borderRadius": "8px",
                                           "padding": "0.55rem 1.4rem", "fontFamily": FONT,
                                           "fontWeight": "700", "fontSize": "0.85rem", "cursor": "pointer"}),
                    ], style={"display": "flex", "gap": "0.75rem", "marginBottom": "1rem"}),

                    html.Div(id="stock-header"),

                    html.Div([
                        html.Button("Price Chart",       id="tab-chart",     n_clicks=0, style=NAV_BTN_ACTIVE),
                        html.Button("Valuation Metrics", id="tab-valuation", n_clicks=0, style=NAV_BTN),
                        html.Button("Income Statement",  id="tab-income",    n_clicks=0, style=NAV_BTN),
                        html.Button("Balance Sheet",     id="tab-balance",   n_clicks=0, style=NAV_BTN),
                        html.Button("Cash Flow",         id="tab-cashflow",  n_clicks=0, style=NAV_BTN),
                    ], id="tab-nav",
                       style={"display": "none", "gap": "0.5rem", "flexWrap": "wrap", "marginBottom": "1rem"}),

                    html.Div(
                        [html.Div("Period:", style={"color": C["subtext"], "fontSize": "0.75rem",
                                                    "alignSelf": "center", "fontFamily": FONT})] +
                        [html.Button(p, id=f"period-{p}", n_clicks=0,
                                     style={**NAV_BTN,
                                            "padding": "0.3rem 0.7rem", "fontSize": "0.75rem",
                                            **({"backgroundColor": C["accent"], "color": "#000",
                                                "border": f"1px solid {C['accent']}"} if p == "6mo" else {})})
                         for p in PERIODS],
                        id="period-nav",
                        style={"display": "none", "gap": "0.4rem", "alignItems": "center",
                               "marginBottom": "0.75rem", "flexWrap": "wrap"},
                    ),

                    html.Div(id="stock-content"),

                    dcc.Store(id="active-tab",    data="chart"),
                    dcc.Store(id="active-period", data="6mo"),
                    dcc.Store(id="active-ticker", data=""),
                ], style=PANEL),
            ], id="section-analyser", style={"display": "none"}),

            html.Div([
                html.Div([
                    html.Div("Stock Screener", style={**LBL, "color": C["green"], "fontSize": "0.72rem"}),

                    html.Div([
                        html.Div([
                            html.Div("Add extra tickers (optional):", style={**LBL, "marginBottom": "0.3rem"}),
                            dcc.Input(id="screener-extra", type="text",
                                      placeholder="e.g. ABNB, GRAB, CRH",
                                      style={"backgroundColor": C["bg"], "border": f"1px solid {C['border']}",
                                             "borderRadius": "8px", "color": C["text"],
                                             "padding": "0.5rem 0.9rem", "fontFamily": FONT,
                                             "fontSize": "0.82rem", "width": "100%", "outline": "none"}),
                        ], style={"flex": "1"}),

                        html.Div([
                            html.Div("P/E max:", style={**LBL, "marginBottom": "0.3rem"}),
                            dcc.Input(id="f-pe-max", type="number", placeholder="e.g. 30",
                                      style={"backgroundColor": C["bg"], "border": f"1px solid {C['border']}",
                                             "borderRadius": "8px", "color": C["text"],
                                             "padding": "0.5rem 0.7rem", "fontFamily": FONT,
                                             "fontSize": "0.82rem", "width": "100%", "outline": "none"}),
                        ], style={"width": "90px"}),

                        html.Div([
                            html.Div("EV/EBITDA max:", style={**LBL, "marginBottom": "0.3rem"}),
                            dcc.Input(id="f-ev-max", type="number", placeholder="e.g. 20",
                                      style={"backgroundColor": C["bg"], "border": f"1px solid {C['border']}",
                                             "borderRadius": "8px", "color": C["text"],
                                             "padding": "0.5rem 0.7rem", "fontFamily": FONT,
                                             "fontSize": "0.82rem", "width": "100%", "outline": "none"}),
                        ], style={"width": "110px"}),

                        html.Div([
                            html.Div("Profit Margin min %:", style={**LBL, "marginBottom": "0.3rem"}),
                            dcc.Input(id="f-margin-min", type="number", placeholder="e.g. 10",
                                      style={"backgroundColor": C["bg"], "border": f"1px solid {C['border']}",
                                             "borderRadius": "8px", "color": C["text"],
                                             "padding": "0.5rem 0.7rem", "fontFamily": FONT,
                                             "fontSize": "0.82rem", "width": "100%", "outline": "none"}),
                        ], style={"width": "130px"}),

                        html.Div([
                            html.Div("Rev Growth min %:", style={**LBL, "marginBottom": "0.3rem"}),
                            dcc.Input(id="f-revgrowth-min", type="number", placeholder="e.g. 5",
                                      style={"backgroundColor": C["bg"], "border": f"1px solid {C['border']}",
                                             "borderRadius": "8px", "color": C["text"],
                                             "padding": "0.5rem 0.7rem", "fontFamily": FONT,
                                             "fontSize": "0.82rem", "width": "100%", "outline": "none"}),
                        ], style={"width": "120px"}),

                        html.Div([
                            html.Div("Div Yield min %:", style={**LBL, "marginBottom": "0.3rem"}),
                            dcc.Input(id="f-div-min", type="number", placeholder="e.g. 1",
                                      style={"backgroundColor": C["bg"], "border": f"1px solid {C['border']}",
                                             "borderRadius": "8px", "color": C["text"],
                                             "padding": "0.5rem 0.7rem", "fontFamily": FONT,
                                             "fontSize": "0.82rem", "width": "100%", "outline": "none"}),
                        ], style={"width": "110px"}),

                        html.Div([
                            html.Div("Debt/Equity max:", style={**LBL, "marginBottom": "0.3rem"}),
                            dcc.Input(id="f-de-max", type="number", placeholder="e.g. 2",
                                      style={"backgroundColor": C["bg"], "border": f"1px solid {C['border']}",
                                             "borderRadius": "8px", "color": C["text"],
                                             "padding": "0.5rem 0.7rem", "fontFamily": FONT,
                                             "fontSize": "0.82rem", "width": "100%", "outline": "none"}),
                        ], style={"width": "110px"}),

                    ], style={"display": "flex", "gap": "0.75rem", "flexWrap": "wrap",
                              "alignItems": "flex-end", "marginBottom": "1rem"}),

                    html.Div([
                        html.Div([
                            html.Div("Sector:", style={**LBL, "marginBottom": "0.3rem"}),
                            dcc.Dropdown(
                                id="f-sector",
                                options=[{"label": s, "value": s} for s in [
                                    "All","Technology","Healthcare","Financials","Consumer Cyclical",
                                    "Consumer Defensive","Industrials","Energy","Utilities",
                                    "Real Estate","Communication Services","Basic Materials",
                                ]],
                                value="All",
                                clearable=False,
                                style={"width": "200px", "fontSize": "0.82rem"},
                            ),
                        ]),
                        html.Div(style={"flex": "1"}),
                        html.Button("▶  Run Screen", id="screener-run", n_clicks=0, style={
                            "backgroundColor": C["green"], "color": "#000", "border": "none",
                            "borderRadius": "8px", "padding": "0.55rem 1.6rem",
                            "fontFamily": FONT, "fontWeight": "700", "fontSize": "0.85rem",
                            "cursor": "pointer", "alignSelf": "flex-end",
                        }),
                        html.Button("⬇  Download CSV", id="screener-download-btn", n_clicks=0, style={
                            "backgroundColor": "transparent", "color": C["green"],
                            "border": f"1px solid {C['green']}",
                            "borderRadius": "8px", "padding": "0.55rem 1.2rem",
                            "fontFamily": FONT, "fontWeight": "600", "fontSize": "0.82rem",
                            "cursor": "pointer", "alignSelf": "flex-end",
                        }),
                        dcc.Download(id="screener-download"),
                    ], style={"display": "flex", "gap": "0.75rem", "alignItems": "flex-end",
                              "marginBottom": "1rem", "flexWrap": "wrap"}),

                    html.Div(id="screener-status",
                             style={"color": C["muted"], "fontSize": "0.75rem",
                                    "fontFamily": FONT, "marginBottom": "0.65rem"}),
                    html.Div(id="screener-results"),

                    dcc.Store(id="screener-data-store"),
                ], style=PANEL),
            ], id="section-screener", style={"display": "none"}),

            html.Div([
                html.Div([
                    html.Div("Stock Correlation Matrix", style={**LBL, "color": C["blue"], "fontSize": "0.72rem"}),
                    html.Div("Compare how your selected stocks move together.",
                             style={"color": C["muted"], "fontSize": "0.78rem", "marginBottom": "0.8rem",
                                    "fontFamily": FONT}),

                    html.Div([
                        html.Div([
                            html.Div("Tickers", style={**LBL, "marginBottom": "0.3rem"}),
                            dcc.Input(
                                id="corr-tickers",
                                type="text",
                                placeholder="e.g. PYPL, NKE, BA, BABA",
                                value="PYPL, NKE, BA, BABA",
                                style={"backgroundColor": C["bg"], "border": f"1px solid {C['border']}",
                                       "borderRadius": "8px", "color": C["text"],
                                       "padding": "0.5rem 0.9rem", "fontFamily": FONT,
                                       "fontSize": "0.82rem", "width": "100%", "outline": "none"},
                            ),
                        ], style={"flex": "1"}),

                        html.Div([
                            html.Div("Frequency", style={**LBL, "marginBottom": "0.3rem"}),
                            dcc.Dropdown(
                                id="corr-frequency",
                                options=[
                                    {"label": "Daily", "value": "daily"},
                                    {"label": "Weekly", "value": "weekly"},
                                    {"label": "Monthly", "value": "monthly"},
                                ],
                                value="weekly",
                                clearable=False,
                                style={"width": "170px", "fontSize": "0.82rem"},
                            ),
                        ]),

                        html.Button("Calculate", id="corr-run", n_clicks=0, style={
                            "backgroundColor": C["blue"], "color": "#000", "border": "none",
                            "borderRadius": "8px", "padding": "0.55rem 1.5rem",
                            "fontFamily": FONT, "fontWeight": "700", "fontSize": "0.85rem",
                            "cursor": "pointer", "alignSelf": "flex-end",
                        }),
                    ], style={"display": "flex", "gap": "0.75rem", "flexWrap": "wrap",
                              "alignItems": "flex-end", "marginBottom": "0.9rem"}),

                    html.Div(id="corr-status",
                             style={"color": C["muted"], "fontSize": "0.75rem",
                                    "fontFamily": FONT, "marginBottom": "0.65rem"}),
                    html.Div(id="corr-heatmap", style={"marginBottom": "0.9rem"}),
                    html.Div(id="corr-table"),
                ], style=PANEL),
            ], id="section-correlation", style={"display": "none"}),

            html.Div([
                html.Div([
                    html.Div("Portfolio Performance", style={**LBL, "color": C["accent"], "fontSize": "0.72rem"}),
                    html.Div("Track a weighted portfolio index over time.",
                             style={"color": C["muted"], "fontSize": "0.78rem", "marginBottom": "0.8rem",
                                    "fontFamily": FONT}),

                    html.Div([
                        html.Div([
                            html.Div("Tickers", style={**LBL, "marginBottom": "0.3rem"}),
                            dcc.Input(
                                id="perf-tickers",
                                type="text",
                                placeholder="e.g. PYPL, NKE, BA, BABA",
                                value="PYPL, NKE, BA, BABA",
                                style={"backgroundColor": C["bg"], "border": f"1px solid {C['border']}",
                                       "borderRadius": "8px", "color": C["text"],
                                       "padding": "0.5rem 0.9rem", "fontFamily": FONT,
                                       "fontSize": "0.82rem", "width": "100%", "outline": "none"},
                            ),
                        ], style={"flex": "1"}),

                        html.Div([
                            html.Div("Weights", style={**LBL, "marginBottom": "0.3rem"}),
                            dcc.Input(
                                id="perf-weights",
                                type="text",
                                placeholder="e.g. 25, 25, 25, 25",
                                value="25, 25, 25, 25",
                                style={"backgroundColor": C["bg"], "border": f"1px solid {C['border']}",
                                       "borderRadius": "8px", "color": C["text"],
                                       "padding": "0.5rem 0.9rem", "fontFamily": FONT,
                                       "fontSize": "0.82rem", "width": "230px", "outline": "none"},
                            ),
                        ]),

                        html.Div([
                            html.Div("Frequency", style={**LBL, "marginBottom": "0.3rem"}),
                            dcc.Dropdown(
                                id="perf-frequency",
                                options=[
                                    {"label": "Daily", "value": "daily"},
                                    {"label": "Weekly", "value": "weekly"},
                                    {"label": "Monthly", "value": "monthly"},
                                ],
                                value="weekly",
                                clearable=False,
                                style={"width": "170px", "fontSize": "0.82rem"},
                            ),
                        ]),

                        html.Button("Calculate", id="perf-run", n_clicks=0, style={
                            "backgroundColor": C["accent"], "color": "#000", "border": "none",
                            "borderRadius": "8px", "padding": "0.55rem 1.5rem",
                            "fontFamily": FONT, "fontWeight": "700", "fontSize": "0.85rem",
                            "cursor": "pointer", "alignSelf": "flex-end",
                        }),
                    ], style={"display": "flex", "gap": "0.75rem", "flexWrap": "wrap",
                              "alignItems": "flex-end", "marginBottom": "0.9rem"}),

                    html.Div(id="perf-status",
                             style={"color": C["muted"], "fontSize": "0.75rem",
                                    "fontFamily": FONT, "marginBottom": "0.65rem"}),
                    html.Div(id="perf-chart", style={"marginBottom": "0.9rem"}),
                    html.Div(id="perf-weights-table"),
                ], style=PANEL),
            ], id="section-performance", style={"display": "none"}),
        ], style={"flex": "1", "minWidth": "280px"}),
    ], style={"display": "flex", "gap": "1rem", "alignItems": "flex-start", "flexWrap": "wrap"}),

    dcc.Interval(id="auto-refresh", interval=5 * 60 * 1000, n_intervals=0),
])


@app.callback(
    Output("menu-dashboard", "style"),
    Output("menu-news", "style"),
    Output("menu-analyser", "style"),
    Output("menu-screener", "style"),
    Output("menu-correlation", "style"),
    Output("menu-performance", "style"),
    Output("section-dashboard", "style"),
    Output("section-news", "style"),
    Output("section-analyser", "style"),
    Output("section-screener", "style"),
    Output("section-correlation", "style"),
    Output("section-performance", "style"),
    Output("active-main-menu", "data"),
    Input("menu-dashboard", "n_clicks"),
    Input("menu-news", "n_clicks"),
    Input("menu-analyser", "n_clicks"),
    Input("menu-screener", "n_clicks"),
    Input("menu-correlation", "n_clicks"),
    Input("menu-performance", "n_clicks"),
    State("active-main-menu", "data"),
)
def set_main_menu(n_dashboard, n_news, n_analyser, n_screener, n_correlation, n_performance, current):
    ctx = dash.callback_context
    if not ctx.triggered:
        active = current or "dashboard"
    else:
        active = ctx.triggered[0]["prop_id"].split(".")[0].replace("menu-", "")

    buttons = [
        MAIN_MENU_BTN_ACTIVE if name == active else MAIN_MENU_BTN
        for name in ["dashboard", "news", "analyser", "screener", "correlation", "performance"]

    ]

    sections = [
        {"display": "block"} if name == active else {"display": "none"}
        for name in ["dashboard", "news", "analyser", "screener", "correlation", "performance"]
    ]

    return *buttons, *sections, active


# ─────────────────────────────────────────────────────────────────────────────
# Callbacks — main dashboard
# ─────────────────────────────────────────────────────────────────────────────
@app.callback(
    Output("index-cards",     "children"),
    Output("earnings-table",  "children"),
    Output("earnings-legend", "children"),
    Output("portfolio-table", "children"),
    Output("news-feed",       "children"),
    Output("last-updated",    "children"),
    Input("refresh-btn",   "n_clicks"),
    Input("auto-refresh",  "n_intervals"),
    State("ticker-input",  "value"),
)
def update_dashboard(n_clicks, n_intervals, raw):
    now     = datetime.datetime.now().strftime("%d %b %Y %H:%M")
    tickers = parse_tickers(raw)

    idx_cards = [index_card(d["name"], d["price"], d["chg"], d["pct"])
                 for d in fetch_index_data()]

    # Earnings
    if tickers:
        edf = fetch_earnings(tickers)
        if edf.empty:
            earn_content = html.Div("No upcoming earnings within 30 days.",
                                    style={"color": C["muted"], "fontSize": "0.82rem", "fontFamily": FONT})
            legend = html.Div()
        else:
            rows = []
            for _, row in edf.iterrows():
                days = row["Days Away"]
                urg  = C["red"] if days <= 7 else (C["accent"] if days <= 14 else C["green"])
                mine = row["Ticker"] in tickers
                rows.append(html.Tr([
                    html.Td([row["Ticker"],
                             html.Span(" ★", style={"color": C["accent"]}) if mine else None],
                            style={"color": C["accent"] if mine else C["text"],
                                   "fontWeight": "700" if mine else "500",
                                   "padding": "0.45rem 0.75rem",
                                   "borderBottom": f"1px solid {C['border']}",
                                   "fontFamily": FONT, "fontSize": "0.83rem"}),
                    html.Td(row["Earnings Date"],
                            style={"color": C["subtext"], "padding": "0.45rem 0.75rem",
                                   "borderBottom": f"1px solid {C['border']}",
                                   "fontSize": "0.8rem", "fontFamily": FONT}),
                    html.Td(f"{days}d",
                            style={"color": urg, "fontWeight": "700",
                                   "padding": "0.45rem 0.75rem",
                                   "borderBottom": f"1px solid {C['border']}",
                                   "textAlign": "right", "fontFamily": FONT, "fontSize": "0.8rem"}),
                ], style={"backgroundColor": "rgba(240,180,41,0.06)" if mine else "transparent"}))

            earn_content = html.Table([
                html.Thead(html.Tr([
                    html.Th(h, style={"color": C["muted"], "padding": "0.35rem 0.75rem",
                                       "fontSize": "0.62rem", "textTransform": "uppercase",
                                       "letterSpacing": "0.07em", "fontWeight": "700",
                                       "borderBottom": f"2px solid {C['border']}",
                                       "fontFamily": FONT,
                                       "textAlign": "right" if h == "Days" else "left"})
                    for h in ["Ticker", "Date", "Days"]
                ])),
                html.Tbody(rows),
            ], style={"width": "100%", "borderCollapse": "collapse"})

            legend = html.Div([
                html.Span("★ ", style={"color": C["accent"]}),
                html.Span("you own  ", style={"color": C["subtext"], "fontSize": "0.7rem", "fontFamily": FONT}),
                html.Span("■ ", style={"color": C["red"]}),
                html.Span("≤7d  ",    style={"color": C["subtext"], "fontSize": "0.7rem", "fontFamily": FONT}),
                html.Span("■ ", style={"color": C["accent"]}),
                html.Span("≤14d  ",   style={"color": C["subtext"], "fontSize": "0.7rem", "fontFamily": FONT}),
                html.Span("■ ", style={"color": C["green"]}),
                html.Span(">14d",     style={"color": C["subtext"], "fontSize": "0.7rem", "fontFamily": FONT}),
            ])
    else:
        earn_content = html.Div("Enter your tickers above and click Refresh.",
                                style={"color": C["muted"], "fontSize": "0.82rem", "fontFamily": FONT})
        legend = html.Div()

    # Portfolio
    if tickers:
        pdf = fetch_prices(tickers)
        port_rows = []
        for _, row in pdf.iterrows():
            col = C["green"] if row["_chg"] >= 0 else C["red"]
            port_rows.append(html.Tr([
                html.Td(row["Ticker"],
                        style={"color": C["accent"], "fontWeight": "700",
                               "padding": "0.45rem 0.75rem",
                               "borderBottom": f"1px solid {C['border']}",
                               "fontFamily": FONT, "fontSize": "0.83rem"}),
                html.Td(row["Price"],
                        style={"color": C["text"], "padding": "0.45rem 0.75rem",
                               "borderBottom": f"1px solid {C['border']}",
                               "textAlign": "right", "fontFamily": FONT, "fontSize": "0.83rem"}),
                html.Td(row["Change"],
                        style={"color": col, "padding": "0.45rem 0.75rem",
                               "borderBottom": f"1px solid {C['border']}",
                               "textAlign": "right", "fontFamily": FONT, "fontSize": "0.83rem"}),
                html.Td(row["Chg %"],
                        style={"color": col, "fontWeight": "700",
                               "padding": "0.45rem 0.75rem",
                               "borderBottom": f"1px solid {C['border']}",
                               "textAlign": "right", "fontFamily": FONT, "fontSize": "0.83rem"}),
                html.Td(row["Mkt Cap"],
                        style={"color": C["subtext"], "padding": "0.45rem 0.75rem",
                               "borderBottom": f"1px solid {C['border']}",
                               "textAlign": "right", "fontFamily": FONT, "fontSize": "0.78rem"}),
            ]))
        port_content = html.Table([
            html.Thead(html.Tr([
                html.Th(h, style={"color": C["muted"], "padding": "0.35rem 0.75rem",
                                   "fontSize": "0.62rem", "textTransform": "uppercase",
                                   "letterSpacing": "0.07em", "fontWeight": "700",
                                   "borderBottom": f"2px solid {C['border']}",
                                   "fontFamily": FONT,
                                   "textAlign": "right" if i > 0 else "left"})
                for i, h in enumerate(["Ticker", "Price", "Change", "Chg %", "Mkt Cap"])
            ])),
            html.Tbody(port_rows),
        ], style={"width": "100%", "borderCollapse": "collapse"})
    else:
        port_content = html.Div("No tickers entered yet.",
                                style={"color": C["muted"], "fontSize": "0.82rem", "fontFamily": FONT})

    # News
    if tickers:
        arts = fetch_news(tickers)
        if arts:
            news_content = html.Div([
                html.A([
                    html.Span(f"[{a['ticker']}] ",
                              style={"color": C["accent"], "fontWeight": "700",
                                     "fontSize": "0.72rem", "fontFamily": FONT}),
                    html.Span(a["title"],
                              style={"color": C["text"], "fontSize": "0.82rem", "fontFamily": FONT}),
                    html.Span(f"  {a['published'][:16]}",
                              style={"color": C["muted"], "fontSize": "0.68rem",
                                     "marginLeft": "0.5rem", "fontFamily": FONT}),
                ], href=a["link"], target="_blank",
                   style={"display": "block", "padding": "0.55rem 0",
                          "borderBottom": f"1px solid {C['border']}",
                          "textDecoration": "none", "lineHeight": "1.5"})
                for a in arts
            ])
        else:
            news_content = html.Div("No news found.",
                                    style={"color": C["muted"], "fontSize": "0.82rem", "fontFamily": FONT})
    else:
        news_content = html.Div("Enter tickers above to load news.",
                                style={"color": C["muted"], "fontSize": "0.82rem", "fontFamily": FONT})

    return idx_cards, earn_content, legend, port_content, news_content, f"Updated {now}"


# ─────────────────────────────────────────────────────────────────────────────
# Callbacks — Stock Analyser: load stock
# ─────────────────────────────────────────────────────────────────────────────
@app.callback(
    Output("active-ticker", "data"),
    Output("stock-header",  "children"),
    Output("tab-nav",       "style"),
    Input("lookup-btn",   "n_clicks"),
    State("lookup-input", "value"),
    prevent_initial_call=True,
)
def load_stock(n, raw):
    if not raw:
        return "", html.Div(), {"display": "none"}
    ticker = raw.strip().upper()
    try:
        info     = yf.Ticker(ticker).info
        name     = info.get("longName") or info.get("shortName") or ticker
        price    = info.get("currentPrice") or info.get("regularMarketPrice")
        prev     = info.get("previousClose")
        chg      = round(price - prev, 2) if price and prev else 0
        pct      = round((chg / prev) * 100, 2) if prev else 0
        col      = C["green"] if chg >= 0 else C["red"]
        sign     = "▲" if chg >= 0 else "▼"
        sector   = info.get("sector", "")
        industry = info.get("industry", "")

        header = html.Div([
            html.Div([
                html.Span(name,
                          style={"fontFamily": FONT, "fontWeight": "800",
                                 "fontSize": "1.3rem", "color": C["text"]}),
                html.Span(f"  {ticker}",
                          style={"color": C["subtext"], "fontSize": "0.85rem",
                                 "fontFamily": FONT, "marginLeft": "0.4rem"}),
            ]),
            html.Div([
                html.Span(f"${price:,.2f}" if price else "—",
                          style={"fontSize": "1.55rem", "fontWeight": "700",
                                 "color": C["text"], "fontFamily": FONT}),
                html.Span(f"  {sign} {abs(chg):.2f} ({abs(pct):.2f}%)",
                          style={"color": col, "fontSize": "0.88rem",
                                 "fontFamily": FONT, "marginLeft": "0.5rem",
                                 "fontWeight": "600"}),
            ], style={"marginTop": "0.2rem"}),
            html.Div(f"{sector}  ·  {industry}",
                     style={"color": C["muted"], "fontSize": "0.72rem",
                            "fontFamily": FONT, "marginTop": "0.2rem"}),
        ], style={"marginBottom": "1rem", "paddingBottom": "0.75rem",
                  "borderBottom": f"1px solid {C['border']}"})

    except Exception:
        header = html.Div(f"Could not find ticker: {ticker}",
                          style={"color": C["red"], "fontFamily": FONT, "fontSize": "0.85rem"})

    nav_style = {"display": "flex", "gap": "0.5rem", "flexWrap": "wrap", "marginBottom": "1rem"}
    return ticker, header, nav_style


# ─────────────────────────────────────────────────────────────────────────────
# Callbacks — tab switching
# ─────────────────────────────────────────────────────────────────────────────
@app.callback(
    Output("tab-chart",     "style"),
    Output("tab-valuation", "style"),
    Output("tab-income",    "style"),
    Output("tab-balance",   "style"),
    Output("tab-cashflow",  "style"),
    Output("active-tab",    "data"),
    Output("period-nav",    "style"),
    Input("tab-chart",     "n_clicks"),
    Input("tab-valuation", "n_clicks"),
    Input("tab-income",    "n_clicks"),
    Input("tab-balance",   "n_clicks"),
    Input("tab-cashflow",  "n_clicks"),
    State("active-tab",    "data"),
)
def switch_tab(c1, c2, c3, c4, c5, current):
    ctx = dash.callback_context
    if not ctx.triggered or not any([c1, c2, c3, c4, c5]):
        active = current or "chart"
    else:
        active = ctx.triggered[0]["prop_id"].split(".")[0].replace("tab-", "")

    tabs   = ["chart", "valuation", "income", "balance", "cashflow"]
    styles = [NAV_BTN_ACTIVE if t == active else NAV_BTN for t in tabs]
    period_vis = ({"display": "flex", "gap": "0.4rem", "alignItems": "center",
                   "marginBottom": "0.75rem", "flexWrap": "wrap"}
                  if active == "chart" else {"display": "none"})
    return *styles, active, period_vis


# ─────────────────────────────────────────────────────────────────────────────
# Callbacks — period switching
# ─────────────────────────────────────────────────────────────────────────────
@app.callback(
    *[Output(f"period-{p}", "style") for p in PERIODS],
    Output("active-period", "data"),
    *[Input(f"period-{p}",  "n_clicks") for p in PERIODS],
    State("active-period",  "data"),
)
def switch_period(*args):
    clicks  = args[:len(PERIODS)]
    current = args[len(PERIODS)]
    ctx = dash.callback_context
    if not ctx.triggered or not any(clicks):
        active = current or "6mo"
    else:
        active = ctx.triggered[0]["prop_id"].split(".")[0].replace("period-", "")

    styles = [{**NAV_BTN, "padding": "0.3rem 0.7rem", "fontSize": "0.75rem",
               **({"backgroundColor": C["accent"], "color": "#000",
                   "border": f"1px solid {C['accent']}"} if p == active else {})}
              for p in PERIODS]
    return *styles, active


# ─────────────────────────────────────────────────────────────────────────────
# Callbacks — render stock content
# ─────────────────────────────────────────────────────────────────────────────
@app.callback(
    Output("stock-content", "children"),
    Input("active-tab",    "data"),
    Input("active-period", "data"),
    Input("active-ticker", "data"),
)
def render_content(tab, period, ticker):
    if not ticker:
        return html.Div("Search for a stock above to get started.",
                        style={"color": C["muted"], "fontSize": "0.82rem", "fontFamily": FONT})

    if tab == "chart":
        fig = build_price_chart(ticker, period)
        return dcc.Graph(figure=fig, config={"displayModeBar": False},
                         style={"height": "380px"})
    elif tab == "valuation":
        return html.Div([html.Div("Valuation & Key Metrics", style=LBL),
                         build_valuation_table(ticker)])
    elif tab == "income":
        return build_financials(ticker, "income")
    elif tab == "balance":
        return build_financials(ticker, "balance")
    elif tab == "cashflow":
        return build_financials(ticker, "cashflow")
    return html.Div()



# ─────────────────────────────────────────────────────────────────────────────
# Callbacks — Screener
# ─────────────────────────────────────────────────────────────────────────────

@app.callback(
    Output("screener-results",    "children"),
    Output("screener-status",     "children"),
    Output("screener-data-store", "data"),
    Input("screener-run",  "n_clicks"),
    State("screener-extra",    "value"),
    State("f-pe-max",          "value"),
    State("f-ev-max",          "value"),
    State("f-margin-min",      "value"),
    State("f-revgrowth-min",   "value"),
    State("f-div-min",         "value"),
    State("f-de-max",          "value"),
    State("f-sector",          "value"),
    prevent_initial_call=True,
)
def run_screen(n, extra_raw, pe_max, ev_max, margin_min, revgrowth_min, div_min, de_max, sector):
    if not n:
        return html.Div(), "", None
    extra = parse_tickers(extra_raw) if extra_raw else []
    df    = run_screener(extra)
    if df.empty:
        return html.Div("No data returned.", style={"color": C["muted"], "fontFamily": FONT}), "", None

    if sector and sector != "All":
        df = df[df["Sector"] == sector]
    if pe_max is not None:
        df = df[df["P/E"].isna() | (df["P/E"] <= float(pe_max))]
    if ev_max is not None:
        df = df[df["EV/EBITDA"].isna() | (df["EV/EBITDA"] <= float(ev_max))]
    if margin_min is not None:
        df = df[df["Profit Margin Raw"].isna() | (df["Profit Margin Raw"] >= float(margin_min)/100)]
    if revgrowth_min is not None:
        df = df[df["Rev Growth Raw"].isna() | (df["Rev Growth Raw"] >= float(revgrowth_min)/100)]
    if div_min is not None:
        df = df[df["Div Yield Raw"].isna() | (df["Div Yield Raw"] >= float(div_min)/100)]
    if de_max is not None:
        df = df[df["Debt/Equity"].isna() | (df["Debt/Equity"] <= float(de_max))]

    if df.empty:
        return html.Div("No stocks matched your filters.", style={"color": C["muted"], "fontFamily": FONT}), "0 results", None

    df = df.sort_values("Mkt Cap Raw", ascending=False).reset_index(drop=True)
    status = f"{len(df)} stock{'s' if len(df)!=1 else ''} matched · sorted by Market Cap"
    display_cols = ["Ticker","Name","Sector","Price","Mkt Cap","P/E","EV/EBITDA",
                    "Rev Growth","Profit Margin","Div Yield","52w Chg %","Debt/Equity","Day Chg %"]

    th_s = {
        "padding": "0.38rem 0.6rem", "fontSize": "0.62rem", "textTransform": "uppercase",
        "letterSpacing": "0.06em", "fontWeight": "700", "whiteSpace": "nowrap",
        "borderBottom": "2px solid " + C["border"], "fontFamily": FONT, "color": C["muted"],
    }
    header = html.Thead(html.Tr(
        [html.Th(c, style={**th_s, "textAlign": "right" if i > 2 else "left"})
         for i, c in enumerate(display_cols)]
    ))

    def cell_color(col, val):
        if col in ("Day Chg %", "52w Chg %", "Rev Growth"):
            try:
                nv = float(str(val).replace("%","").replace("+",""))
                return C["green"] if nv > 0 else (C["red"] if nv < 0 else C["subtext"])
            except Exception:
                return C["subtext"]
        if col == "Profit Margin":
            try:
                nv = float(str(val).replace("%",""))
                return C["green"] if nv >= 15 else (C["accent"] if nv >= 5 else C["red"])
            except Exception:
                return C["subtext"]
        return C["text"]

    body_rows = []
    for _, row in df.iterrows():
        cells = []
        for i, col in enumerate(display_cols):
            val = row.get(col, "—")
            val = "—" if (val is None or (isinstance(val, float) and pd.isna(val))) else val
            is_right = i > 2
            color = cell_color(col, val) if i > 2 else (C["accent"] if col == "Ticker" else C["text"])
            fw = "700" if col == "Ticker" else ("600" if i > 2 else "400")
            cells.append(html.Td(str(val), style={
                "color": color, "fontWeight": fw,
                "padding": "0.4rem 0.6rem",
                "borderBottom": "1px solid " + C["border"],
                "fontSize": "0.78rem", "fontFamily": FONT,
                "textAlign": "right" if is_right else "left",
                "whiteSpace": "nowrap",
            }))
        body_rows.append(html.Tr(cells))

    table = html.Div(
        html.Table([header, html.Tbody(body_rows)],
                   style={"width": "100%", "borderCollapse": "collapse"}),
        style={"overflowX": "auto", "maxHeight": "520px", "overflowY": "auto"},
    )
    csv_df = df[display_cols].copy()
    store_data = csv_df.to_json(date_format="iso", orient="split")
    return table, status, store_data


@app.callback(
    Output("screener-download", "data"),
    Input("screener-download-btn", "n_clicks"),
    State("screener-data-store",   "data"),
    prevent_initial_call=True,
)
def download_csv(n, store_data):
    if not store_data:
        return None
    df  = pd.read_json(store_data, orient="split")
    now = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    return dcc.send_data_frame(df.to_csv, f"screener_{now}.csv", index=False)


@app.callback(
    Output("corr-heatmap", "children"),
    Output("corr-table", "children"),
    Output("corr-status", "children"),
    Input("corr-run", "n_clicks"),
    State("corr-tickers", "value"),
    State("corr-frequency", "value"),
    prevent_initial_call=True,
)
def calculate_correlation(n, raw_tickers, frequency):
    tickers = parse_tickers(raw_tickers)
    # Correlation is only meaningful with at least 2 assets.
    if len(tickers) < 2:
        msg = "Enter at least 2 tickers to calculate correlations."
        return html.Div(), html.Div(), msg

    corr, available = build_correlation_data(tickers, frequency or "daily")
    if corr is None or corr.empty:
        msg = "No usable return series found for the selected inputs."
        return html.Div(), html.Div(), msg

    fig = go.Figure(data=go.Heatmap(
        z=corr.values,
        x=list(corr.columns),
        y=list(corr.index),
        zmin=-1,
        zmax=1,
        colorscale=[
            [0.0, "#f85149"],
            [0.5, "#21262d"],
            [1.0, "#3fb950"],
        ],
        text=corr.values,
        texttemplate="%{text:.2f}",
        hovertemplate="%{y} vs %{x}: %{z:.3f}<extra></extra>",
        colorbar={"title": "Corr"},
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": FONT, "color": C["text"], "size": 11},
        margin={"l": 0, "r": 0, "t": 10, "b": 0},
        xaxis={"side": "top", "tickangle": 0},
        yaxis={"autorange": "reversed"},
        height=max(260, 50 * len(corr.index) + 90),
    )

    header_cells = [
        html.Th("Ticker", style={
            "padding": "0.38rem 0.6rem", "fontSize": "0.62rem", "textTransform": "uppercase",
            "letterSpacing": "0.06em", "fontWeight": "700", "borderBottom": "2px solid " + C["border"],
            "fontFamily": FONT, "color": C["muted"], "textAlign": "left",
        })
    ] + [
        html.Th(col, style={
            "padding": "0.38rem 0.6rem", "fontSize": "0.62rem", "textTransform": "uppercase",
            "letterSpacing": "0.06em", "fontWeight": "700", "borderBottom": "2px solid " + C["border"],
            "fontFamily": FONT, "color": C["muted"], "textAlign": "right",
        })
        for col in corr.columns
    ]

    rows = []
    for row_label in corr.index:
        cells = [html.Td(row_label, style={
            "padding": "0.4rem 0.6rem", "borderBottom": "1px solid " + C["border"],
            "fontSize": "0.78rem", "fontFamily": FONT, "color": C["accent"], "fontWeight": "700",
            "textAlign": "left", "whiteSpace": "nowrap",
        })]

        for col_label in corr.columns:
            val = float(corr.loc[row_label, col_label])
            color = C["green"] if val > 0.4 else (C["red"] if val < -0.4 else C["subtext"])
            cells.append(html.Td(f"{val:.3f}", style={
                "padding": "0.4rem 0.6rem", "borderBottom": "1px solid " + C["border"],
                "fontSize": "0.78rem", "fontFamily": FONT, "color": color,
                "textAlign": "right", "whiteSpace": "nowrap",
            }))
        rows.append(html.Tr(cells))

    table = html.Div(
        html.Table([html.Thead(html.Tr(header_cells)), html.Tbody(rows)],
                   style={"width": "100%", "borderCollapse": "collapse"}),
        style={"overflowX": "auto"},
    )

    used = ", ".join(available)
    freq_label = (frequency or "daily").capitalize()
    status = f"Computed {freq_label} return correlations for {len(available)} ticker(s): {used}"

    return dcc.Graph(figure=fig, config={"displayModeBar": False}), table, status


@app.callback(
    Output("perf-chart", "children"),
    Output("perf-weights-table", "children"),
    Output("perf-status", "children"),
    Input("perf-run", "n_clicks"),
    State("perf-tickers", "value"),
    State("perf-weights", "value"),
    State("perf-frequency", "value"),
    prevent_initial_call=True,
)
def calculate_portfolio_performance(n, raw_tickers, raw_weights, frequency):
    import re

    tickers = parse_tickers(raw_tickers)
    if len(tickers) < 1:
        return html.Div(), html.Div(), "Enter at least one ticker."

    weight_tokens = [w for w in re.split(r"[\s,;]+", (raw_weights or "").strip()) if w]
    if len(weight_tokens) != len(tickers):
        msg = "Provide exactly one weight per ticker (same order)."
        return html.Div(), html.Div(), msg

    weights = []
    for token in weight_tokens:
        try:
            weights.append(float(token.replace("%", "")))
        except Exception:
            msg = "Weights must be numeric (e.g. 25, 25, 25, 25)."
            return html.Div(), html.Div(), msg

    # Accept either percentages (25, 25, 50) or decimals (0.25, 0.25, 0.5).
    if any(w > 1 for w in weights):
        weights = [w / 100 for w in weights]

    if sum(weights) <= 0:
        return html.Div(), html.Div(), "Total weight must be greater than zero."

    port_index, component_index, used_weights = build_portfolio_performance_data(
        tickers, weights, frequency or "weekly"
    )
    if port_index is None or component_index is None or used_weights is None:
        return html.Div(), html.Div(), "No usable price history found for these inputs."

    fig = go.Figure()
    for ticker in component_index.columns:
        fig.add_trace(go.Scatter(
            x=component_index.index,
            y=component_index[ticker],
            mode="lines",
            line={"width": 1.2, "color": C["muted"]},
            opacity=0.5,
            name=ticker,
            hovertemplate=f"{ticker}: %{{y:.2f}}<extra></extra>",
        ))

    fig.add_trace(go.Scatter(
        x=port_index.index,
        y=port_index,
        mode="lines",
        line={"width": 3, "color": C["accent"]},
        name="Portfolio",
        hovertemplate="Portfolio: %{y:.2f}<extra></extra>",
    ))

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": FONT, "color": C["text"], "size": 11},
        margin={"l": 0, "r": 0, "t": 10, "b": 0},
        xaxis={"showgrid": False, "color": C["muted"], "linecolor": C["border"]},
        yaxis={"showgrid": True, "gridcolor": C["border"], "color": C["subtext"]},
        legend={"orientation": "h", "y": 1.02, "x": 0},
        hovermode="x unified",
        height=390,
    )

    rows = []
    for ticker, weight in used_weights.items():
        rows.append(html.Tr([
            html.Td(ticker, style={
                "padding": "0.4rem 0.7rem", "borderBottom": "1px solid " + C["border"],
                "fontSize": "0.8rem", "fontFamily": FONT, "color": C["accent"], "fontWeight": "700",
            }),
            html.Td(f"{weight * 100:.2f}%", style={
                "padding": "0.4rem 0.7rem", "borderBottom": "1px solid " + C["border"],
                "fontSize": "0.8rem", "fontFamily": FONT, "color": C["text"], "textAlign": "right",
            }),
        ]))

    weights_table = html.Div(
        html.Table([
            html.Thead(html.Tr([
                html.Th("Ticker", style={
                    "padding": "0.35rem 0.7rem", "fontSize": "0.62rem", "textTransform": "uppercase",
                    "letterSpacing": "0.06em", "fontWeight": "700", "borderBottom": "2px solid " + C["border"],
                    "fontFamily": FONT, "color": C["muted"], "textAlign": "left",
                }),
                html.Th("Weight", style={
                    "padding": "0.35rem 0.7rem", "fontSize": "0.62rem", "textTransform": "uppercase",
                    "letterSpacing": "0.06em", "fontWeight": "700", "borderBottom": "2px solid " + C["border"],
                    "fontFamily": FONT, "color": C["muted"], "textAlign": "right",
                }),
            ])),
            html.Tbody(rows),
        ], style={"width": "100%", "borderCollapse": "collapse", "maxWidth": "420px"}),
        style={"overflowX": "auto"},
    )

    total_return = ((float(port_index.iloc[-1]) / float(port_index.iloc[0])) - 1) * 100
    freq_label = (frequency or "weekly").capitalize()
    status = (
        f"{freq_label} portfolio performance across {len(used_weights)} ticker(s). "
        f"Total return over shown period: {total_return:+.2f}%"
    )

    return dcc.Graph(figure=fig, config={"displayModeBar": False}), weights_table, status

# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.getenv("DASH_PORT", "8051"))
    print("\n  Stock Dashboard")
    print("  ─────────────────────────────────────")
    print(f"  Open your browser at → http://127.0.0.1:{port}\n")
    # Default to a single-process server to avoid stale duplicate app instances.
    debug_mode = os.getenv("DASH_DEBUG", "0") == "1"
    app.run(debug=debug_mode, port=port, use_reloader=False)
    

