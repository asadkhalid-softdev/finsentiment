# FinSentiment

A sophisticated stock analysis tool that combines technical and fundamental analysis to generate sentiment scores for long-term investment decisions.

## Features

- **Long-term Investment Analysis**: Analyzes stocks using a 5-year historical data period
- **Comprehensive Metrics**:
  - Technical Indicators (Moving Averages, 1-Year and 3-Year Momentum, Volume Trends)
  - Fundamental Analysis (P/E Ratio, Revenue Growth, Profit Margins, Debt-to-Equity)
  - Market Performance (Volatility, Growth Patterns)
- **Sentiment Scoring**: Calculates weighted sentiment scores for each stock based on multiple factors
- **Portfolio Optimization**: Automatically allocates investment for top performing stocks
- **Stock Discovery**: Includes a tool to discover and add trending stocks from Yahoo Finance
- **Filtering Options**: Filter stocks by availability in Germany, exclude boycotted companies
- **Excel Integration**: Reads from and writes to Excel spreadsheets for easy data management

## Prerequisites

- Python 3.8+
- Required Python packages (see requirements.txt):
  - pandas
  - numpy
  - yfinance
  - openpyxl
  - tqdm
  - requests_html
  - html5lib
  - lxml_html_clean

## Installation

1. Clone the repository:
```bash
git clone https://github.com/asadkhalid-softdev/finsentiment.git
cd finsentiment
```

2. Create a virtual environment:
```bash
python -m uv venv --python 3.10
```

3. Activate the virtual environment:
```bash
# On Windows
.venv\Scripts\activate
# On macOS/Linux
source .venv/bin/activate
```

4. Install required packages:
```bash
pip install -r requirements.txt
```

## Usage

### Stock Analysis

1. Prepare your stock data in an Excel file named `stocks.xlsx` with the following columns:
   - Company Name
   - Ticker
   - ISIN (optional)
   - Domain/Topic (optional)
   - inGermany (Yes/No)
   - Boycott (Yes/No)
   - Reason (for boycott, if applicable)
   - Ignore (Yes/No)

2. Run the sentiment analysis:
```bash
python stock_sentiment.py
```

3. Results will be saved to `stocks_metrics.xlsx` with sentiment scores and investment allocation.

### Updating Stock List

To discover and add trending stocks:

```bash
python update_stocks.py
```

This will fetch the most active stocks from Yahoo Finance and add them to your stocks.xlsx file.

## Sentiment Score Components

The sentiment score is calculated based on:
- Technical Indicators (30% weight)
  - Long-term trend (using 200-day moving average)
  - 1-year and 3-year momentum
  - Volume trends
- Fundamental Analysis (40% weight)
  - P/E Ratio
  - Profit Margins
  - Revenue Growth
  - Debt-to-Equity Ratio
- Market Performance (30% weight, implied from technical and fundamental analysis)

## Portfolio Allocation

The tool automatically:
- Selects the top stocks based on sentiment scores and profit margins
- Calculates optimal portfolio allocation based on weighted scores
- Provides investment amount, shares to purchase, and portfolio percentage for each stock
- Targets a total investment of $2000 across the top 20 stocks by default

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This tool is for educational and research purposes only. Always conduct your own research and consult with financial advisors before making investment decisions. 
