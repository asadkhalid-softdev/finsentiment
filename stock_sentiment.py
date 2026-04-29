import os
import pandas as pd
import yfinance as yf
import numpy as np
from datetime import datetime, timedelta
import time
from tqdm import tqdm

total_investment = 2000
n_stocks = 20
METRICS_FILE = "stocks_metrics.xlsx"
METRICS_SHEET = "Metrics"
CACHE_MINUTES = 30

METRICS_COLUMNS = [
    'Ticker', 'Company Name', 'Region',
    'Sentiment_Score', 'Current_Price',
    '1Y_Momentum', '3Y_Momentum', 'Volume_Trend',
    'Market_Cap', 'PE_Ratio', 'Profit_Margin',
    'Revenue_Growth', 'Debt_To_Equity', 'Dividend_Yield', 'Analyst_Rating',
    'Fetched_At',
]


# ---------------------------------------------------------------------------
# Technical + scoring helpers
# ---------------------------------------------------------------------------

def calculate_technical_indicators(hist_data):
    if hist_data.empty:
        return {}

    n = len(hist_data)
    current_price = hist_data['Close'].iloc[-1]

    hist_data['MA200'] = hist_data['Close'].rolling(window=200).mean()
    ma200 = hist_data['MA200'].iloc[-1]

    if n >= 252:
        momentum_1y = (current_price - hist_data['Close'].iloc[-252]) / hist_data['Close'].iloc[-252] * 100
    else:
        momentum_1y = (current_price - hist_data['Close'].iloc[0]) / hist_data['Close'].iloc[0] * 100

    if n >= 756:
        momentum_3y = (current_price - hist_data['Close'].iloc[-756]) / hist_data['Close'].iloc[-756] * 100
    else:
        momentum_3y = momentum_1y

    avg_volume_1y = hist_data['Volume'].iloc[-min(252, n):].mean()
    avg_volume_3y = hist_data['Volume'].mean()
    volume_trend = avg_volume_1y / avg_volume_3y if avg_volume_3y > 0 else 1.0

    return {
        'price_above_ma200': current_price > ma200 if not pd.isna(ma200) else False,
        '1y_momentum': momentum_1y,
        '3y_momentum': momentum_3y,
        'volume_trend': volume_trend,
        'current_price': current_price,
    }


def calculate_sentiment_score(technical_data, stock_info):
    score = 50

    if technical_data:
        if technical_data['price_above_ma200']:
            score += 10
        else:
            score += 5

        m1 = technical_data['1y_momentum']
        m3 = technical_data['3y_momentum']
        if m1 > 10 and m3 > 30:
            score += 10
        elif m1 > 5 and m3 > 15:
            score += 7
        elif m1 > 0 and m3 > 0:
            score += 5

        vt = technical_data['volume_trend']
        if vt > 1.5:
            score += 10
        elif vt > 1.2:
            score += 7
        elif vt > 1.0:
            score += 5

    if stock_info:
        def _num(key):
            try:
                v = stock_info.get(key)
                return float(v) if v is not None else None
            except (TypeError, ValueError):
                return None

        pe = _num('trailingPE')
        if pe is not None:
            if 10 <= pe <= 25:
                score += 10
            elif 5 <= pe <= 30:
                score += 7
            else:
                score += 3

        pm = _num('profitMargins')
        if pm is not None:
            if pm > 0.2:
                score += 10
            elif pm > 0.1:
                score += 7
            elif pm > 0:
                score += 5

        rg = _num('revenueGrowth')
        if rg is not None:
            if rg > 0.2:
                score += 10
            elif rg > 0.1:
                score += 7
            elif rg > 0:
                score += 5

        de = _num('debtToEquity')
        if de is not None:
            if de < 0.5:
                score += 10
            elif de < 1.0:
                score += 7
            elif de < 2.0:
                score += 5

    return min(100, max(0, score))


