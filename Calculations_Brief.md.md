
## Calculations and Option Selection for 2023-01-20

### 1. Strategy Level
For the date 2023-01-20, the initial strategy level recorded is 99.9842202770424.

### 2. Call and Put Positions
Call Position:
- Delta: 0.5218815120233881
- Units: -0.0009895602216882895
- Strike: 3900
- Price at t: 218.94
- Price at t-1: 218.94

Put Position:
- Delta: -0.4781184879766119
- Units: -0.0009895602216882895
- Strike: 3900
- Price at t: 146.33
- Price at t-1: 146.33

### 3. Underlying Delta
The delta contribution from the underlying asset is -4.330614777747776e-05.

### 4. Calculations

#### a. Option Contributions
**Call Option Contribution**:  
Units * (Price at t - Price at t-1)  
= -0.0009895602216882895 * (218.94 - 218.94)  
= -0.000000

**Put Option Contribution**:  
Units * (Price at t - Price at t-1)  
= -0.0009895602216882895 * (146.33 - 146.33)  
= -0.000000

**Total Option Contribution**:  
Call Contribution + Put Contribution  
= -0.000000 + -0.000000  
= -0.000000

#### b. Delta Contribution
**Total Delta Contribution**:  
(Call Delta * Call Units) + (Put Delta * Put Units) + Underlying Delta Contribution  
= (0.5218815120233881 * -0.0009895602216882895) + (-0.4781184879766119 * -0.0009895602216882895) + -4.330614777747776e-05  
= -0.000087

#### c. Updated Strategy Level
**New Strategy Level**:  
Previous Strategy Level + Option Contribution + Delta Contribution  
= 99.9842202770424 + -0.000000 + -0.000087  
= 99.984134

### 5. Flow of Code
The code flow is as below
- First we call the back the  backtest_strategy method against our dataset.
- We convert the output that we get from the backtest_strategy into two csv files which are strategy levels and Portfolio decomposition. Merged the two files into the a single data set and displayed the results in the App