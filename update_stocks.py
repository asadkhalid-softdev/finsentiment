import pandas as pd
from requests_html import HTMLSession # Make sure this is in requirements.txt
import sys
import time # For potential delays
import re # For cleaning company name

# --- Custom Scraping Functions ---

def get_yahoo_most_active(count=100):
    """
    Fetches the 'Most Active' stocks table from Yahoo Finance.

    Args:
        count (int): The number of results to fetch (max usually 100 per page).

    Returns:
        pandas.DataFrame: DataFrame containing the most active stocks,
                          or None if fetching/parsing fails.
                          Expected to have a 'Symbol' column.
    """
    url = f"https://finance.yahoo.com/most-active?offset=0&count={count}"
    session = HTMLSession()
    try:
        print(f"Fetching most active stocks from: {url}")
        resp = session.get(url, timeout=20) # Add timeout
        resp.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)

        # Render JavaScript if necessary (often needed for dynamic tables)
        # Note: This requires Chromium to be installed in the environment
        # It might increase runtime significantly. Test without first.
        # try:
        #     print("Rendering JavaScript on page...")
        #     resp.html.render(sleep=1, timeout=30)
        #     print("Rendering complete.")
        # except Exception as render_err:
        #     print(f"⚠️ Warning: Failed to render JavaScript: {render_err}. Proceeding with raw HTML.")

        print("Parsing HTML tables...")
        tables = pd.read_html(resp.html.raw_html)

        if not tables:
            print("❌ Error: No tables found on the most active page.")
            return None

        print(f"Found {len(tables)} tables. Assuming the first table is the correct one.")
        df = tables[0]

        # Basic validation - does it have a 'Symbol' column?
        if 'Symbol' not in df.columns:
             print(f"❌ Error: Could not find 'Symbol' column in the parsed table. Columns found: {df.columns.tolist()}")
             # Let's try to find a column that might be the symbol (heuristic)
             potential_symbol_cols = [col for col in df.columns if isinstance(col, str) and ('symbol' in col.lower() or 'ticker' in col.lower())]
             if potential_symbol_cols:
                 print(f"⚠️ Attempting to rename '{potential_symbol_cols[0]}' to 'Symbol'.")
                 df = df.rename(columns={potential_symbol_cols[0]: 'Symbol'})
             else:
                 # If still no symbol column, we might have the wrong table or page structure changed
                 print("Could not identify a symbol column.")
                 return None # Cannot proceed without symbols

        return df

    except pd.errors.ParserError as pe:
        print(f"❌ Error parsing HTML tables with pandas: {pe}")
        return None
    except Exception as e:
        print(f"❌ Error fetching or processing {url}: {e}")
        return None
    finally:
        session.close() # Ensure session is closed


def get_yahoo_quote_name(ticker):
    """
    Fetches the Company Name for a given ticker from Yahoo Finance quote page.

    Args:
        ticker (str): The stock ticker symbol.

    Returns:
        str: The company name, or the ticker itself if the name cannot be found.
    """
    url = f"https://finance.yahoo.com/quote/{ticker}"
    session = HTMLSession()
    company_name = ticker # Default to ticker if scraping fails

    try:
        print(f"Fetching quote page for {ticker}: {url}")
        resp = session.get(url, timeout=15) # Add timeout
        resp.raise_for_status()

        # The company name is usually in the main H1 tag
        h1_tag = resp.html.find('h1', first=True)

        if h1_tag:
            # Example: "Apple Inc. (AAPL)" -> Extract "Apple Inc."
            # Regex tries to remove the trailing " (SYMBOL)" part
            raw_name = h1_tag.text
            match = re.match(r'^(.*?)\s*\(\s*' + re.escape(ticker) + r'\s*\)\s*$', raw_name, re.IGNORECASE)
            if match:
                company_name = match.group(1).strip()
                if not company_name: # Handle cases where regex might fail or name is just "(TICKER)"
                     company_name = raw_name.replace(f"({ticker})", "").strip() # Fallback cleaning
                if not company_name: # If still empty, use raw H1
                    company_name = raw_name
            else:
                 # If regex doesn't match, maybe the format changed, use the whole h1 text
                 print(f"⚠️ H1 tag format for {ticker} might have changed: '{raw_name}'. Using raw text.")
                 company_name = raw_name.strip() # Use the full H1 text as name

            # Final sanity check for empty name
            if not company_name:
                print(f"⚠️ Could not extract meaningful name for {ticker} from H1. Defaulting to ticker.")
                company_name = ticker

        else:
            print(f"❌ Could not find H1 tag for company name on {ticker}'s page.")
            # As a fallback, you *could* try parsing tables like get_quote_table did,
            # but often the name isn't reliably in those tables.
            # For this specific need (just the name), H1 is the best bet.

    except Exception as e:
        print(f"❌ Error fetching or processing quote page for {ticker}: {e}")
        # Keep company_name as the default (ticker)
    finally:
        session.close()

    # Optional delay to avoid getting blocked by Yahoo
    time.sleep(0.5) # Sleep for 500ms between quote page requests

    return company_name

# --- Main Script Logic (Modified) ---

