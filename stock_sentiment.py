import pandas as pd
import yfinance as yf
import numpy as np
from datetime import datetime, timedelta
import time
from tqdm import tqdm

total_investment = 2000
n_stocks = 20

def calculate_technical_indicators(hist_data):
    """Calculate technical indicators from historical data."""
    if hist_data.empty:
        return {}
    
    # Calculate 200-day moving average (long-term trend)
    hist_data['MA200'] = hist_data['Close'].rolling(window=200).mean()
    
    # Calculate 1-year and 3-year momentum
    hist_data['1Y_Momentum'] = (hist_data['Close'].iloc[-1] - hist_data['Close'].iloc[-252]) / hist_data['Close'].iloc[-252] * 100
    hist_data['3Y_Momentum'] = (hist_data['Close'].iloc[-1] - hist_data['Close'].iloc[-756]) / hist_data['Close'].iloc[-756] * 100
    
    # Get latest values
    current_price = hist_data['Close'].iloc[-1]
    ma200 = hist_data['MA200'].iloc[-1]
    
    # Calculate long-term volume trend (1-year average vs 3-year average)
    avg_volume_1y = hist_data['Volume'].iloc[-252:].mean()
    avg_volume_3y = hist_data['Volume'].mean()
    volume_trend = avg_volume_1y / avg_volume_3y
    
    return {
        'price_above_ma200': current_price > ma200,
        '1y_momentum': hist_data['1Y_Momentum'].iloc[-1],
        '3y_momentum': hist_data['3Y_Momentum'].iloc[-1],
        'volume_trend': volume_trend,
        'current_price': current_price
    }

def calculate_sentiment_score(technical_data, stock_info):
    """Calculate overall sentiment score based on various factors."""
    score = 50  # Start with neutral score
    
    # Technical factors (max 30 points)
    if technical_data:
        # Long-term trend (10 points)
        if technical_data['price_above_ma200']:
            score += 10
        elif technical_data['price_above_ma200'] is False:
            score += 5
            
        # Momentum (10 points)
        momentum_1y = technical_data['1y_momentum']
        momentum_3y = technical_data['3y_momentum']
        
        if momentum_1y > 10 and momentum_3y > 30:  # Strong long-term growth
            score += 10
        elif momentum_1y > 5 and momentum_3y > 15:  # Moderate growth
            score += 7
        elif momentum_1y > 0 and momentum_3y > 0:  # Positive growth
            score += 5
            
        # Volume trend (10 points)
        volume_trend = technical_data['volume_trend']
        if volume_trend > 1.5:  # Strong institutional interest
            score += 10
        elif volume_trend > 1.2:  # Moderate interest
            score += 7
        elif volume_trend > 1.0:  # Stable interest
            score += 5
            
    # Fundamental factors (max 40 points)
    if stock_info:
        # P/E Ratio (10 points)
        if 'trailingPE' in stock_info and stock_info['trailingPE'] is not None:
            pe = stock_info['trailingPE']
            if 10 <= pe <= 25:
                score += 10
            elif 5 <= pe <= 30:
                score += 7
            else:
                score += 3
                
        # Profit margins (10 points)
        if 'profitMargins' in stock_info and stock_info['profitMargins'] is not None:
            profit_margin = stock_info['profitMargins']
            if profit_margin > 0.2:
                score += 10
            elif profit_margin > 0.1:
                score += 7
            elif profit_margin > 0:
                score += 5
                
        # Revenue growth (10 points)
        if 'revenueGrowth' in stock_info and stock_info['revenueGrowth'] is not None:
            revenue_growth = stock_info['revenueGrowth']
            if revenue_growth > 0.2:  # 20% growth
                score += 10
            elif revenue_growth > 0.1:  # 10% growth
                score += 7
            elif revenue_growth > 0:  # Positive growth
                score += 5
                
        # Debt to equity (10 points)
        if 'debtToEquity' in stock_info and stock_info['debtToEquity'] is not None:
            debt_to_equity = stock_info['debtToEquity']
            if debt_to_equity < 0.5:  # Low debt
                score += 10
            elif debt_to_equity < 1.0:  # Moderate debt
                score += 7
            elif debt_to_equity < 2.0:  # High but manageable debt
                score += 5
                
    return min(100, max(0, score))

