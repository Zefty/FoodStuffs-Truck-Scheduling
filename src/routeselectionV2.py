####################################################################################
#
# Import modules
#
####################################################################################
import numpy as np
import random
import pandas as pd
from pulp import *

def RouteSelectionV2(routeData, nodes):
    """
    Select the best routes to minimise the cost of transporting pallets to supermarket 

    Inputs:
    -------
    routeData : pd.DataFrame
        dataframe containing the all the routes and their corresponding cost 

        Example: 
                        Route                                           Cost 
        0   ['Warehouse', 'Four Square ...']                           1.375
        1   ['Warehouse', 'Four Square ...']                           1.338

    node : list
        a list of all the nodes in the network 

    Outputs:
    -------
    routeDataLP: pd.DataFrame
        Returns solution of LP and whether route is selected 

        Example: 
                        Route                                           State 
        0   ['Warehouse', 'Four Square ...']                                1
        1   ['Warehouse', 'Four Square ...']                                0

    obj  : 
        Cost of objective function 
    """
    # Convert to dollar amount
    costFS = (routeData['Cost']*(150/3600)).tolist()
    costMF = (routeData['Cost']*0+1200).tolist()
    costDollars = costFS + costMF

    frame = [routeData, routeData]
    routeDataDupli = pd.concat(frame, ignore_index = True)
    routeDataDupli['CostDolllars'] = costDollars
    routeIdx = list(routeDataDupli.index) 

    prob = LpProblem("RouteSelection", LpMinimize)

    # Create binary variables
    routeVars = LpVariable.dicts("route", routeIdx, 0, cat = "Binary")

    # Objective function: minimise the cost of traversing routes 
    prob.setObjective(LpAffineExpression([(routeVars[i], costDollars[i]) for i in routeIdx]))
    # prob += lpSum([cost[i] * routeVars[i] for i in routeIdx]), "Total Cost of Traversing Routes"

    # Constraints: 
    # Form constraint for each node i.e. sum of all routes passing through node = 1
    for node in nodes:
        prob += lpSum([routeVars[i] for i in routeIdx if (node in routeDataDupli.iloc[i]['Route'])]) == 1, node
        # prob += lpSum([1 * routeVars[i] if node in routeData['Route'][i] else 0 * routeVars[i] for i in routeIdx]) == 1, node

    # Form constraint for total number of trucks 
    prob += lpSum([1 * routeVars[i] for i in list(routeData.index)]) <= 20, "Total Number of Trucks"

    # The problem data is written to an .lp file
    prob.writeLP("RouteSelection.lp")

    # The problem is solved using PuLP's choice of Solver
    prob.solve()

    # The status of the solution is printed to the screen
    print("Status:", LpStatus[prob.status])

    # Each of the variables is printed with it's resolved optimum value
    routeLpVars = []
    routeLpVarsValue = []
    for v in prob.variables():
        routeLpVars.append(v.name)
        routeLpVarsValue.append(v.varValue)

    # Sort puLP variables and their corresponding values into order 
    idx = sorted(range(len(routeLpVars)), key = lambda k: int(routeLpVars[k].split('_')[1]))
    routeLpVarsSorted = [routeLpVars[i] for i in idx]
    routeLpVarsValueSorted = [routeLpVarsValue[i] for i in idx]

    # The optimised objective function value is printed to the screen
    obj = value(prob.objective)
    print("Total Cost of Traversing Routes =", obj)

    # Put solution into a data frame 

    # Old way without Cost 
    # route = pd.Series(routeData['Route'].tolist(), index = routeLpVarsSorted)
    # state = pd.Series(routeLpVarsValueSorted, index = routeLpVarsSorted)
    # routeDataLP = pd.DataFrame({'Route': route, 'State': state})

    routeDataDupli.index = routeLpVarsSorted
    routeDataDupli['State'] = routeLpVarsValueSorted
    
    # Return the solution + objective function
    return routeDataDupli, obj