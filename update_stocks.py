import pandas as pd
from yahoo_fin import stock_info as si
from requests_html import HTMLSession

file_path = "stocks.xlsx"

# Load existing data
try:
    existing_df = pd.read_excel(file_path, sheet_name="Stocks")
except Exception as e:
    print(f"Couldn't read {file_path}: {e}")
    existing_df = pd.DataFrame(columns=[
        'Ticker', 'Company Name', 'ISIN', 'Domain/Topic',
        'inGermany', 'Boycott', 'Reason', 'Ignore'
    ])

# Fetch trending tickers
try:
    most_active_df = si.get_day_most_active()
    trending_tickers = most_active_df['Symbol'].tolist()
except Exception as e:
    print(f"Error fetching trending stocks: {e}")
    trending_tickers = []

# Prepare new entries
new_entries = []
for ticker in trending_tickers[:10]:  # Limit to top 10
    try:
        info = si.get_quote_table(ticker, dict_result=True)
        new_entries.append({
            'Ticker': ticker,
            'Company Name': info.get('Quote Source Name', ''),
            'ISIN': '',
            'Domain/Topic': 'Trending',
            'inGermany': '',
            'Boycott': '',
            'Reason': '',
            'Ignore': ''
        })
    except Exception as e:
        print(f"Failed to fetch info for {ticker}: {e}")

if new_entries:
    df_new = pd.DataFrame(new_entries)

    # Filter out duplicates based on Ticker
    if not existing_df.empty:
        df_final = df_new[~df_new['Ticker'].isin(existing_df['Ticker'])]
    else:
        df_final = df_new

    # Append new rows and save
    df_updated = pd.concat([existing_df, df_final], ignore_index=True)

    with pd.ExcelWriter(file_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
        df_updated.to_excel(writer, sheet_name="Stocks", index=False)

    print(f"✅ Added {len(df_final)} new trending stocks.")
else:
    print("No new entries found or fetched.")