def calculate_investment_allocation(df, total_investment=300, n_stocks=20):
    """Calculate investment allocation based on sentiment scores and profit margins for top 20 stocks."""
    # Convert profit margin to numeric type and multiply by 100 for better readability

    # Drop rows with any missing values in key columns
    key_columns = [
        'Sentiment_Score', 'Profit_Margin', 'Current_Price',
        '1Y_Momentum', '3Y_Momentum', 'Volume_Trend',
        'PE_Ratio', 'Revenue_Growth', 'Debt_To_Equity'
    ]
    df = df.dropna(subset=key_columns)

    df = df.sort_values(['Sentiment_Score', 'Profit_Margin'], 
                          ascending=[False, False], 
                          na_position='last',
                          kind='stable')
    df['Profit_Margin'] = pd.to_numeric(df['Profit_Margin'], errors='coerce') * 100
    
    # Sort with stable sorting to maintain relative positions of equal values
    top_df = df.head(n_stocks).copy()
    
    print("\nDebug - Selected stocks before allocation:")
    print(top_df[['Company Name', 'Ticker', 'Sentiment_Score', 'Profit_Margin']].to_string())
    
    # Calculate weights based on sentiment scores for top stocks
    top_df['Weight'] = top_df['Sentiment_Score'] / top_df['Sentiment_Score'].sum()
    
    # Calculate investment amount for each stock
    top_df['Investment_Amount'] = top_df['Weight'] * total_investment
    
    # Round investment amounts to 2 decimal places
    top_df['Investment_Amount'] = top_df['Investment_Amount'].round(2)
    
    # Calculate fractional shares (keeping 4 decimal places for precision)
    top_df['Shares'] = (top_df['Investment_Amount'] / top_df['Current_Price']).round(4)
    
    # Calculate actual investment amount based on shares
    top_df['Actual_Investment'] = (top_df['Shares'] * top_df['Current_Price']).round(2)
    
    # Calculate percentage of portfolio
    top_df['Portfolio_Percentage'] = (top_df['Actual_Investment'] / top_df['Actual_Investment'].sum() * 100).round(2)
    
    # Update the main dataframe with investment information
    df['Actual_Investment'] = 0.0
    df['Portfolio_Percentage'] = 0.0
    df['Shares'] = 0.0
    
    # Update values for top stocks
    for idx in top_df.index:
        df.loc[idx, 'Actual_Investment'] = top_df.loc[idx, 'Actual_Investment']
        df.loc[idx, 'Portfolio_Percentage'] = top_df.loc[idx, 'Portfolio_Percentage']
        df.loc[idx, 'Shares'] = top_df.loc[idx, 'Shares']
    
    # Convert profit margin back to decimal form
    df['Profit_Margin'] = df['Profit_Margin'] / 100
    
    return df

