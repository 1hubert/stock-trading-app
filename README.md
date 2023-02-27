# Simple Finance App
A simple stock trading app built in Python with Flask as part of the CS50 course. The money is fictional, but the available stocks and current stock prices are fetched from IEX Exchange using the IEX Cloud Legacy API.

# Features
- Register an account to get a 10,000$ of fictional money to trade
- Buy and sell selected stocks at real-time prices
- Portfolio view
- Trading history

# Motivation
I've wanted to learn basics of back-end development and Flask seemed like a good start.

# Configuration (Windows)
1) Install dependencies with `pip install -r requirements.txt`.
2) Make an account on [IEX Cloud](https://iexcloud.io) to get an API key ([API docs](https://iexcloud.io/docs/api)).
3) Set API_KEY as an environmental variable for the same directory in which the app is located using `set API_KEY=X` where X is your API key without quotes.
3) Use `flask run` in the main directory to start the app!
