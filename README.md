# CTC23

- Code for the first case of the cornell trading competition
- Uses a linear solver (PuLP) in order to maximize weights for an equity market neutral portfolio 
- Establishes linear constraints to ensure weights for any given day sum to 0, long positions = short positions, and turnover is less than 25%
- Succesfully delivers consistently high ROI's when run on a backtester for a portfolio of stocks over a given timeframe
- Placed top 5 in the competition
  
![main solution](https://github.com/Shrey-Varma/CTC23/blob/main/sol1.png?raw=true)
![turnover constraint](https://github.com/Shrey-Varma/CTC23/blob/main/sol2.png?raw=true)
