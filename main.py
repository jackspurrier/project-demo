# This is a sample Python script.
import datetime
from IPython.display import HTML
import pandas as pd
import json
import requests
import math
import streamlit as st
import plotly.express as pexp
import plotly.graph_objects as go
import csv
from empyrial import empyrial, Engine, get_report, get_returns_from_data,get_returns
import numpy as np
import quantstats as qs





#api_key = "3ZGSDZGITRAO2JWA"

data_stock = []
meta_info_stock = []
df_stock = []
daily_std_stock = []
daily_volatility_stock = []
monthly_volatility_stock = []



def get_daily_stock(stock_sym,api_key):
    url = 'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=' + stock_sym + '&apikey=' + api_key
    r = requests.get(url)
    if r.status_code == 200:
        data = r.json()
        print(data)
        return data
    else:
        st.error("Cannot find daily stock values for !" + stock_sym  )

def get_normalized_json(data):

    stock_dates = data['Time Series (Daily)'].keys()
    stock_open = []
    stock_close = []
    stock_high = []
    stock_low = []

    for dt in stock_dates:
        stock_open.append(data['Time Series (Daily)'][dt]['1. open'])
        stock_close.append(data['Time Series (Daily)'][dt]['4. close'])
        stock_high.append(data['Time Series (Daily)'][dt]['2. high'])
        stock_low.append(data['Time Series (Daily)'][dt]['3. low'])

    df = pd.json_normalize(data, max_level=2)
    df = pd.DataFrame(
        {'Date': stock_dates, 'stock_open': stock_open, 'stock_close': stock_close, 'stock_high': stock_high,
         'stock_low': stock_low})
    df.index = df['Date']
    stock_close_data = df['stock_close'].astype(float)
    stock_open_data = df['stock_open'].astype(float)
    df['returns'] = (stock_close_data - stock_open_data) / stock_open_data * 100
    df['30_EWM'] = df['returns'].ewm(span=30, adjust=False).mean()
    return df

def gfn(stock_sym):
    url='https://www.alphavantage.co/query?function=INCOME_STATEMENT&symbol=' + stock_sym + '&apikey=DLC0NSMS2P7WIW1J'
    r = requests.get(url)
    data = r.json()
    print(data)
    return data

def get_ticker_symbol_list():
    match_symbols = []
    with open('nasdaq-listed-symbols_csv.csv', newline='') as csvfile:
        symbol_data = csv.DictReader(csvfile)
        for symbol in symbol_data:
            match_symbols.append(symbol['Symbol'])
    return  match_symbols


    return match_symbols

def get_currency_symbol_list():
    currency_symbols=[] 
    with open('currency_listings.csv', newline='') as csvfile:
        symbol_data = csv.DictReader(csvfile)
        for symbol in symbol_data:
            currency_symbols.append(symbol['AlphabeticCode'])
    return currency_symbols

def get_volatility(tickers):
    i=0

    for ticker in tickers:
        data_stock.append(get_daily_stock(ticker, '3ZGSDZGITRAO2JWA'))
        meta_info_stock.append(list(data_stock[i].values())[0])

        df_stock.append(get_normalized_json(data_stock[i]))
        daily_volatility_stock.append(df_stock[i]['returns'].std())
        monthly_volatility_stock.append(daily_volatility_stock[i] * math.sqrt(21))
        i+=1
    return  data_stock, meta_info_stock ,df_stock , daily_volatility_stock ,monthly_volatility_stock

def get_exchanged_value(num,from_currency,to_currency):
    url = 'https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&from_currency=' + str(from_currency) + '&to_currency=' + str(to_currency) + '&apikey=' + 'DLC0NSMS2P7WIW1J'
    r = requests.get(url)
    data = r.json()

    if r.status_code == 200:
        exchanged_val = float(num) * float(data['Realtime Currency Exchange Rate']['5. Exchange Rate'])
    return  data, exchanged_val

def getportfolio(tickers,start_dt,to_diversify):

    if to_diversify == 'do not diversify' :

        tickers_portfolio = Engine(start_date=start_dt, portfolio=tickers, weights=[0.3, 0.3, 0.3],benchmark=["SPY"],rebalance='1y')
        empyrial(tickers_portfolio)
        st.subheader(tickers_portfolio.weights)

    elif to_diversify == 'medium diversify':
        tickers_portfolio = Engine(start_date=start_dt, portfolio=tickers, benchmark=["SPY"],optimizer="MINVAR",diversification=1.3)
        empyrial(tickers_portfolio)

    elif to_diversify == 'optimize':
        tickers_portfolio = Engine(start_date=start_dt, portfolio=tickers, benchmark=["SPY"],optimizer="EF")
        empyrial(tickers_portfolio)
    else :
        tickers_portfolio = Engine(start_date=start_dt, portfolio=tickers, benchmark=["SPY"], rebalance='1y', risk_manager = {"Max Dropdown : -0.25"})
        empyrial(tickers_portfolio)


    df_new = pd.DataFrame.from_dict(empyrial.df)

    print(type(tickers_portfolio))

    return  df_new


