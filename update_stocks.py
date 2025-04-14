import pandas as pd
from yahoo_fin import stock_info as si

# Load existing data
file_path = "stocks.xlsx"
existing_df = pd.read_excel(file_path, sheet_name="Stocks")

# Fetch trending tickers (most active today)
try:
    most_active_df = si.get_day_most_active()
    trending_tickers = most_active_df['Symbol'].tolist()
except Exception as e:
    print(f"Error fetching trending stocks: {e}")
    trending_tickers = []

# Prepare new entries
new_entries = []
for ticker in trending_tickers[:10]:  # limit to top 10
    try:
        info = si.get_quote_table(ticker, dict_result=True)
        new_entries.append({
            'Ticker': ticker,
            'Company Name': info.get('Quote Source Name', ''),
            'ISIN': '',  # Need external source or static mapping
            'Domain/Topic': 'Trending',
            'inGermany': '',
            'Boycott': '',
            'Reason': '',
            'Ignore': ''
        })
    except Exception as e:
        print(f"Failed to fetch info for {ticker}: {e}")

# Convert to DataFrame
df_new = pd.DataFrame(new_entries)

# Remove duplicates based on Ticker
df_final = df_new[~df_new['Ticker'].isin(existing_df['Ticker'])]

# Merge with existing
df_updated = pd.concat([existing_df, df_final], ignore_index=True)

# Save back to Excel
with pd.ExcelWriter(file_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
    df_updated.to_excel(writer, sheet_name="Stocks", index=False)

print(f"✅ Added {len(df_final)} new trending stocks.")
