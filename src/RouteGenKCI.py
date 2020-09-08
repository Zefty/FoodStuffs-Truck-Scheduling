####################################################################################
#
# Import modules
#
####################################################################################
import numpy as np
import pandas as pd
from pulp import *
import random
from scipy.cluster.vq import kmeans2, whiten
from sklearn.cluster import DBSCAN
from os import sep
import matplotlib.pyplot as plt

def KRegionalClusters(locationData, k=10, plot=False):
    '''
    Separate supermarkets into k clusters such that route generation for each cluster/region is possible

    Inputs
    ------
    k : integer
    Number of clusters/regions. Default for k clusters is 10.

    plot : boolean
    True if we want to plot the data

    Returns
    -------

    l : np.array
    Contains the cluster/region that the corresponding supermarket belongs to
    '''
    # Load the location data of each store

    # locationData = locationData[1:][:]

    # Extract out only the longitude and latitude values for each supermarket (retains order)
    coord = locationData[["Long", "Lat"]].values

    # Plot the supermarkets
    x = [x[0] for x in coord]
    y = [y[1] for y in coord]
    f1 = plt.figure()
    f1 = plt.scatter(x, y)

    # Use k means algorithm to form regions/clusters
    c, l = kmeans2(whiten(coord), k, iter = 50)

    # Plot the supermarkets based on its region
    f2 = plt.figure()
    f2 = plt.scatter(x, y, c=l)
    if plot:
        plt.show()

    return l

def CreateRegionsFromKMeans(locationData, l):
    """
    Creates list of lists of stores for K means regions

    Inputs
    ------
    locationData

    l
    array of region numbers from k means
    """
    # locationData = locationData[1:][:]
    regions = []
    for region in set(l):
        CurrentRegion = locationData[l==region]["Supermarket"].values.tolist()
        regions.append(CurrentRegion)
    return regions

def CheapestInsertion(nodes, weights, centralNode = None):
    '''
    Cheapest insertion heuristics to compute the most optimal tour for a given set of nodes 

    Inputs
    ------
    nodes : np.array/list 
    Current nodes to find optimal tour  

    weights : pd.dataframe
    Distance, time, or any unit of measurement between nodes 

    centralNode : String  
    Central distribution node is the starting/ending node of the tour  

    Returns
    -------
    finalTour : list
        list of strings representing a tour of supermarkets
    finalTourWeight : float
        number representing the weight of the final tour
    '''
    
    # Cheapest insertion can still function even if we randomly assign a central node 
    if centralNode == None:
        centralNode = random.choice(nodes)

    finalTourWeight = 0 
    # Start with one node in solution 
    finalTour = [centralNode]

    # Initialise algorithm 
    finalTour.append(weights[centralNode][nodes].idxmin())
    finalTourWeight += weights[centralNode][nodes].min()

    # While each node/sm not in final tour 
    while len(finalTour) <= len(nodes):
        
        # On each iteration, reset the optimal route for adding new node/sm to final tour 
        optimalTourWeight = float('inf')
        optimalNodeToInsert = None
        positionToInsert = None

        # Loop through each node/sm to find nearest neighbour and add to tour 
        for sm in nodes:
            
            # Check if node/sm already added to tour 
            if sm in finalTour:
                # Skip current iteration if node/sm already added to tour
                continue 

            # Otherwise determine weight/cost of insertion 
            for i in range(len(finalTour)-1):
                currentTourWeight = finalTourWeight + weights[finalTour[i]][sm] + weights[sm][finalTour[i+1]] - weights[finalTour[i]][finalTour[i+1]]
                if currentTourWeight < optimalTourWeight:
                    optimalTourWeight = currentTourWeight
                    optimalNodeToInsert = sm
                    positionToInsert = i+1

        # Update final tour after cheapest insertion of all nodes 
        finalTour.insert(positionToInsert, optimalNodeToInsert)
        finalTourWeight = optimalTourWeight

    # Complete node by adding back central node 
    finalTourWeight += weights[centralNode][finalTour[-1]]
    finalTour.append(centralNode)

    return finalTour, finalTourWeight