def calculate_investment_allocation(df, total_investment=2000, n_stocks=20):
    key_columns = [
        'Sentiment_Score', 'Profit_Margin', 'Current_Price',
        '1Y_Momentum', '3Y_Momentum', 'Volume_Trend',
        'PE_Ratio', 'Revenue_Growth', 'Debt_To_Equity',
    ]
    df = df.dropna(subset=key_columns)
    df = df.sort_values(
        ['Sentiment_Score', 'Profit_Margin'],
        ascending=[False, False],
        na_position='last',
        kind='stable',
    )
    df['Profit_Margin'] = pd.to_numeric(df['Profit_Margin'], errors='coerce') * 100

    top_df = df.head(n_stocks).copy()

    print("\nSelected stocks before allocation:")
    print(top_df[['Company Name', 'Ticker', 'Region', 'Sentiment_Score', 'Profit_Margin']].to_string())

    top_df['Weight'] = top_df['Sentiment_Score'] / top_df['Sentiment_Score'].sum()
    top_df['Investment_Amount'] = (top_df['Weight'] * total_investment).round(2)
    top_df['Shares'] = (top_df['Investment_Amount'] / top_df['Current_Price']).round(4)
    top_df['Actual_Investment'] = (top_df['Shares'] * top_df['Current_Price']).round(2)
    top_df['Portfolio_Percentage'] = (
        top_df['Actual_Investment'] / top_df['Actual_Investment'].sum() * 100
    ).round(2)

    df['Actual_Investment'] = 0.0
    df['Portfolio_Percentage'] = 0.0
    df['Shares'] = 0.0
    for idx in top_df.index:
        df.loc[idx, 'Actual_Investment'] = top_df.loc[idx, 'Actual_Investment']
        df.loc[idx, 'Portfolio_Percentage'] = top_df.loc[idx, 'Portfolio_Percentage']
        df.loc[idx, 'Shares'] = top_df.loc[idx, 'Shares']

    df['Profit_Margin'] = df['Profit_Margin'] / 100
    return df


# ---------------------------------------------------------------------------
# Metrics cache helpers
# ---------------------------------------------------------------------------

def load_metrics_cache() -> pd.DataFrame:
    """Load stocks_metrics.xlsx; return empty DataFrame if not found."""
    if not os.path.exists(METRICS_FILE):
        return pd.DataFrame(columns=METRICS_COLUMNS)
    try:
        df = pd.read_excel(METRICS_FILE, sheet_name=METRICS_SHEET)
        if 'Domain/Topic' in df.columns:
            df = df.drop(columns=['Domain/Topic'])
        if df.empty:
            return pd.DataFrame(columns=METRICS_COLUMNS)
        for col in METRICS_COLUMNS:
            if col not in df.columns:
                df[col] = np.nan
        df = df[METRICS_COLUMNS]
        df['Fetched_At'] = pd.to_datetime(df['Fetched_At'])
        print(f"Loaded {len(df)} cached rows from {METRICS_FILE}")
        return df
    except Exception as e:
        print(f"Could not load metrics cache: {e}")
        return pd.DataFrame(columns=METRICS_COLUMNS)


def is_fresh(cache_df: pd.DataFrame, ticker: str) -> bool:
    """Return True if ticker has a cache entry younger than CACHE_MINUTES."""
    if cache_df.empty:
        return False
    rows = cache_df[cache_df['Ticker'] == ticker]
    if rows.empty:
        return False
    latest = rows['Fetched_At'].max()
    return (datetime.now() - latest) < timedelta(minutes=CACHE_MINUTES)


def upsert_and_save(cache_df: pd.DataFrame, new_row: dict) -> pd.DataFrame:
    """Replace any existing row for the ticker, append the new one, persist to disk."""
    ticker = new_row['Ticker']
    cache_df = cache_df[cache_df['Ticker'] != ticker].copy()
    cache_df = pd.concat([cache_df, pd.DataFrame([new_row])], ignore_index=True)

    # Ensure column order
    for col in METRICS_COLUMNS:
        if col not in cache_df.columns:
            cache_df[col] = np.nan
    cache_df = cache_df[METRICS_COLUMNS]

    with pd.ExcelWriter(METRICS_FILE, engine='openpyxl', mode='w') as writer:
        cache_df.to_excel(writer, sheet_name=METRICS_SHEET, index=False)

    return cache_df


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def _ensure_stocks_file() -> bool:
    if not os.path.exists('stocks.xlsx'):
        empty = pd.DataFrame(columns=[
            'Ticker', 'Company Name', 'ISIN', 'Region',
            'Boycott', 'Reason', 'Ignore',
        ])
        with pd.ExcelWriter('stocks.xlsx', engine='openpyxl') as writer:
            empty.to_excel(writer, sheet_name='Stocks', index=False)
        print("stocks.xlsx not found — created empty file. Run update_stocks.py first to populate it.")
        return False
    return True