def update_stock_analysis():
    try:
        # Read the Stocks.xlsx file, specifically the 'Stocks' sheet
        df = pd.read_excel('stocks.xlsx', sheet_name='Stocks')
        # Filter out rows where inGermany is 'No' or Boycott is 'Yes'
        df = df[(df['inGermany'] != 'No') & (df['Boycott'] != 'Yes') & (df['Ignore'] != 'Yes')]
        print(f"Loaded {len(df)} stocks from Stocks.xlsx (excluding non-German and boycotted stocks)")
        
        # Initialize results
        results = []
        
        # Create progress bar
        pbar = tqdm(df.iterrows(), total=len(df), desc="Processing stocks", ncols=100)
        
        for _, row in pbar:
            name = row['Company Name']
            symbol = row['Ticker']
            
            # Update progress bar description with current company
            pbar.set_description(f"Processing {name[:30]}..." if len(name) > 30 else f"Processing {name}...")
            
            try:
                # Create Ticker object
                ticker = yf.Ticker(symbol)
                
                # Get historical data (5 years)
                hist_data = ticker.history(period='5y')
                if hist_data.empty:
                    print(f"\nNo historical data available for {name}")
                    continue
                    
                # Get stock info
                stock_info = ticker.info
                
                # Calculate technical indicators
                technical_data = calculate_technical_indicators(hist_data)
                
                # Calculate sentiment score
                sentiment_score = calculate_sentiment_score(technical_data, stock_info)
                
                # Store results
                result = {
                    'Company Name': name,
                    'Ticker': symbol,
                    'Domain/Topic': row['Domain/Topic'],
                    'Sentiment_Score': sentiment_score,
                    'Current_Price': technical_data['current_price'],
                    '1Y_Momentum': technical_data['1y_momentum'],
                    '3Y_Momentum': technical_data['3y_momentum'],
                    'Volume_Trend': technical_data['volume_trend']
                }
                
                # Add additional metrics if available
                if stock_info:
                    result.update({
                        'Market_Cap': stock_info.get('marketCap'),
                        'PE_Ratio': stock_info.get('trailingPE'),
                        'Profit_Margin': stock_info.get('profitMargins'),
                        'Revenue_Growth': stock_info.get('revenueGrowth'),
                        'Debt_To_Equity': stock_info.get('debtToEquity'),
                        'Dividend_Yield': stock_info.get('dividendYield'),
                        'Analyst_Rating': stock_info.get('recommendationMean')
                    })
                    
                results.append(result)
                
                # Sleep to avoid hitting rate limits
                time.sleep(0.5)
                
            except Exception as e:
                print(f"\nError updating {name}: {str(e)}")
                continue
        
        # Close progress bar
        pbar.close()
        
        print("\nCalculating investment allocations...")
        
        # Create results DataFrame
        results_df = pd.DataFrame(results)
        
        # Calculate investment allocation
        results_df = calculate_investment_allocation(results_df, total_investment=total_investment, n_stocks=n_stocks)
        
        # Sort by sentiment score in descending order
        results_df = results_df.sort_values('Sentiment_Score', ascending=False)
        
        # Get current date for sheet name
        current_date = datetime.now().strftime('%Y-%m-%d')
        
        print("Saving results to Excel...")
        
        # Read existing Excel file
        try:
            with pd.ExcelWriter('Stocks.xlsx', mode='a', if_sheet_exists='replace') as writer:
                results_df.to_excel(writer, sheet_name=current_date, index=False)
        except FileNotFoundError:
            # If file doesn't exist, create it
            results_df.to_excel('Stocks.xlsx', sheet_name=current_date, index=False)
        
        print(f"\nUpdate complete! Results saved to Stocks.xlsx in sheet '{current_date}'")
        
        if not results_df.empty:
            print("\nTop 5 stocks by sentiment score and profit margin:")
            display_columns = ['Company Name', 'Ticker', 'Sentiment_Score', 'Profit_Margin', 'Revenue_Growth', 
                             'Debt_To_Equity', 'Current_Price', 'Actual_Investment', 'Shares', 'Portfolio_Percentage']
            pd.set_option('display.float_format', lambda x: '%.2f' % x)
            print(results_df[display_columns].head().to_string())
            
            # Print total investment summary
            total_invested = results_df['Actual_Investment'].sum()
            print(f"\nTotal Investment: ${total_invested:.2f}")
            print(f"Remaining Cash: ${300 - total_invested:.2f}")
            
            # Print portfolio allocation summary for top 20
            print(f"\nPortfolio Allocation Summary (Top {n_stocks}):")
            allocation_summary = results_df[results_df['Shares'] > 0][['Company Name', 'Ticker', 'Sentiment_Score', 
                                                                     'Profit_Margin', 'Revenue_Growth', 'Debt_To_Equity',
                                                                     'Shares', 'Actual_Investment', 'Portfolio_Percentage']]
            print(allocation_summary.to_string())
            
    except Exception as e:
        print(f"Error updating analysis: {str(e)}")

if __name__ == "__main__":
    print("Starting stock analysis update...")
    update_stock_analysis() 