def RouteConstruction(locationData, weights, l, demandPreds, weekday):
    '''
    Construct routes per region by creating supermarket node sets that satisfy the
    requirments and constraints

    Inputs
    ------
    locationData : pandas dataframe
    Basically dataframe of excel data

    weights : pd.dataframe
    Distance, time, or any unit of measurement between nodes

    l : np.array
    Contains the cluster/region that the corresponding supermarket belongs to 

    demandPreds : pandas dataframe
    Dataframe of demand estimates for costs

    weekday : string 
    The day of the week to generate routes for 

    Returns:
    -------
    routeData : pd.DataFrame
        dataframe containing the all the routes and their corresponding cost 

        Example: 
                        Route                                           Cost 
        0   ['Warehouse', 'Four Square ...']                            3000
        1   ['Warehouse', 'Four Square ...']                            4000

    Notes:
    ------
    This method will work by repeatedly ban the optimal solution and resolve for more optimal routes. 
    '''
    # Get supermarket regions
    # locationData, l = KRegionalClusters(k=3, plot=True)
    # locationData = locationData[1:][:]
    
    routes = []
    costs = []
    # Loop through each region, identify possible locations, construct a set of feasible routes
    for region in set(l):
        
        # Get supermarkets in current region and store in numpy array
        smCurrentRegion = locationData[l==region]["Supermarket"]

        # Construct supermarket data: demand and cost

        # Helper function returns the value of demand for current store and weekday
        def GetDemand(store):
            store_type = locationData.loc[locationData["Supermarket"] == store, ["Type"]].values[0][0]
            demandcol = demandPreds.loc[demandPreds["Supermarket Type"] == store_type]
            return demandcol.loc[demandcol["Weekday"] == weekday, ["Demand"]].values[0]

        Demand = []

        for store in smCurrentRegion:
            Demand.append(GetDemand(store))

        Demand = pd.Series(Demand, index = smCurrentRegion)

        Cost = pd.Series([1]*len(smCurrentRegion), index = smCurrentRegion)

        # Form integer binary LP to figure out a supermarket "node" set that
        # satisfies the demand constraint. Will be used for constructing
        # routes (and its cost)
        prob = LpProblem("RouteContructionRegion" + str(region), LpMaximize)

        # Create binary variables
        smVars = LpVariable.dicts("sm", smCurrentRegion, 0, cat = "Binary")

        # Maximise the total number of supermarket in the route
        prob += lpSum([Cost[i] * smVars[i] for i in smCurrentRegion]), "Total Supermarkets in Route"

        # Ensure route capacity is met
        prob += lpSum([Demand[i] * smVars[i] for i in smCurrentRegion]) <= 12, "MaxTruckCapacity"

        # The problem data is written to an .lp file
        prob.writeLP("RouteContructionRegion" + str(region) + ".lp")

        # The problem is solved using PuLP's choice of Solver to get 50 different optimal solutions
        for i in range(50):
            prob.solve()

            if LpStatus[prob.status] == "Optimal": 
                # Determine the cardinality of the set of decision variables  
                p = 0
                for v in prob.variables():
                    if v.varValue == 1: 
                        p = p + 1 

                # For current set of nodes, find the heuristic solution to the most optimal path 
                # Using cheapest insertion 
                nodes = [i for i in smCurrentRegion if smVars[i].varValue == 1]
                finalTour, finalTourWeight = CheapestInsertion(nodes, weights, centralNode = 'Warehouse')
                # Add time it takes to unload per supermarket
                finalTourWeight += 300*(len(finalTour)-2)

                # If the route takes less than four hours to traverse then append to list of optimal solutions 
                if finalTourWeight < 14400:
                    routes.append(finalTour)
                    costs.append(finalTourWeight)

                # The constraint is added that the same solution cannot be returned again
                prob += lpSum([1 * smVars[i] if smVars[i].varValue == 1 else 0 * smVars[i] for i in smCurrentRegion]) <= p - 1
            # If a new optimal solution cannot be found, we end the program
            else:
                break

    # Put routes and costs into a dataframe 
    routesdf = pd.Series(routes)
    costsdf = pd.Series(costs)
    routeData = pd.DataFrame({'Route': routesdf, 'Cost': costsdf})

    return routeData, list(locationData["Supermarket"])


