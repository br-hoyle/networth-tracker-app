# 💰 Net Worth Tracker

This Personal Net Worth Tracker is a simple Streamlit web application that helps you track your assets, liabilities, and overall net worth over time. The app provides an intuitive interface for entering your financial data and visualizes your progress with interactive charts.

## Features

- Add, edit, and remove balances to your accounts
- Calculate and display your net worth
- Visualize your financial history with charts
- Data persistence using Google Sheets via GSheetsConnection
- Clean, responsive UI powered by Streamlit

## How It Works

1. **Input your account balances:** Enter values for your banking, investments, debts, and other balances in all your financial accounts.
2. **Automatic calculations:** The app computes your net worth, targets based on income, target retirement age, and savings rates.
3. **Track progress:** View your net worth history and trends with easy-to-read charts.

## Tools & Technologies

- **[Streamlit](https://streamlit.io/):** For building the interactive web app.
- **[GSheetsConnection](https://www.youtube.com/watch?v=HwxrXnYVIlU):** For connecting and persisting data to a Google Sheets database.
- **Pandas:** Data manipulation and cached data.
- **Plotly:** Data visualization.


## Getting Started

1. Install the requirements:

   ```bash
   poetry install
   ```

2. Run the app:

   ```bash
   streamlit run streamlit_app.py
   ```

---

Start tracking your net worth today and gain insights into your financial journey!