try:
    # === Config ===
    file_path = "stocks.xlsx"
    sheet_name = "Stocks"
    max_new_tickers = 100 # Use this for fetching most active

    # === Load existing stocks ===
    try:
        existing_df = pd.read_excel(file_path, sheet_name=sheet_name)
        print(f"✅ Loaded {len(existing_df)} existing stocks from {file_path}")
    except FileNotFoundError:
        print(f"⚠️ File {file_path} not found, creating a new one.")
        existing_df = pd.DataFrame(columns=[
            'Ticker', 'Company Name', 'ISIN', 'Domain/Topic',
            'inGermany', 'Boycott', 'Reason', 'Ignore'
        ])
    except Exception as e:
        print(f"❌ Failed to read {file_path}: {e}")
        # Start with an empty DataFrame on read error to avoid losing all data
        existing_df = pd.DataFrame(columns=[
            'Ticker', 'Company Name', 'ISIN', 'Domain/Topic',
            'inGermany', 'Boycott', 'Reason', 'Ignore'
        ])
        print("⚠️ Proceeding with an empty stock list due to read error.")


    # === Fetch trending tickers using custom function ===
    most_active_df = get_yahoo_most_active(count=max_new_tickers)

    if most_active_df is None or 'Symbol' not in most_active_df.columns:
        print("❌ Critical Error: Could not fetch or parse most active stocks. Exiting.")
        sys.exit(1) # Exit if we can't get the source list
        
    print(f"most_active_df.columns: {most_active_df.columns.tolist()}")

    if most_active_df.empty:
         print("⚠️ Fetched most active stocks table, but it was empty.")
         trending_tickers = []
    else:
        # Create a dictionary of ticker-to-name mappings for faster lookup
        ticker_name_map = {}
        if 'Name' in most_active_df.columns:
            ticker_name_map = dict(zip(most_active_df['Symbol'], most_active_df['Name']))
            print("✅ Successfully created ticker-to-name mapping from most_active_df.")
        else:
            print("⚠️ 'Name' column not found in most_active_df. Will use fallback method for company names.")
        
        trending_tickers = most_active_df['Symbol'].tolist()
        print(f"✅ Retrieved {len(trending_tickers)} trending tickers using custom function.")
        # Optional: Print first few tickers
        print(f"   Tickers sample: {trending_tickers[:5]}")


    # === Prepare new entries ===
    new_entries = []
    processed_count = 0

    # Use only up to max_new_tickers found (already limited by fetch count)
    for ticker in trending_tickers:
        if not isinstance(ticker, str) or not ticker.strip():
            print(f"⚠️ Skipping invalid ticker found in list: {ticker}")
            continue

        ticker = ticker.strip().upper() # Normalize ticker

        if ticker in existing_df['Ticker'].astype(str).values:
            # print(f"Skipping duplicate: {ticker}") # Reduce log noise
            continue  # skip duplicates

        processed_count += 1
        print(f"\nProcessing new ticker ({processed_count}/{len(trending_tickers)}): {ticker}")

        try:
            # Get company name from the most_active_df if available
            if ticker in ticker_name_map and ticker_name_map[ticker]:
                company_name = ticker_name_map[ticker]
                print(f"✅ Using company name from most_active_df: {company_name}")
            else:
                # Fallback to scraping the name if not available in most_active_df
                print(f"⚠️ Company name not found in most_active_df for {ticker}. Fetching from quote page...")
                company_name = get_yahoo_quote_name(ticker)

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
            # This catches errors *within* the loop logic, not the scraping functions
            print(f"❌ Skipping {ticker}: Unexpected error during processing – {e}")

    # === Merge & Save ===
    if new_entries:
        df_new = pd.DataFrame(new_entries)
        # Ensure columns match exactly before concat (handles case changes or new/missing cols)
        df_updated = pd.concat([existing_df.astype(str), df_new.astype(str)], ignore_index=True)
        # Optional: Remove duplicates just in case logic missed something, keeping the last (newest) entry
        df_updated = df_updated.drop_duplicates(subset=['Ticker'], keep='last')
        print(f"\n📈 {len(df_new)} new potential stocks processed. Total stocks now: {len(df_updated)}")
    else:
        df_updated = existing_df
        print("\n⚠️ No new tickers found or added. No changes to stock list.")

    # === Write back to Excel ===
    try:
        # Ensure consistent data types before writing
        for col in ['inGermany', 'Boycott', 'Ignore']:
             if col in df_updated.columns:
                 # Convert potential non-string values (like numpy bools if loaded) to empty string or keep existing
                 df_updated[col] = df_updated[col].apply(lambda x: str(x) if pd.notna(x) and str(x).lower() not in ['nan', 'none', ''] else '')

        with pd.ExcelWriter(file_path, engine='openpyxl', mode='w') as writer:
            df_updated.to_excel(writer, sheet_name=sheet_name, index=False)
        print(f"💾 Stocks written to {file_path} (sheet: {sheet_name})")
    except Exception as e:
        print(f"❌ Failed to save updated Excel: {e}")
        # Don't exit here, maybe the processing was still valuable, but log the error
        # raise # Optional: re-raise if saving is critical

except Exception as e:
    print(f"\n🔥 Fatal error in update_stocks.py: {e}")
    # Print traceback for more detail
    import traceback
    traceback.print_exc()
    sys.exit(1)

finally:
    print("\n--- Script execution finished ---")