# Press the green button in the gutter to run the script.
if __name__ == '__main__':

    st.title('Portfolio Management Dashboard')

    ###################################PORTFOLIO ANALYSIS OF 3 TICKERS ENTERED###############################################
    st.subheader('Portfolio Analysis')

    st.sidebar.subheader("Select Tickers")
    ticker1 = st.sidebar.selectbox('Ticker1',get_ticker_symbol_list())
    ticker2 = st.sidebar.selectbox('Ticker2',get_ticker_symbol_list())
    st.sidebar.warning('Please select a different from ticker 1')
    ticker3 = st.sidebar.selectbox('Ticker3',get_ticker_symbol_list())
    st.sidebar.warning('Please select a different from ticker 1 and ticker 2')
    clicked = st.sidebar.button("Submit")

    tickers = [ticker1, ticker2, ticker3]

    st.subheader('Showing portfolio analysis for :'.format(str(ticker1), str(ticker2), str(ticker3)))
    diversify_cols = st.columns(1)
    diversify = diversify_cols[0].radio("Make slection for diversification : ",('do not diversify', 'medium diversify','optimize','manage risk'))
    start_dt = st.date_input("Enter Date :", datetime.datetime(2018,3,18))
    str_start_date= start_dt.strftime("%Y-%m-%d")
    print(str_start_date)
    #end_dt = st.date_input("Enter Date :", datetime.date(2022, 3, 18))

    #st.subheader("Rebalancing Yearly")

    if diversify and ticker1 != 'AAIT' and ticker2 != 'AAIT' and ticker3  != 'AAIT' :

        df_new= getportfolio(tickers,str_start_date,diversify)
        #returns = get_returns(portfolio.portfolio,portfolio.weights,portfolio.start_date,portfolio.end_date)

        #print(df_new)
        #df_new=getportfolio(tickers,str_start_date,diversify)
        st.dataframe(df_new.astype(str))
        #qs.plots.monthly_heatmap()
        #clicked = st.sidebar.button("Download Report", on_click=get_report(portfolio))
        #get_returns(portfolio.portfolio,portfolio.weights, portfolio.start_date,portfolio.end_date)


    if clicked and  ticker1 != 'AAIT' and ticker2 != 'AAIT' and ticker3  != 'AAIT':
        if ticker1   !=  'Ticker1' and   ticker2   !=  'Ticker2' and ticker3   !=  'Ticker3':

            if (ticker1 != ticker2 or ticker1 != ticker3 or ticker2 != ticker3):


                ###################################VOLATILITY DETAILS###############################################


                data_stock, meta_info_stock ,df_stock , daily_volatility_stock ,monthly_volatility_stock = get_volatility(tickers)
                



                ###################################VOLATALITY BASED ON FREQUENCY : DAILY/MONTHLY###############################################
                select_freq = st.sidebar.radio("Select Volatility Frequency",('Daily','Monthly'))

                ###################################VOLATALITY PLOTS BASED ON FREQUENCY : DAILY/MONTHLY###############################################

                cols = st.columns(3)
                sign=''
                for i in range(3):

                    st.subheader('Volatility plot for '+ meta_info_stock[i]['2. Symbol'])

                    if(select_freq == 'Daily'):

                       volatility_freq = daily_volatility_stock[i]
                       if daily_volatility_stock[i] > df_stock[i]['returns'].mean():
                          sign = 'increasing'
                       elif daily_volatility_stock[i] < df_stock[i]['returns'].mean():
                          sign = 'decreasing'

                    else:
                        volatility_freq = monthly_volatility_stock[i]
                    if monthly_volatility_stock[i] > df_stock[i]['returns'].mean()* math.sqrt(21):
                         sign = 'increasing'
                    elif monthly_volatility_stock[i] < df_stock[i]['returns'].mean()* math.sqrt(21):
                         sign = 'decreasing'


                    fig =  go.Figure(go.Indicator(mode = "gauge+number+delta",value = volatility_freq,domain = {'x': [0,0.25] ,'y': [0,0.25]},
                    title = {'text' : select_freq + " Volatility for " + meta_info_stock[i]['2. Symbol'] },
                            delta = {'reference': df_stock[i]['returns'].mean(),sign : {'color':"purple"}},
                    gauge = { 'bar' : {'color' : "skyblue"} }))
                    cols[i].plotly_chart(fig)

                    ###################################VOLATALITY MEASURED AS EXPONENTIAL MOVING AVERAGE###############################################

                    Stock_movements= [df_stock[i]['returns'], df_stock[i]['30_EWM']]
                    pf_graph = pexp.line(df_stock[i], x=df_stock[i]['Date'],y=Stock_movements, labels={'30-Day-EWM'})
                    st.plotly_chart(pf_graph)

            else:

                st.sidebar.error('Please elect 3 unique ticker values for the portfolio analysis')


    st.sidebar.subheader('Calculate Exchange : ')
    num = st.sidebar.number_input('Enter value for currency exchange : ')
    from_currency = st.sidebar.selectbox('Select from currency : ',get_currency_symbol_list() )
    to_currency = st.sidebar.selectbox('Select to currency : ', get_currency_symbol_list())

    clicked = st.sidebar.button("Convert")

    if clicked:

        if   from_currency  !=   to_currency :
            data1, exchanged_val = get_exchanged_value(num, from_currency, to_currency)

            st.sidebar.write(data1["Realtime Currency Exchange Rate"]["3. To_Currency Code"])
            st.sidebar.write(data1["Realtime Currency Exchange Rate"]["5. Exchange Rate"])
            st.sidebar.subheader('Calculated currency of ' + str(num) + ' ' + from_currency + ' to ' + to_currency + ' is : ' + str(round(exchanged_val, 2)))

        else:
            st.sidebar.error('Enter different currency values for  from_currency and to_currency')