import numpy as np
import pandas as pd 
from RouteGenKCI import *
from routeselectionV1 import *
from routeselectionV2 import *
# from routeselection import *
from RouteGen import *
from ast import literal_eval
from simulation import *
from scipy import stats

def TestCheapestInsertion():
    weights = pd.DataFrame({'O': {'R': 80, 'B': 100, 'W': 120, 'Y': 110},
               'R': {'O': 80, 'Y': 90, 'W': 100, 'B': 90},
               'B': {'R': 90, 'O': 100, 'Y': 100, 'W': 110},
               'W': {'Y': 150, 'O': 120, 'R': 100, 'B': 110},
               'Y': {'O': 110, 'R': 90, 'B': 100, 'W': 150}
              })

    nodes = ['R', 'B', 'W', 'Y']
    finalTour, finalTourWeight = CheapestInsertion(nodes, weights, centralNode = 'O')
    print("Path of optimal tour", finalTour, "\nWeight of Tour:", finalTourWeight)

# TestCheapestInsertion()

def TestRouteGeneration(): 
    # Import data
    locationData = pd.read_csv("Data" + sep + "FoodstuffLocations.csv")
    locationData.loc[locationData["Supermarket"] == "Fresh Collective Alberton", "Type"] = "Four Square"
    locationData = locationData[1:][:]
    timeData = pd.read_csv("Data" + sep + "FoodstuffTravelTimes.csv", index_col = 0)
    demandPreds = pd.read_csv("Data" + sep + "demandModel.csv")

    # Generate k means 
    l = KRegionalClusters(locationData, k=2, plot=False)

    # Construct routes based on k means 
    routeData1, stores = RouteConstruction(locationData, timeData, l, demandPreds, "Monday")
    frame = [routeData1]
    for i in range(1,12):
        routeData2, stores = RouteConstruction2(locationData, timeData, l, demandPreds, "Monday", min = i)
        frame.append(routeData2)
    routeData = pd.concat(frame, ignore_index = True)
    # Save current solution so we do not need to run again 
    routeData.to_csv("Data" + sep + "UnitTest" + sep + "generatedRoutesWeekday.csv", index=False)

# TestRouteGeneration()

def TestRouteSelection():
    Test1 = False
    TestModel = True

    if Test1: 
        # Test Case 1 for RouteSelection
        routes = pd.Series([['1', '4'], ['2', '6'], ['3', '4'], ['1', '5']])
        costs = pd.Series([5, 8, 2, 8])
        routeData = pd.DataFrame({'Route': routes, 'Cost': costs})
        nodes = ['1', '2', '3', '4', '5', '6']

        # Test RouteSelection using example on page13 of notes 
        routeDataLP, obj = RouteSelection(routeData, nodes)
        print(routeDataLP)
        print(obj)

    if TestModel:
        # Set to True if we want to generate a new set of routes for testing 
        # Otherwise load what is currently saved in repo 
        if False:
            TestRouteGeneration()

        # Load data so we DO NOT need to run route gen again 
        # Below tests route selection 
        routeData = pd.read_csv("Data" + sep + "generatedRoutesWeekday.csv", converters = {"Route": literal_eval})
        locationData = pd.read_csv("Data" + sep + "FoodstuffLocations.csv")
        locationData.loc[locationData["Supermarket"] == "Fresh Collective Alberton", "Type"] = "Four Square"
        supermarkets = list(locationData["Supermarket"])
        supermarkets.remove('Warehouse')

        # Select routes 
        routes, obj = RouteSelection(routeData, supermarkets)
        chosenRoutes = routes.loc[routes['State'] == 1]
        chosenRoutes.to_csv("Data" + sep + "chosenRoutesFINAL.csv", index=False)
        print(chosenRoutes)

        # Debug selected routes 
        print("commencing debugging")
        for s in supermarkets:
            included = 0
            i = 0
            while i < len(chosenRoutes) and not included:
                if s in chosenRoutes['Route'][i]:
                    included = 1
                i+=1
            if not included:
                print(f"{s} is not in any routes!")
        print("finished debugging")

# TestRouteSelection()

def TestRunSimulation():
    # Initialise list of optimal solution routes
    weekRoutes = pd.read_csv("Data" + sep + "Routes" + sep + "optimalRoutes" + "Monday" + ".csv", converters = {"Route": literal_eval})
    wkndRoutes = pd.read_csv("Data" + sep + "Routes" + sep + "optimalRoutes" + "Saturday" + ".csv", converters = {"Route": literal_eval})

    # Get cleaned dataframe
    demandData = pd.read_csv("Data" + sep + "demandData.csv")
    locationData = pd.read_csv("Data" + sep + "FoodstuffLocations.csv")
    demandData = clean_data(demandData,locationData)
    locationData.loc[locationData["Supermarket"] == "Fresh Collective Alberton", "Type"] = "Four Square"
    demandData = setupbootstrap(demandData)

    wopt = simulate(weekRoutes, demandData, locationData, wknd=False)
    opt = simulate(wkndRoutes, demandData, locationData, wknd=True)
    # Import travel times between supermarkets + demand predictions per store 


print(stats.norm.rvs(loc=10, scale =2, size =100))

# TestRunSimulation()


# test = ['Warehouse', 'Pak \'n Save Mangere', 'Warehouse']
# print(test)
# print([test[i] for i in range(len(test)) if 'New World Mt Roskill' in test[i]])

# routeData = pd.read_csv("Data" + sep + "generatedRoutesWeekend.csv", converters = {"Route": literal_eval})
# print(routeData)
# print(routeData.max())