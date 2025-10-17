import yfinance as yf
import numpy as np
from scipy.stats import norm
import matplotlib.pyplot as plt
from matplotlib.widgets import TextBox, Slider, Button
import time

# Used for legend components
import matplotlib.patches as mpatches
import matplotlib.lines as mlines

ticker = 'NVDA'  # Other high-liquidity tickers include AAPL QQQ TSLA SPY
date = 0  # Chosen index for expiration date
rate = 0.0443  # Risk-free rate
adjust = True  # Flag to adjust x- and y-axis
delta = False # display against strike price, not delta

red = (1, 0, 0.25)
blue = (0.1, 0.35, 1)
purple = (0.5, 0.1, 0.9)

# Function to fetch and plot option data so we can update without restarting
def plot_options(ax, ax_iv, ticker, date, adjust, delta):
    stock_data = yf.Ticker(ticker)
    price = stock_data.history_metadata['regularMarketPrice']  # Store current price

    # List available expiration dates
    global expirations
    expirations = stock_data.options
    chosen_expiration = expirations[date]  # Choose the first expiration date (since date = 0) as an example

    # Fetch the option chain for the chosen expiration date
    option_chain = stock_data.option_chain(chosen_expiration)
    calls = option_chain.calls
    puts = option_chain.puts

    # Extract strike prices and last prices for calls and puts
    common_strikes = calls.merge(puts, on='strike', suffixes=('_call', '_put'))
    strike_prices = common_strikes['strike']

    # Extract the implied volatilities for each call and put
    call_volatility = calls[calls['strike'].isin(strike_prices)]['impliedVolatility'].values
    put_volatility = puts[puts['strike'].isin(strike_prices)]['impliedVolatility'].values

    call_prices = common_strikes['lastPrice_call']
    call_strikes = calls[calls['strike'].isin(strike_prices)]['strike'].values
    put_prices = common_strikes['lastPrice_put']
    put_strikes = puts[puts['strike'].isin(strike_prices)]['strike'].values

    # Calculate intrinsic values as the difference between currrent price and strike price
    call_intrinsic = np.maximum(0, price - strike_prices)  # Call intrinsic values
    put_intrinsic = np.maximum(0, strike_prices - price)  # Put intrinsic values

    xlim, ylim = ax.get_xlim(), ax.get_ylim()  # Store current x- and y-axis values
    volatility_ylim = ax_iv.get_ylim()  # Store current y-axis values for implied volatility

    # Clear previous graph and add new y-axis for IV
    ax.clear()
    ax_iv.clear()

    if delta:
        call_deltas = calc_delta(True, price, strike_prices, rate, call_volatility, 1)
        put_deltas = calc_delta(False, price, strike_prices, rate, put_volatility, 1)

        ax.plot(call_prices, call_deltas, label="Call Option Price", color=blue)
        ax.plot(put_prices, put_deltas,label="Put Option Price", color=red)

        # Plot intrinsic and extrinsic values as stacked components
        ax.plot(call_intrinsic, call_deltas, label="Call Intrinsic", color=blue, alpha=0.5)
        ax.fill_between(call_deltas, call_intrinsic, call_prices, color=blue, alpha=0.25, label="Call Extrinsic")
        
        ax.plot(put_intrinsic, put_deltas, label="Put Intrinsic", color=red, alpha=0.5)
        ax.fill_between(put_deltas, put_intrinsic, put_prices, color=red, alpha=0.25, label="Put Extrinsic")

        ax.set_xlabel("Option Price")
        ax.set_ylabel("Delta")
        # ax_iv.set_ylabel("Implied Volatility")
        # ax_iv.yaxis.set_label_position('right')
        ax.set_title(f"Real-Life Call and Put Option Prices vs. Delta ({ticker}) - Expiration: {chosen_expiration}")

        ax.axvline(price, linestyle='--', color='gray', label='Stock Price')  # Vertical line for stock price

        ax_iv.clear()
    else:
        ax.plot(strike_prices, call_prices, label="Call Option Price", color=blue)
        ax.plot(strike_prices, put_prices, label="Put Option Price", color=red)

        # Plot intrinsic and extrinsic values as stacked components
        ax.plot(strike_prices, call_intrinsic, label="Call Intrinsic", color=blue, alpha=0.5)
        ax.fill_between(strike_prices, call_intrinsic, call_prices, color=blue, alpha=0.25, label="Call Extrinsic")
        
        ax.plot(strike_prices, put_intrinsic, label="Put Intrinsic", color=red, alpha=0.5)
        ax.fill_between(strike_prices, put_intrinsic, put_prices, color=red, alpha=0.25, label="Put Extrinsic")

        # Plot implied volatilities if they exist
        if call_volatility is not None:
            ax_iv.scatter(call_strikes, call_volatility, color='blue', marker='o', label="Call IV", alpha=0.6)
        if put_volatility is not None:
            ax_iv.scatter(put_strikes, put_volatility, color='red', marker='o', label="Put IV", alpha=0.6)

        ax.axvline(price, linestyle='--', color='gray', label='Stock Price')  # Vertical line for stock price

        ax.set_xlabel("Strike Price")
        ax.set_ylabel("Option Price")
        ax_iv.set_ylabel("Implied Volatility")
        ax_iv.yaxis.set_label_position('right')
        ax.set_title(f"Real-Life Call and Put Option Prices vs. Strike Prices ({ticker}) - Expiration: {chosen_expiration}")


    if adjust:  # If the ticker has been changed, adjust the x- and y-axis
        ax.relim()
        ax.autoscale_view()
        ax_iv.relim()
        ax_iv.autoscale_view()
        adjust = False
    else:  # Otherwise, keep them the same for easier comparison, can remove this block if not needed
        ax.set_xlim(xlim)
        ax.set_ylim(ylim)
        ax_iv.set_ylim(volatility_ylim)

    ax.grid(True)

    # Defining legend components
    option_price_line = mlines.Line2D([], [], color=purple, label="Option Price")
    intrinsic_line = mlines.Line2D([], [], color=purple, alpha=0.5, label="Intrinsic Value", linewidth=2)
    extrinsic_patch = mpatches.Patch(color=purple, alpha=0.25, label="Extrinsic Value")
    volatility_marker = mlines.Line2D([], [], color=purple, marker="o", linestyle="None", label="Implied Volatility")

    ax.legend(handles=[option_price_line, intrinsic_line, extrinsic_patch, volatility_marker])

    fig.canvas.draw_idle()

