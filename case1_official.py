import pandas as pd
import pulp
import yfinance as yf
import numpy as np

def get_stock_data(stock_list, start_date, end_date):

    combined = pd.DataFrame()
    for country in stock_list:
        data = yf.download(stock_list[country], start=start_date, end=end_date, interval='1d', group_by='ticker')
        #data = data.dropna()
        #remove all columns in the multiindex besides open and close
        data = data.loc[:, (slice(None), ['Open', 'Adj Close'])]
        # Create a new MultiIndex with country as the first level
        data.columns = pd.MultiIndex.from_tuples([(country, stock, metric) for stock, metric in data.columns], 
                                        names=['Country', 'Stock', 'Metric'])
        #calculate expected returns for each stock per day
        for stock in data.columns.get_level_values('Stock').unique():
            open_price = data[country, stock, 'Open']
            close_price = data[country, stock, 'Adj Close']
            expected_return = (close_price - open_price) / open_price
            data[(country, stock, 'ExpReturn')] = expected_return
        data = data.loc[:, data.columns.get_level_values('Metric') == 'ExpReturn']
        data = data.iloc[:-1]
        if combined.empty:
            combined = data
        else:
            combined = pd.concat([combined, data], axis=1)
    return combined

def get_weights(stock_data):
    assets = stock_data.columns.get_level_values('Stock').unique().to_list()
    weights = pd.DataFrame(columns=assets)
    all_returns = pd.DataFrame(columns=assets)
    data_length = len(stock_data)
    last_long = {}
    last_short = {}

    for i in range(len(stock_data)):
        if i == 0:
            if data_length >= 7:
                cur_row = stock_data.iloc[0:7]
            else: 
                cur_row = stock_data
            returns_dict = {asset:[] for asset in assets}
            for col in cur_row.columns:
                for item in cur_row[col]:
                    returns_dict[col[1]].append(item)
        else:
            cur_row = stock_data.iloc[[i], :]
            returns_dict = {}
            for col in cur_row.columns:
                for item in cur_row[col]:
                    if np.isnan(item):
                        returns_dict[col[1]] = 0
                    else:
                        returns_dict[col[1]] = item
        

        
        # Define the Problem
        lp = pulp.LpProblem("Portfolio_Optimization", pulp.LpMaximize)
        # Variables
        wL = pulp.LpVariable.dicts(
            "Weights_Long", assets, lowBound=0, upBound=1, cat="Continuous"
        )
        wS = pulp.LpVariable.dicts(
            "Weights_Short", assets, lowBound=0, upBound=1, cat="Continuous"
        )
        if i > 0:
            t = pulp.LpVariable.dicts(
                "Turnover", assets, lowBound=0, upBound=0.25, cat="Continuous"
            )
        
        delta = pulp.LpVariable.dicts("delta", assets, cat="Binary")
        # objective
        if i == 0:
            lp.setObjective(sum(np.nansum(returns_dict[asset]) * (wL[asset] - wS[asset]) for asset in assets))
        else:
            lp.setObjective(sum(returns_dict[asset] * (wL[asset] - wS[asset]) for asset in assets))

        # Linearize the min/max constraints
        for asset in assets:
            lp.addConstraint(wL[asset] <= delta[asset])
            lp.addConstraint(wS[asset] <= 1-delta[asset])

            if i > 0:
                w0 = last_long[asset] - last_short[asset]
                lp.addConstraint(t[asset] >= (wL[asset] - wS[asset] - w0))
                lp.addConstraint(t[asset] >= -(wL[asset] - wS[asset] - w0))

        # positive weights equal 0.5, i.e. sum(zMax[asset]) == 0.5
        lp.addConstraint(sum(wL[asset] for asset in assets) == 0.5)
        lp.addConstraint(sum(wS[asset] for asset in assets) == 0.5)
        if i > 0:
            lp.addConstraint(sum(t[asset] for asset in assets) <= 0.25)

        # solve the model
        #solver = pulp.getSolver('PULP_CBC_CMD', threads=8, msg=False)
        lp.solve()

        # Check the status of the solution
        if pulp.LpStatus[lp.status] == "Optimal":
            # Get and print the optimal portfolio weights
            long = {asset: wL[asset].varValue for asset in assets}
            short = {asset: wS[asset].varValue for asset in assets}
            last_long = long
            last_short = short
            #print(long)
            #print(short)
            combined_weights = {asset:(long[asset] - short[asset]) for asset in assets}
            index = cur_row.index[0].date()

            print(returns_dict)
            print("\n\n\n")
            print(combined_weights)
            
            cur_returns = pd.DataFrame(returns_dict, index=[index])
            cur_weights = pd.DataFrame(combined_weights, index=[index])
            weights = pd.concat([weights, cur_weights])
            all_returns = pd.concat([all_returns, cur_returns])
        else:
            print(f"Status: {pulp.LpStatus[lp.status]}")
        
    return weights, all_returns

def main():
    portfolio = {   'BRA': ['PBR','VALE','ITUB','NU','BSBR'],
                'MEX': ['AMX','KCDMY','VLRS','ALFAA.MX','BBAJIOO.MX'],
                'IND': ['RELIANCE.NS','TCS', 'HDB', 'INFY', 'ADANIENT.NS'],
                'USA': ['AAPL', 'MSFT','GOOG','AMZN','NVDA']
                }
    start = '2021-12-10'
    end = '2021-12-30'
    combined = get_stock_data(portfolio, start, end)

    weights, all_returns = get_weights(combined)

    print(weights['GOOG'][0])
    print(weights.head(10))




main()

