import pandas as pd
from yahoo_fin import stock_info as si
from requests_html import HTMLSession

# === Config ===
file_path = "stocks.xlsx"
sheet_name = "Stocks"
max_new_tickers = 10

# === Load existing stocks ===
try:
    existing_df = pd.read_excel(file_path, sheet_name=sheet_name)
except FileNotFoundError:
    print(f"⚠️ File {file_path} not found, creating a new one.")
    existing_df = pd.DataFrame(columns=[
        'Ticker', 'Company Name', 'ISIN', 'Domain/Topic',
        'inGermany', 'Boycott', 'Reason', 'Ignore'
    ])
except Exception as e:
    print(f"❌ Failed to read {file_path}: {e}")
    existing_df = pd.DataFrame(columns=[
        'Ticker', 'Company Name', 'ISIN', 'Domain/Topic',
        'inGermany', 'Boycott', 'Reason', 'Ignore'
    ])

# === Fetch trending tickers ===
try:
    most_active_df = si.get_day_most_active()
    print("most_active_df: ", most_active_df)

    trending_tickers = most_active_df['Symbol'].tolist()
    print(f"✅ Retrieved {len(trending_tickers)} trending tickers.")
except Exception as e:
    print(f"❌ Error fetching trending stocks: {e}")
    trending_tickers = []

# === Prepare new entries ===
new_entries = []

for ticker in trending_tickers[:max_new_tickers]:
    if ticker in existing_df['Ticker'].values:
        continue  # skip duplicates

    try:
        info = si.get_quote_table(ticker, dict_result=True)
        company_name = info.get('Quote Source Name', ticker)

        new_entries.append({
            'Ticker': ticker,
            'Company Name': company_name,
            'ISIN': '',  # placeholder
            'Domain/Topic': 'Trending',
            'inGermany': '',
            'Boycott': '',
            'Reason': '',
            'Ignore': ''
        })

        print(f"✅ Added {ticker} ({company_name})")

    except Exception as e:
        print(f"❌ Skipping {ticker}: Failed to fetch quote table – {e}")

# === Merge & Save ===
if new_entries:
    df_new = pd.DataFrame(new_entries)
    df_updated = pd.concat([existing_df, df_new], ignore_index=True)
    print(f"\n📈 {len(df_new)} new stocks added.")
else:
    df_updated = existing_df
    print("\n⚠️ No new valid tickers found. No changes to stock list.")

# === Write back to Excel ===
try:
    with pd.ExcelWriter(file_path, engine='openpyxl', mode='w') as writer:
        df_updated.to_excel(writer, sheet_name=sheet_name, index=False)
    print(f"💾 Stocks written to {file_path} (sheet: {sheet_name})")
except Exception as e:
    print(f"❌ Failed to save updated Excel: {e}")
