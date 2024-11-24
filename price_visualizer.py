import yfinance as yf
import numpy as np
from scipy.stats import norm
import matplotlib.pyplot as plt
from matplotlib.widgets import TextBox, Slider, Button

ticker = 'DJT'  # Define the ticker symbol and fetch data
date = 0  # Chosen index for expiration date
adjust = True  # Flag to adjust x- and y-axis

# Function to fetch and plot option data so we can update without restarting
def plot_options(ax, ticker, date, adjust):
    stock_data = yf.Ticker(ticker)
    price = stock_data.history_metadata['regularMarketPrice']  # Store current price

    # List available expiration dates
    global expirations
    expirations = stock_data.options
    chosen_expiration = expirations[date]  # Choose the first expiration date as an example

    # Fetch the option chain for the chosen expiration date
    option_chain = stock_data.option_chain(chosen_expiration)
    calls = option_chain.calls
    puts = option_chain.puts

    # Extract strike prices and last prices for calls and puts
    common_strikes = calls.merge(puts, on='strike', suffixes=('_call', '_put'))
    strike_prices = common_strikes['strike']
    call_prices = common_strikes['lastPrice_call']
    put_prices = common_strikes['lastPrice_put']

    xlim, ylim = ax.get_xlim(), ax.get_ylim()  # Store current x- and y-axis values
    ax.clear()
    ax.plot(strike_prices, call_prices, label="Call Option Price", color="blue")
    ax.plot(strike_prices, put_prices, label="Put Option Price", color="red")
    ax.axvline(price, linestyle='--', color='black', label='Stock Price')

    if adjust:  # If the ticker has been changed, adjust the x- and y-axis
        ax.relim()
        ax.autoscale_view()
        adjust = False
    else:  # Otherwise, keep them the same for easier comparison, can remove this block if not needed
        ax.set_xlim(xlim)
        ax.set_ylim(ylim)

    ax.set_xlabel("Strike Price")
    ax.set_ylabel("Option Price")
    ax.set_title(f"Real-Life Call and Put Option Prices vs. Strike Prices ({ticker}) - Expiration: {chosen_expiration}")
    ax.legend()
    ax.grid(True)

    fig.canvas.draw_idle()


# def get_implied_volatility(price, underlying, strike, time, rate, option_type):

# Initial plot setup
fig, ax = plt.subplots(figsize=(10, 6))  # Needed to add widgets
plot_options(ax, ticker, date, adjust)

# Adjust whitespace of the plot
fig.subplots_adjust(top=0.925, left=0.09, bottom=0.1375, right=0.95)


# Add a ticker input box below the plot
axbox = fig.add_axes([0.15, 0.02, 0.1, 0.05])  # Position of input box

def submit(text):
    global ticker, date, adjust
    date = 0  # Reset the expiration date
    ticker = text  # Update the ticker symbol
    exp_slider.set_val(date)  # Reset the slider value
    adjust = True  # x- and y-axis need to be adjusted for new ticker

    # Reset expiration dates and slider range
    exp_slider.valmax = len(yf.Ticker(ticker).options) - 1  # Update slider max based on new expiration count
    exp_slider.ax.set_xlim(exp_slider.valmin, exp_slider.valmax)  # Update slider limits

text_box = TextBox(axbox, 'Stock Ticker ', initial=ticker)
text_box.on_submit(submit)


# Add an expiration date slider
axexp = fig.add_axes([0.4, 0.03, 0.4, 0.03])  # Position of slider

def adjust_date(val):
    global date, adjust
    date = val  # Update the expiration date
    adjust = False  # x- and y-axis don't need to be adjusted, same ticker

exp_slider = Slider(
    ax=axexp,
    label='Expiration Date ',
    valmin=0,
    valmax=len(expirations) - 1,  # Set the max number of expiration dates based off stock
    valinit=date,
    valstep=1
)

exp_slider.on_changed(adjust_date)


# Add an "Update" button
ax_button = fig.add_axes([0.85, 0.035, 0.1, 0.05])  # Position of button
update_button = Button(ax_button, 'Update')

# Label for users to press Enter to Update
ax_label = fig.add_axes([0.85, 0.02, 0.1, 0.02])  # Position of text
ax_label.axis("off")
ax_label.text(0.5, 0, "Press Enter to Update", ha="center", va="center", fontsize=7, color="gray")

def update_plot(event):
    plot_options(ax, ticker, date, adjust)


# Bind the Enter key to trigger the update function
def on_enter_press(event):
    if event.key == 'enter':
        update_plot(event)

# Connect the Enter key event to the figure
fig.canvas.mpl_connect('key_press_event', on_enter_press)

update_button.on_clicked(update_plot)



plt.show()