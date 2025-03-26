# FinSentiment

A sophisticated stock analysis tool that combines technical and fundamental analysis to generate sentiment scores for long-term investment decisions.

## Features

- **Long-term Investment Analysis**: Analyzes stocks using a 5-year historical data period
- **Comprehensive Metrics**:
  - Technical Indicators (RSI, MACD, Moving Averages)
  - Fundamental Analysis (Revenue Growth, Profit Margins, Debt-to-Equity)
  - Market Performance (Beta, Volatility)
- **Sentiment Scoring**: Calculates weighted sentiment scores based on multiple factors
- **Portfolio Optimization**: Automatically allocates investments based on sentiment scores and profit margins
- **Excel Integration**: Reads stock data from Excel and saves analysis results

## Prerequisites

- Python 3.x
- Required Python packages:
  - pandas
  - numpy
  - yfinance
  - openpyxl
  - tqdm

## Installation

1. Clone the repository:
```bash
git clone https://github.com/asadkhalid-softdev/finsentiment.git
cd finsentiment
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

## Usage

1. Prepare your stock data in an Excel file named `Stocks.xlsx` with the following columns:
   - Company Name
   - Ticker
   - Current Price
   - Actual Investment

2. Run the analysis:
```bash
python stock_sentiment.py
```

3. Results will be saved in the same Excel file under a new sheet with the current date.

## Sentiment Score Components

The sentiment score is calculated based on:
- Technical Indicators (40% weight)
- Fundamental Analysis (30% weight)
- Market Performance (30% weight)

## Portfolio Allocation

The tool automatically:
- Calculates optimal portfolio allocation
- Considers sentiment scores and profit margins
- Maintains diversification across sectors
- Targets a total investment of $300

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This tool is for educational and research purposes only. Always conduct your own research and consult with financial advisors before making investment decisions. 