def RouteConstruction2(locationData, weights, l, demandPreds, weekday, min):
    '''
    Construct routes per region by creating supermarket node sets that satisfy the
    requirments and constraints

    Inputs
    ------
    locationData : pandas dataframe
    Basically dataframe of excel data

    weights : pd.dataframe
    Distance, time, or any unit of measurement between nodes

    l : np.array
    Contains the cluster/region that the corresponding supermarket belongs to 

    demandPreds : pandas dataframe
    Dataframe of demand estimates for costs

    weekday : string 
    The day of the week to generate routes for 

    Returns:
    -------
    routeData : pd.DataFrame
        dataframe containing the all the routes and their corresponding cost 

        Example: 
                        Route                                           Cost 
        0   ['Warehouse', 'Four Square ...']                            3000
        1   ['Warehouse', 'Four Square ...']                            4000

    Notes:
    ------
    This method will work by repeatedly ban the optimal solution and resolve for more optimal routes. 
    '''
    # Get supermarket regions
    # locationData, l = KRegionalClusters(k=3, plot=True)
    # locationData = locationData[1:][:]
    
    routes = []
    costs = []
    # Loop through each region, identify possible locations, construct a set of feasible routes
    for region in set(l):
        
        # Get supermarkets in current region and store in numpy array
        smCurrentRegion = locationData[l==region]["Supermarket"]

        # Construct supermarket data: demand and cost

        # Helper function returns the value of demand for current store and weekday
        def GetDemand(store):
            store_type = locationData.loc[locationData["Supermarket"] == store, ["Type"]].values[0][0]
            demandcol = demandPreds.loc[demandPreds["Supermarket Type"] == store_type]
            return demandcol.loc[demandcol["Weekday"] == weekday, ["Demand"]].values[0]

        Demand = []

        for store in smCurrentRegion:
            Demand.append(GetDemand(store))

        # Generate demand data required for the supermarkets in the current region 
        Demand = pd.Series(Demand, index = smCurrentRegion)

        Cost = pd.Series([1]*len(smCurrentRegion), index = smCurrentRegion)

        # Form integer binary LP to figure out a supermarket "node" set that
        # satisfies the demand constraint. Will be used for constructing
        # routes (and its cost)
        prob = LpProblem("RouteContructionRegion" + str(region), LpMinimize)

        # Create binary variables
        smVars = LpVariable.dicts("sm", smCurrentRegion, 0, cat = "Binary")

        # Maximise the total number of supermarket in the route
        prob += lpSum([Cost[i] * smVars[i] for i in smCurrentRegion]), "Total Supermarkets in Route"

        # Ensure route capacity is met
        prob += lpSum([Demand[i] * smVars[i] for i in smCurrentRegion]) <= 12, "MaxTruckCapacity"
        prob += lpSum([Demand[i] * smVars[i] for i in smCurrentRegion]) >= min, "MinTruckCapacity"

        # The problem data is written to an .lp file
        prob.writeLP("RouteContructionRegion" + str(region) + ".lp")

        # The problem is solved using PuLP's choice of Solver to generate 50 different optimal solutions
        for i in range(50):
            prob.solve()

            if LpStatus[prob.status] == "Optimal": 
                # Determine the cardinality of the decision variables 
                p = 0
                for v in prob.variables():
                    if v.varValue == 1: 
                        p = p + 1 

                # For current set of nodes, find the heuristic solution to the most optimal path 
                # Using cheapest insertion 
                nodes = [i for i in smCurrentRegion if smVars[i].varValue == 1]
                finalTour, finalTourWeight = CheapestInsertion(nodes, weights, centralNode = 'Warehouse')
                # Add time it takes to unload per supermarket 
                finalTourWeight += 300*(len(finalTour)-2)
                
                # If the route takes less than four hours to traverse then append to list of optimal solutions 
                if finalTourWeight < 14400:
                    routes.append(finalTour)
                    costs.append(finalTourWeight)

                # The constraint is added that the same solution cannot be returned again
                prob += lpSum([1 * smVars[i] if smVars[i].varValue == 1 else 0 * smVars[i] for i in smCurrentRegion]) <= p - 1
            
            # If a new optimal solution cannot be found, we end the program
            else:
                break
    
    # Put routes and costs into a dataframe 
    routesdf = pd.Series(routes)
    costsdf = pd.Series(costs)
    routeData = pd.DataFrame({'Route': routesdf, 'Cost': costsdf})

    return routeData, list(locationData["Supermarket"])