def update_stock_analysis():
    try:
        if not _ensure_stocks_file():
            return

        df = pd.read_excel('stocks.xlsx', sheet_name='Stocks')
        if 'Domain/Topic' in df.columns:
            df = df.drop(columns=['Domain/Topic'])
        df = df[(df['Boycott'] != 'Yes') & (df['Ignore'] != 'Yes')]
        print(f"Loaded {len(df)} stocks from stocks.xlsx")

        cache_df = load_metrics_cache()

        fresh_count = sum(is_fresh(cache_df, t) for t in df['Ticker'])
        print(f"Cache hits (≤{CACHE_MINUTES} min old): {fresh_count} / {len(df)}")

        results = []
        pbar = tqdm(df.iterrows(), total=len(df), desc="Processing stocks", ncols=100)

        try:
            for _, row in pbar:
                name = str(row['Company Name'])
                symbol = str(row['Ticker'])
                pbar.set_description(f"Processing {name[:35]}..." if len(name) > 35 else f"Processing {name}...")

                # --- Serve from cache if fresh ---
                if is_fresh(cache_df, symbol):
                    cached = cache_df[cache_df['Ticker'] == symbol].iloc[-1].to_dict()
                    results.append(cached)
                    continue

                # --- Fetch from yfinance ---
                try:
                    ticker = yf.Ticker(symbol)
                    hist_data = ticker.history(period='5y')
                    if hist_data.empty:
                        print(f"\nNo historical data for {name} ({symbol})")
                        continue

                    stock_info = ticker.info
                    technical_data = calculate_technical_indicators(hist_data)
                    sentiment_score = calculate_sentiment_score(technical_data, stock_info)

                    def _f(key):
                        try:
                            v = stock_info.get(key)
                            return float(v) if v is not None else None
                        except (TypeError, ValueError):
                            return None

                    new_row = {
                        'Ticker': symbol,
                        # Prefer Yahoo name — corrects bad Company Name from stocks.xlsx (e.g. after old strip bug)
                        'Company Name': (stock_info.get('longName') or stock_info.get('shortName') or name).strip(),
                        'Region': row.get('Region', ''),
                        'Sentiment_Score': sentiment_score,
                        'Current_Price': technical_data['current_price'],
                        '1Y_Momentum': technical_data['1y_momentum'],
                        '3Y_Momentum': technical_data['3y_momentum'],
                        'Volume_Trend': technical_data['volume_trend'],
                        'Market_Cap': _f('marketCap'),
                        'PE_Ratio': _f('trailingPE'),
                        'Profit_Margin': _f('profitMargins'),
                        'Revenue_Growth': _f('revenueGrowth'),
                        'Debt_To_Equity': _f('debtToEquity'),
                        'Dividend_Yield': _f('dividendYield'),
                        'Analyst_Rating': _f('recommendationMean'),
                        'Fetched_At': datetime.now(),
                    }

                    cache_df = upsert_and_save(cache_df, new_row)
                    results.append(new_row)
                    time.sleep(0.5)

                except Exception as e:
                    print(f"\nError updating {name} ({symbol}): {e}")
                    continue

        except KeyboardInterrupt:
            pbar.close()
            print(f"\nInterrupted — {len(results)} stocks processed so far. Cache saved.")
            if not results:
                return

        else:
            pbar.close()

        if not results:
            print("No results to process.")
            return

        print("\nCalculating investment allocations...")
        results_df = pd.DataFrame(results)
        results_df = calculate_investment_allocation(
            results_df, total_investment=total_investment, n_stocks=n_stocks
        )
        results_df = results_df.sort_values('Sentiment_Score', ascending=False)


        pd.set_option('display.float_format', lambda x: '%.2f' % x)
        display_cols = [
            'Company Name', 'Ticker', 'Region', 'Sentiment_Score',
            'Profit_Margin', 'Revenue_Growth', 'Debt_To_Equity',
            'Current_Price', 'Actual_Investment', 'Shares', 'Portfolio_Percentage',
        ]
        print("\nTop 5 stocks:")
        print(results_df[display_cols].head().to_string())

        total_invested = results_df['Actual_Investment'].sum()
        print(f"\nTotal Investment: ${total_invested:.2f}")
        print(f"Remaining Cash:   ${total_investment - total_invested:.2f}")

        print(f"\nPortfolio Allocation Summary (Top {n_stocks}):")
        alloc_summary = results_df[results_df['Shares'] > 0][display_cols]
        print(alloc_summary.to_string())

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error updating analysis: {e}")


if __name__ == "__main__":
    print("Starting stock analysis update...")
    update_stock_analysis()