# Calculate the deltas at each strike price to replace the x-axis values
def calc_delta(call, price, strike_prices, rate, iv, time):
    strike_prices = np.array(strike_prices)
    iv = np.array(iv)
    time = np.array(time)

    d1 = (np.log(price/strike_prices) + (rate + iv**2 / 2) * time) / (iv * np.sqrt(time))
    if(call):
        return norm.cdf(d1)
    else:
        return norm.cdf(d1) -1

# Initial plot setup
plt.style.use('dark_background')
fig, ax = plt.subplots(figsize=(10, 6))  # Subplots needed to add widgets
ax_iv = ax.twinx() # Add a second y-axis for implied volatility
ax_iv.set_ylim(0, 1)
plot_options(ax, ax_iv, ticker, date, adjust, delta)

# Adjust whitespace of the plot
fig.subplots_adjust(top=0.925, left=0.09, bottom=0.1375, right=0.91)


# Add a ticker input box below the plot
ax_box = fig.add_axes([0.15, 0.035, 0.1, 0.05])  # Position of input box

def submit(text):
    global ticker, date, adjust
    date = 0  # Reset the expiration date
    ticker = text  # Update the ticker symbol
    exp_slider.set_val(date)  # Reset the slider value
    adjust = True  # x- and y-axis need to be adjusted for new ticker

    # Reset expiration dates and slider range
    exp_slider.valmax = len(yf.Ticker(ticker).options) - 1  # Update slider max based on new expiration count
    exp_slider.ax.set_xlim(exp_slider.valmin, exp_slider.valmax)  # Update slider limits

text_box = TextBox(
    ax=ax_box, 
    label='Stock Ticker ', 
    initial=ticker, 
    color='black', 
    hovercolor='darkgray'
)
text_box.on_submit(submit)

# Label for users to type lowercase
ax_label = fig.add_axes([0.15, 0.02, 0.1, 0.02])  # Position of text
ax_label.axis("off")
ax_label.text(0.5, 0, "Lower/Uppercase Work", ha="center", va="center", fontsize=7, color="gray")


# Add an expiration date slider
ax_exp = fig.add_axes([0.4, 0.025, 0.4, 0.03])  # Position of slider

def adjust_date(val):
    global date, adjust
    date = val  # Update the expiration date
    adjust = False  # x- and y-axis don't need to be adjusted, same ticker

exp_slider = Slider(
    ax=ax_exp,
    label='Expiration Date ',
    valmin=0,
    valmax=len(expirations) - 1,  # Vary max number of expiration dates from stock to stock
    valinit=date,
    valstep=1,
    facecolor=(0.7, 0.4, 1),
)

exp_slider.on_changed(adjust_date)


# Add an "Update" button
ax_button = fig.add_axes([0.85, 0.035, 0.1, 0.05])  # Position of button
update_button = Button(ax_button, 'Update', color='black', hovercolor='darkgray')

# Label for users to press Enter to Update
ax_label = fig.add_axes([0.85, 0.02, 0.1, 0.02])  # Position of text
ax_label.axis("off")
ax_label.text(0.5, 0, "Press Enter to Update", ha="center", va="center", fontsize=7, color="gray")

def update_plot(event):
    plot_options(ax, ax_iv, ticker, date, adjust, delta)


# Bind the Enter key to trigger the update function
def on_enter_press(event):
    if event.key == 'enter':
        update_plot(event)

# Connect the Enter key event to the figure
fig.canvas.mpl_connect('key_press_event', on_enter_press)

update_button.on_clicked(update_plot)



plt.show()