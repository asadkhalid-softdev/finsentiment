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

### Complete Analysis Pipeline

Run the scripts from the repository root in this order:

```bash
python update_stocks.py
python stock_sentiment.py
python calculate_final_score.py
```

The order matters:

1. `update_stocks.py` discovers eligible US, German, and Hong Kong stocks and updates `stocks.xlsx`.
2. `stock_sentiment.py` retrieves market and fundamental data and writes `stocks_metrics.xlsx`.
3. `calculate_final_score.py` reads the completed `Metrics` sheet and adds or refreshes its `Final_Score` column.

`stock_sentiment.py` rebuilds the metrics columns, so rerun
`calculate_final_score.py` whenever the metrics file is refreshed.

Before running the pipeline, prepare `stocks.xlsx` with these columns:

   - Company Name
   - Ticker
   - ISIN (optional)
   - Region (`US`, `DE`, or `HK`)
   - Boycott (Yes/No)
   - Reason (for boycott, if applicable)
   - Ignore (Yes/No)

To calculate scores without changing the workbook:

```bash
python calculate_final_score.py --dry-run
```

To read or write a different workbook:

```bash
python calculate_final_score.py --input path/to/input.xlsx --output path/to/output.xlsx
```

By default, the scoring script updates `stocks_metrics.xlsx` in place. It preserves
the existing workbook and updates the same `Final_Score` column on repeat runs.

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

## Final Score

`Final_Score` is a 0-100, region-relative screening score for comparing the
current stock universe. It is not a price target or a forecast of percentage
return.

| Factor | Weight | Direction |
| --- | ---: | --- |
| Profitability (`Profit_Margin`) | 25% | Higher is better |
| Value (`PE_Ratio`) | 25% | Lower positive P/E is better |
| Growth quality | 20% | Revenue growth rewarded more when profitability is strong |
| Momentum (`1Y_Momentum`) | 15% | Higher is better |
| Balance sheet (`Debt_To_Equity`) | 10% | Lower non-negative leverage is better |
| Analyst rating (`Analyst_Rating`) | 5% | Lower is better; Yahoo uses 1 = Strong Buy, 5 = Sell |

Each metric is cleaned, winsorized at its region's 5th and 95th percentiles,
and converted to a percentile score. The calculation is:

```text
GrowthQuality = RevenueGrowthPercentile
                × (0.5 + 0.5 × ProfitabilityPercentile)

BaseScore = weighted average of the available factor scores

FinalScore = 100 × BaseScore × (0.85 + 0.15 × available factor weight)
```

A row must contain at least 60% of the weighted factor inputs to receive a
score. Missing inputs are not treated as zero, but the completeness multiplier
penalizes incomplete rows.

The existing `Sentiment_Score`, `3Y_Momentum`, `Volume_Trend`, `Market_Cap`,
and `Dividend_Yield` are deliberately excluded:

- `Sentiment_Score` already incorporates fundamentals and momentum, so including
  it would double-count those signals.
- Academic momentum is closer to an intermediate-horizon signal than a raw
  three-year return.
- Volume and market capitalization are more appropriate as eligibility and
  liquidity controls than as simple positive return factors.
- Dividend yield alone is not a quality measure and can be elevated by a falling
  share price.

The factor design is informed by established value, profitability, quality,
and momentum research, including:

- Fama and French, *A Five-Factor Asset Pricing Model*:
  https://doi.org/10.1016/j.jfineco.2014.10.010
- Novy-Marx, *The Other Side of Value: The Gross Profitability Premium*:
  https://doi.org/10.1016/j.jfineco.2013.01.003
- Jegadeesh and Titman, *Returns to Buying Winners and Selling Losers*:
  https://doi.org/10.1111/j.1540-6261.1993.tb04702.x
- Asness, Moskowitz, and Pedersen, *Value and Momentum Everywhere*:
  https://doi.org/10.1111/jofi.12021

The exact weights are judgmental and have not been validated as a standalone
trading strategy. A proper evaluation requires point-in-time, out-of-sample
backtesting that includes delisted securities, transaction costs, and currency
effects.

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
