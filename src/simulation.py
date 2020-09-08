# Simulation file for route times

####################################################################################
#
# Import modules
#
####################################################################################
import numpy as np
import random
import pandas as pd
from os import sep
from DataAnalysis import *
import time

def generate_distribution_value(minimum, maximum):
    ''' Generates a route time from a set distribution, in order to simulate the time
    variability in the data. Generated according to a normal distribution.

    Inputs:
        min: float
            min value of time taken (hrs)
        max: float
            max value of time taken (hrs)

    Outputs:
        value: float
            time value generated according to a normal distribution
    '''
    tol = maximum - minimum
    choice = random.uniform(0,1)
    return minimum + tol*choice

def generate_time_values(weekend=False):
    ''' Generates one possbile set of times to work with for route generation.

    Inputs:
        weekend: bool
            true/false depending on if we wish to generate times for the weekend.
            assigns max multiplier different times if we wish

    Outputs:
        times: dataframe
            one set of variable times from which to sample from.
    '''
    # Assigning multipliers to different day scenarios
    mn = 1                  # min multiplier is best case scenario - no traffic
    if weekend: ma = 1.5
    else: ma = 2

    # Import travel times between supermarkets
    timeData = pd.read_csv("Data" + sep + "FoodstuffTravelTimes.csv", index_col = 0)

    # Iterating through index for the problem
    indices = timeData.index
    for index1,index2 in zip(indices[::-1],indices[-1::]): # TODO: assess if this is correct iteration approach. runs so it will do for now.
        value = timeData[index1][index2]
        timeData[index1][index2] = generate_distribution_value(mn*value,ma*value)

    return timeData

def setupbootstrap(demandData,wknd=False):
    ''' Initialises lists for bootstrapping
    '''
    # Initialise lists
    fsSamp = []
    pkSamp = []
    nwSamp = []

    if wknd:
        # Iterate through rows for full sample of weekend data, for each store type
        [fsSamp.append(row[1]['Demand']) for row in demandData.iterrows() if row[1]['Type'] == "Four Square" and row[1]['Weekday'] == "Saturday"] 
        [pkSamp.append(row[1]['Demand']) for row in demandData.iterrows() if row[1]['Type'] == "Pak 'n Save" and row[1]['Weekday'] == "Saturday"]
        [nwSamp.append(row[1]['Demand']) for row in demandData.iterrows() if row[1]['Type'] == "New World" and row[1]['Weekday'] == "Saturday"] 
    else:
        # Iterate through rows for full sample of weekday data, for each store type
        [fsSamp.append(row[1]['Demand']) for row in demandData.iterrows() if row[1]['Type'] == "Four Square" and row[1]['Weekday'] != "Saturday"] 
        [pkSamp.append(row[1]['Demand']) for row in demandData.iterrows() if row[1]['Type'] == "Pak 'n Save" and row[1]['Weekday'] != "Saturday"]
        [nwSamp.append(row[1]['Demand']) for row in demandData.iterrows() if row[1]['Type'] == "New World" and row[1]['Weekday'] != "Saturday"] 

    return [fsSamp, pkSamp, nwSamp]

def bootstrap(fsSamp, pkSamp, nwSamp):
    '''
    Returns different demand values input into the linear program; sampling
    with replacement

    Inputs:
    wknd: bool
        if we are sampling demands from weekend or not.
    demandData: dataFrame
        cleaned demand data.

    Outputs:
    demands: dict
       dictionary which has demands corresponding to the three store types.
    demandData: DataFrame
        cleaned data to use for route checking.

    '''
    # start_time = time.time()
    # Setting up dict as output
    demands = {"Four Square": 0,
                "Pak'n Save": 0,
                "New World": 0}
    '''
    fsSamp = []
    pkSamp = []
    nwSamp = []

    if wknd:
        fsSamp = demandData[0]
        pkSamp = demandData[1]
        nwSamp = demandData[5]
    else: 
        fsSamp = demandData[0]
        pkSamp = demandData[1]
        nwSamp = demandData[2]
    '''

    # Now sampling from each row to get a demand value
    demands["Four Square"] = random.choices(fsSamp,k=1)
    demands["Pak 'n Save"] = random.choices(pkSamp,k=1)
    demands["New World"] = random.choices(nwSamp, k=1)

    return demands

