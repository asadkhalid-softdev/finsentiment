import sys
import pandas as pd
import yfinance as yf
from yfinance import EquityQuery

FILE_PATH = "stocks.xlsx"
SHEET_NAME = "Stocks"
COUNT_PER_REGION = 100


def fetch_most_active(region: str, count: int = COUNT_PER_REGION) -> list[dict]:
    """Fetch most-active equities for a given region using yfinance EquityQuery."""
    if region == 'US':
        query = EquityQuery('and', [
            EquityQuery('eq', ['region', 'us']),
            EquityQuery('is-in', ['exchange', 'NMS', 'NYQ', 'NGM', 'NCM']),
            EquityQuery('gt', ['intradaymarketcap', 500_000_000]),
            EquityQuery('gt', ['dayvolume', 1_000_000]),
        ])
    elif region == 'DE':
        query = EquityQuery('and', [
            EquityQuery('eq', ['region', 'de']),
            EquityQuery('is-in', ['exchange', 'GER', 'FRA']),
            EquityQuery('gt', ['intradaymarketcap', 100_000_000]),
            EquityQuery('gt', ['dayvolume', 1_000]),
        ])
    elif region == 'HK':
        query = EquityQuery('and', [
            EquityQuery('eq', ['region', 'hk']),
            EquityQuery('eq', ['exchange', 'HKG']),
            EquityQuery('gt', ['intradaymarketcap', 500_000_000]),
            EquityQuery('gt', ['dayvolume', 100_000]),
        ])
    else:
        raise ValueError(f"Unsupported region: {region}")

    result = yf.screen(query, size=count, sortField='dayvolume', sortAsc=False)
    quotes = result.get('quotes', [])
    total = result.get('total', 0)
    print(f"  [{region}] fetched {len(quotes)} of {total} available stocks")

    entries = []
    for q in quotes:
        symbol = q.get('symbol', '').strip().upper()
        name = q.get('shortName') or q.get('longName') or symbol
        # Whitespace only — str.strip(' \tINR') wrongly strips leading letters I/N/R (e.g. "NVIDIA" → "VIDIA")
        name = str(name).strip()
        if not symbol:
            continue
        entries.append({
            'Ticker': symbol,
            'Company Name': name,
            'ISIN': '',
            'Region': region,
            'Boycott': '',
            'Reason': '',
            'Ignore': '',
        })
    return entries


def load_existing(file_path: str, sheet_name: str) -> pd.DataFrame:
    expected_cols = ['Ticker', 'Company Name', 'ISIN', 'Region',
                     'Boycott', 'Reason', 'Ignore']
    try:
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        print(f"Loaded {len(df)} existing stocks from {file_path}")
        if 'Domain/Topic' in df.columns:
            df = df.drop(columns=['Domain/Topic'])
        # Migrate: rename inGermany -> Region if present
        if 'inGermany' in df.columns and 'Region' not in df.columns:
            df = df.rename(columns={'inGermany': 'Region'})
            print("  Migrated 'inGermany' column to 'Region'")
        elif 'inGermany' in df.columns:
            df = df.drop(columns=['inGermany'])
        # Ensure all expected columns exist
        for col in expected_cols:
            if col not in df.columns:
                df[col] = ''
        return df[expected_cols]
    except FileNotFoundError:
        print(f"File {file_path} not found, starting fresh.")
        return pd.DataFrame(columns=expected_cols)
    except Exception as e:
        print(f"Failed to read {file_path}: {e}")
        return pd.DataFrame(columns=expected_cols)


def main():
    existing_df = load_existing(FILE_PATH, SHEET_NAME)
    existing_tickers = set(existing_df['Ticker'].astype(str).str.strip().str.upper())

    all_new_entries = []
    for region in ['US', 'DE', 'HK']:
        print(f"\nFetching most-active stocks for region: {region}")
        try:
            entries = fetch_most_active(region)
        except Exception as e:
            print(f"  Error fetching {region}: {e}")
            continue

        new_for_region = [e for e in entries if e['Ticker'] not in existing_tickers]
        print(f"  {len(new_for_region)} new tickers (skipped {len(entries) - len(new_for_region)} duplicates)")
        all_new_entries.extend(new_for_region)
        existing_tickers.update(e['Ticker'] for e in new_for_region)

    if all_new_entries:
        new_df = pd.DataFrame(all_new_entries)
        updated_df = pd.concat([existing_df, new_df], ignore_index=True)
        updated_df = updated_df.drop_duplicates(subset=['Ticker'], keep='last')
        print(f"\n{len(all_new_entries)} new stocks added. Total: {len(updated_df)}")
    else:
        updated_df = existing_df
        print("\nNo new tickers found. Stock list unchanged.")

    try:
        with pd.ExcelWriter(FILE_PATH, engine='openpyxl', mode='w') as writer:
            updated_df.to_excel(writer, sheet_name=SHEET_NAME, index=False)
        print(f"Saved to {FILE_PATH} (sheet: {SHEET_NAME})")
    except Exception as e:
        print(f"Failed to save {FILE_PATH}: {e}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        print("\n--- Script execution finished ---")
