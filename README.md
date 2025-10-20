# Options Volatility Surface Visualization

## Overview
Options are financial derivatives that provide the right, but not the obligation, to buy (call option) or sell (put option) an underlying asset at a predetermined strike price before or at the expiration date. Option prices consist of two key components:

- **Intrinsic Value**: The difference between the current stock price and the strike price, representing the immediate profit if exercised.
- **Extrinsic Value**: The additional premium beyond intrinsic value, influenced by factors such as implied volatility, time to expiration, and interest rates.

The **Black-Scholes Model** is a widely used mathematical framework for pricing European options. It calculates theoretical option prices based on:
- Current stock price
- Strike price
- Time to expiration
- Risk-free interest rate
- Implied volatility

## Volatility Smile & Important Components
One of the most crucial aspects of option pricing is **implied volatility**, which represents the market's expectation of future volatility. When plotted against strike prices, implied volatility often forms a U-shaped curve, known as the **volatility smile**. This phenomenon arises due to traders pricing in higher risks for deep in-the-money and deep out-of-the-money options, compared to at-the-money options.

Other key components include:
- **Option Greeks**: Sensitivities such as delta, gamma, theta, vega, and rho, which help in risk management and hedging strategies.
- **Put-Call Parity**: A fundamental relationship ensuring that call and put prices remain consistent with each other given the underlying asset and risk-free interest rate.
- **Liquidity & Bid-Ask Spread**: The ease with which options can be traded and the difference between buying and selling prices, which impacts execution efficiency.

Understanding these components allows traders and investors to better assess risk and make informed decisions in options markets.

## Visualizations
<p align="center">
  <img src="https://github.com/user-attachments/assets/ebd9e9bf-ff6f-4b42-bb0a-4279d453863a" width="49%">
  <img src="https://github.com/user-attachments/assets/a0ee5d40-5ade-46a7-ac00-a0cfff8588c4" width="49%">
</p>

### Explanation of Components (Red for Calls, Blue for Puts)
1. **Option Price (Opaque Line)**: The actual price of the call and put options at various strike prices.
2. **Intrinsic Value (Translucent Line)**: The difference between the stock price and the strike price when the option is in the money.
3. **Extrinsic Value (Shaded Region)**: The remaining value beyond intrinsic, which diminishes as expiration approaches.
4. **Implied Volatility (Scatter Points)**: The market's expectation of future stock price movement, plotted as a secondary y-axis. When plotted across different strike prices, implied volatility often forms a **volatility smile**. This effect occurs because deep in-the-money and out-of-the-money options tend to have higher implied volatilities compared to at-the-money options. The reasons for this shape include market sentiment, supply and demand imbalances, and hedging activities by institutional traders. In real markets, implied volatility may also exhibit a **volatility skew**, where out-of-the-money puts often have higher implied volatility due to demand for protective hedging.

## How It Works
The visualization dynamically updates based on the selected stock ticker and expiration date. It fetches option chain data using `yfinance` and calculates intrinsic/extrinsic values, which are plotted using `matplotlib`. The project also includes interactive components:
- **Text Box** for changing the stock ticker (e.g., NVDA, AAPL, TSLA)
- **Slider** for selecting expiration dates
- **Button & Keyboard Event Handling** for updating the chart

## Code Structure
- **Fetching Data**: Uses `yfinance.Ticker` to retrieve live option chain data.
- **Intrinsic & Extrinsic Value Calculation**: 
  - `Intrinsic Value = max(Stock Price - Strike Price, 0)` for calls
  - `Intrinsic Value = max(Strike Price - Stock Price, 0)` for puts
  - `Extrinsic Value = Option Price - Intrinsic Value`
- **Black-Scholes Delta Calculation**: Computes the option delta to visualize price sensitivity.
- **Graphing & Interactivity**: Uses `matplotlib` widgets to enable dynamic stock selection and expiration adjustment.

## Future Enhancements
- Add support for Greeks (Delta, Gamma, Theta, Vega, Rho) visualization
- Compare theoretical Black-Scholes pricing with real option prices
- Implement implied volatility surface plotting