def simulate(routes, locationData, fsSamp, pkSamp, nwSamp, wknd=False):
    ''' Extracts data as DataFrame of demands. Then, samples the data for each store chain,
    depending on whether or not it is the weekend. The demands are then simulated along with times
    in order to generate a range of optimal solutions.

    Inputs:
    wknd: Bool
        Whether or not we wish to model weekend demand on Saturday.
    routes: DataFrame
        Containing costs for each route in the optimal solution.

    Outputs:
    opt: float
        optimal solution value for one run of the simulation

    '''

    # First getting our demands from bootstrap distribution
    demands = bootstrap(fsSamp,nwSamp,pkSamp)

    # We now split routes into morning and afternoon to account for different weights
    morning = []
    afternoon = []
    i = 0
    for route in routes.iterrows():
        if i%2 == 0: morning.append(route)
        else: afternoon.append(route)
        i += 1

    opt = 0 # Initialising optimal solution
    demand = 0

    # Now simulating time demand for each time in morning or afternoon:
    if wknd:
        for route in morning:
            time = generate_distribution_value(route[1]['Cost'], 1.25*route[1]['Cost'])/3600 # getting time

            if time > 4: opt += (150*4 + (time-4)*200) # Getting cost of route
            else: opt += 150*time

            # Checking demand with input dict
            #demand = 0
            for store in route[1]['Route'][1:-1]:
                store_type = locationData.loc[locationData["Supermarket"] == store, "Type"].values[0]
                demandtoadd = demands[store_type][0]
                demand += demandtoadd # TODO: refactor by store type in the optimal solution

            #if demand > 12:
            #    opt += 1200*np.ceil(demand%12) # Adding cost of mainfreight if we exceed truck demand

        for route in afternoon:
            time = generate_distribution_value(route[1]['Cost'], 1.4*route[1]['Cost'])/3600 # getting time

            if time > 4: opt += (150*4 + (time-4)*200) # Getting cost of route
            else: opt += 150*time

            # Checking demand with input dict
            demand = 0
            for store in route[1]['Route'][1:-1]:
                store_type = locationData.loc[locationData["Supermarket"] == store, "Type"].values[0]
                demandtoadd = demands[store_type][0]
                demand += demandtoadd # TODO: refactor by store type in the optimal solution

            #if demand > 12:
            #    opt += 1200*np.ceil(demand%12) # Adding cost of mainfreight if we exceed truck demand
        opt += ((demand-20*12)%12)*1200 # Mainfreight covers excess demands

    else:
        for route in morning:
            time = generate_distribution_value(route[1]['Cost'], 2*route[1]['Cost'])/3600 # getting time

            if time > 4: opt += (150*4 + (time-4)*200) # Getting cost of route
            else: opt += 150*time

            # Checking demand with input dict
            demand = 0
            for store in route[1]['Route'][1:-1]:
                store_type = locationData.loc[locationData["Supermarket"] == store, "Type"].values[0]
                demandtoadd = demands[store_type][0]
                demand += demandtoadd # TODO: refactor by store type in the optimal solution

            #if demand > 12:
            #    opt += 1200*np.ceil(demand%12) # Adding cost of mainfreight if we exceed truck demand

        for route in afternoon:
            time = generate_distribution_value(route[1]['Cost'], 1.5*route[1]['Cost'])/3600 # getting time

            if time > 4: opt += (150*4 + (time-4)*200) # Getting cost of route
            else: opt += 150*time

            # Checking demand with input dict
            demand = 0
            for store in route[1]['Route'][1:-1]:
                store_type = locationData.loc[locationData["Supermarket"] == store, "Type"].values[0]
                demandtoadd = demands[store_type][0]
                demand += demandtoadd # TODO: refactor by store type in the optimal solution

            #if demand > 12:
            #    opt += 1200*np.ceil(demand%12) # Adding cost of mainfreight if we exceed truck demand
        opt += ((demand-20*12)%12)*1200 # Mainfreight covers excess demands

    return opt


