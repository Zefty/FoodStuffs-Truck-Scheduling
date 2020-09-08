####################################################################################
#
# Import Python Core modules
#
####################################################################################
from ast import literal_eval
from scipy import stats
import matplotlib.pyplot as plt
import statsmodels.stats.weightstats as sms
import statistics
import seaborn as sns
####################################################################################
#
# Import FoodStuffs Model modules
#
####################################################################################
from DataAnalysis import *
from RouteGenKCI import *
from visualisations import *
from RouteGen import *
from routeselectionV1 import *
from routeselectionV2 import *
from routegenAlex import *
from simulation import *
'''
####################################################################################
#
# ENGSCI 263 2019: OR Project Truck Scheduling for Foodstuffs
#
####################################################################################
'''
def main():
    '''
    Uncomment the function you would like to run :D
    '''
    print("Running functions ...\n")
    # DataAnalysis()
    #AlexRouteGeneration()
    #AlexRouteSelection()
    # Visualisations()
    # RouteGenUsingKCI()
    GenerateOptimalSolution(day = "Friday")
    #RunSimulation()
    # RunSimulation2()
    print("Done!")

def DataAnalysis():
    '''
    Stuff
    '''
    # Load data
    demandData = pd.read_csv("Data" + sep + "demandData.csv")
    locationData = pd.read_csv("Data" + sep + "FoodstuffLocations.csv")
    supermarkets = list(locationData["Supermarket"])

    #demandData = pd.read_csv() TODO finish this line
    # Clean data for analysis
    demandData = clean_data(demandData, locationData)
    locationData.loc[locationData["Supermarket"] == "Fresh Collective Alberton", "Type"] = "Four Square"

    # Visualise interaction profiles
    figure = interaction_plot(demandData["Weekday"], demandData["Type"], demandData["Demand"], ylabel="Demand")
    figure.suptitle("Interaction Plot")
    figure.savefig('Pictures/interactionplot.png')

    # Fit model
    demandModel = ols("np.log(Demand + 1) ~ Weekday + Type + Weekday:Type", demandData).fit()

    # Generate assumption check plots
    assumption_plots(demandModel)

    # Perform two-way ANOVA
    print(anova_lm(demandModel, typ=2))

    # Print summary (coefficients and R^2)
    print(demandModel.summary())

    # Predict demand data for weekdays and supermarket types using model
    demandPreds = predict_demand_data(demandModel.params)

    # Write predicted demand data to CSV file
    demandPreds.to_csv("Data" + sep + "demandModel.csv", index=False)

def AlexRouteGeneration():
        # Import data + clean up
    locationData = pd.read_csv("Data" + sep + "FoodstuffLocations.csv")
    locationData.loc[locationData["Supermarket"] == "Fresh Collective Alberton", "Type"] = "Four Square"
    locationData = locationData[1:][:] # Remove warehouse node

    # Import travel times between supermarkets + demand predictions per store
    timeData = pd.read_csv("Data" + sep + "FoodstuffTravelTimes.csv", index_col = 0)
    demandPreds = pd.read_csv("Data" + sep + "demandModel.csv")

    # Separate supermarkets into k regions
    l = []
    for i in range(7, 11):
        newL = list(KRegionalClusters(locationData, k=i, plot=False))
        l.append(newL)
    routeData, supermarkets = RouteConstructionAlex(locationData, timeData, l, demandPreds, "Monday")
    routeData.to_csv("Data" + sep + "AlexGeneratedRoutesTest.csv", index=False)

def AlexRouteSelection():
    # Read data
    routeData = pd.read_csv("Data" + sep + "AlexGeneratedRoutesTest.csv")
    locationData = pd.read_csv("Data" + sep + "FoodstuffLocations.csv")
    locationData.loc[locationData["Supermarket"] == "Fresh Collective Alberton", "Type"] = "Four Square"
    # Delete warehouse node
    locationData.drop(locationData[locationData["Type"] == "Warehouse"].index, inplace = True)
    supermarkets = list(locationData["Supermarket"])

    if True:
        print("Checking for unincluded stores:")
        for store in supermarkets:
            included = 0
            i = 0
            while i < len(routeData) and not included:
                if store in routeData['Route'][i]:
                    included = 1
                i+=1
            if not included:
                print(f"{store} is not in any routes!")

    # Route selection and then display results + save into CSV for easier access
    routes, obj1 = RouteSelection(routeData, supermarkets)
    chosenRoutes = routes.loc[routes['State'] == 1]
    chosenRoutes.to_csv("Data" + sep + "AlexChosenRoutesMonday.csv", index=False)

    # print(routes)
    print(obj1)  # Total Cost of Traversing Routes =  98843.76000000001 but in dollar is 4118.49
    print(chosenRoutes)
    print("DONE SELECTING")
    return

def RouteGenUsingKCI(day = "Monday"):
    '''
    Default solution is a weekday solution
    Please call with day = "Saturday" for weekend solution
    '''
    # Import data
    locationData = pd.read_csv("Data" + sep + "FoodstuffLocations.csv")
    locationData.loc[locationData["Supermarket"] == "Fresh Collective Alberton", "Type"] = "Four Square"
    # Delete warehouse node
    locationData.drop(locationData[locationData["Type"] == "Warehouse"].index, inplace = True)
    # if (day == "Saturday"):
    #     locationData.drop(locationData[locationData["Type"] == "Four Square"].index, inplace = True)
    timeData = pd.read_csv("Data" + sep + "FoodstuffTravelTimes.csv", index_col = 0)
    demandPreds = pd.read_csv("Data" + sep + "demandModel.csv")

    # Create k regions
    l = KRegionalClusters(locationData, k=2, plot=False)

    # Generate routes
    routeData1, stores = RouteConstruction(locationData, timeData, l, demandPreds, day)
    frame = [routeData1]
    for i in range(1,12):
        routeData2, stores = RouteConstruction2(locationData, timeData, l, demandPreds, day, min = i)
        frame.append(routeData2)
    routeData = pd.concat(frame, ignore_index = True)
    # Save routes to csv
    routeData.to_csv("Data" + sep + "Routes" + sep + "generatedRoutes" + day + ".csv", index=False)

def GenerateOptimalSolution(day = "Monday"):
    '''
    Default solution is a weekday solution
    Please call with day = "Saturday" for weekend solution
    '''
    # Regenerate routes first
    RouteGenUsingKCI(day)

    # Read data
    routeData = pd.read_csv("Data" + sep + "Routes" + sep + "generatedRoutes" + day + ".csv", converters = {"Route": literal_eval})
    locationData = pd.read_csv("Data" + sep + "FoodstuffLocations.csv")
    locationData.loc[locationData["Supermarket"] == "Fresh Collective Alberton", "Type"] = "Four Square"
    # Delete warehouse node
    locationData.drop(locationData[locationData["Type"] == "Warehouse"].index, inplace = True)
    # if (day == "Saturday"):
    #     locationData.drop(locationData[locationData["Type"] == "Four Square"].index, inplace = True)
    supermarkets = list(locationData["Supermarket"])

    # Route selection
    routes, obj = RouteSelectionV2(routeData, supermarkets)
    optimalRoutes = routes.loc[routes['State'] == 1]
    save = True

    # Checking if solution acutally covers all supermarkets
    print("Commencing Debugging")
    for s in supermarkets:
        included = 0
        i = 0
        while i < len(optimalRoutes) and not included:
            if s in optimalRoutes['Route'][i]:
                included = 1
            i+=1
        if not included:
            save = False
            print(f"{s} is not in any routes!")
    print("Finished Debugging\n")

    # Saving ...
    if save:
        print('Saving optimal routes to csv ...')
        optimalRoutes.to_csv("Data" + sep + "Routes" + sep + "optimalRoutes" + day + ".csv", index=False)
        print('... Saved!')

    return optimalRoutes

def Visualisations():
    #routes = pd.read_csv("Data" + sep + "AlexChosenRoutesMonday.csv", converters = {"Route": literal_eval})
    routes = pd.read_csv("Data" + sep + "Routes" + sep + "optimalRoutesMonday.csv", converters = {"Route": literal_eval})
    locationData = pd.read_csv("Data" + sep + "FoodstuffLocations.csv")
    locationData.loc[locationData["Supermarket"] == "Fresh Collective Alberton", "Type"] = "Four Square"

    optimalRoutes = routes.loc[routes['State'] == 1]["Route"].to_list()

    # Standalone testing
    # routes =    [["Warehouse", "New World Albany", "Pak 'n Save Henderson", "Four Square Everglade", "Warehouse"],
    #            ["Warehouse", "New World Milford", "Pak 'n Save Mangere", "Fresh Collective Alberton", "Warehouse"]]


    VisualiseRoutes(locationData, optimalRoutes, 'weekday') # Saves map to html

    # Weekend visualisation
    routes = pd.read_csv("Data" + sep + "Routes" + sep + "optimalRoutesSaturday.csv", converters = {"Route": literal_eval})
    locationData = pd.read_csv("Data" + sep + "FoodstuffLocations.csv")
    locationData.loc[locationData["Supermarket"] == "Fresh Collective Alberton", "Type"] = "Four Square"

    optimalRoutes = routes.loc[routes['State'] == 1]["Route"].to_list()

    VisualiseRoutes(locationData, optimalRoutes, 'weekend') # Saves map to html

    return

def RunSimulation(weekday = "Monday", weekend = "Saturday"):
    # Initialise list of optimal solution routes
    weekRoutes = pd.read_csv("Data" + sep + "Routes" + sep + "optimalRoutes" + weekday + ".csv", converters = {"Route": literal_eval})
    wkndRoutes = pd.read_csv("Data" + sep + "Routes" + sep + "optimalRoutes" + weekend + ".csv", converters = {"Route": literal_eval})
    wmed = []
    med = []

    # Get cleaned dataframe
    demandData = pd.read_csv("Data" + sep + "demandData.csv")
    locationData = pd.read_csv("Data" + sep + "FoodstuffLocations.csv")
    demandData = clean_data(demandData,locationData)
    locationData.loc[locationData["Supermarket"] == "Fresh Collective Alberton", "Type"] = "Four Square"

    # 1000 runs for monte carlo simulation for weekday
    cost = []
    for i in range(1000):
        # reset lists for optimal solution
        wopt = []
        opt = []
        for j in range(1000):
            # Import travel times between supermarkets + demand predictions per store
            opt.append(simulate(weekRoutes, demandData, locationData, wknd=False))
            wopt.append(simulate(wkndRoutes, demandData, locationData, wknd=True))

        # Sorting and getting medians
        cost.append(opt)
        opt.sort()
        med.append(opt[500])
        wopt.sort()
        wmed.append(wopt[500])

    plt.hist(cost, density=True, histtype='stepfilled', alpha=0.2)
    plt.show()

    # Histograms for optimal solutions, on weekday and weekend
    plt.hist(opt, density=True, histtype='stepfilled', alpha=0.2)
    plt.show()
    plt.hist(wopt, density=True, histtype='stepfilled', alpha=0.2)
    plt.show()

    # One-sample t-test
    stats.ttest_1samp(opt,popmean=0) # Weekday
    stats.ttest_1samp(wopt,popmean=0) # Weekend

    # Histograms for medians
    plt.hist(med, density=True, histtype='stepfilled', alpha=0.2)
    plt.show()
    plt.hist(wmed, density=True, histtype='stepfilled', alpha=0.2)
    plt.show()

    # Percentile interval
    med.sort()
    med[25]
    med[975]
    wmed.sort()
    wmed[25]
    wmed[975]

def RunSimulation2(weekday="Monday", weekend="Saturday"):
    # Initialise list of optimal solution routes
    weekRoutes = pd.read_csv("Data" + sep + "Routes" + sep + "optimalRoutes" + weekday + ".csv", converters = {"Route": literal_eval})
    wkndRoutes = pd.read_csv("Data" + sep + "Routes" + sep + "optimalRoutes" + weekend + ".csv", converters = {"Route": literal_eval})

    # Get cleaned dataframe
    demandData = pd.read_csv("Data" + sep + "demandData.csv")
    locationData = pd.read_csv("Data" + sep + "FoodstuffLocations.csv")
    demandData = clean_data(demandData,locationData)
    locationData.loc[locationData["Supermarket"] == "Fresh Collective Alberton", "Type"] = "Four Square"
    [a,b,c] = setupbootstrap(demandData,wknd=False)
    [d,e,f] = setupbootstrap(demandData,wknd=True)

    # 1000 runs for monte carlo simulation for weekday
    wopt = []
    opt = []
    for i in range(1000):
        # Import travel times between supermarkets + demand predictions per store
        opt.append(simulate(weekRoutes, locationData, a, b, c, wknd=False))
        wopt.append(simulate(wkndRoutes, locationData, d, e, f, wknd=True))

    # Seaborn plot 
    ax = sns.distplot(wopt, bins=100)
    ax.set_title("Weekend Optimal Solution")
    ax.set_xlabel("Optimal Solution Value ($)")
    ax.set_ylabel("Probablity")
    plt.savefig("Pictures/wopt.png")
    plt.show()
    ax = sns.distplot(opt, bins=100)
    ax.set_title("Weekday Optimal Solution")
    ax.set_xlabel("Optimal Solution Value ($)")
    ax.set_ylabel("Probablity")
    plt.savefig("Pictures/opt.png")
    plt.show()

    # Calculate confidence intervals 
    optLower, optUpper = sms.DescrStatsW(opt).tconfint_mean(alpha = 0.05)
    woptLower, woptUpper = sms.DescrStatsW(wopt).tconfint_mean(alpha = 0.05)

    print("Mean and CI of Weekday")
    print(statistics.mean(opt))
    print(optLower, optUpper)

    print("Mean and CI of Weekend")
    print(statistics.mean(wopt))
    print(woptLower, woptUpper)

    # Sorting and getting prediction intervals for the optimal solution
    opt.sort()
    wopt.sort()

    # Histograms for optimal solutions, on weekday and weekend
    f, (ax1, ax2) = plt.subplots(1, 2, figsize=(15,10))
    ax1.hist(opt, density=True, bins = 100, histtype='stepfilled', alpha=0.2)
    ax1.axvline(x=optLower, color='r', linewidth=2)
    ax1.axvline(x=optUpper, color='r', linewidth=2)
    ax1.axvline(x=opt[25], color='b', linewidth=2)
    ax1.axvline(x=opt[975], color='b', linewidth=2)
    ax1.set_title("Weekday Optimal Solution")
    ax1.set_xlabel("Optimal Solution Value ($)")
    ax1.set_ylabel("Probablity")
    ax2.hist(wopt, density=True, bins = 100, histtype='stepfilled', alpha=0.2)
    ax2.axvline(x=woptLower, color='r', linewidth=2)
    ax2.axvline(x=woptUpper, color='r', linewidth=2)
    ax2.axvline(x=wopt[25], color='b', linewidth=2)
    ax2.axvline(x=wopt[975], color='b', linewidth=2)
    ax2.set_title("Weekend Optimal Solution")
    ax2.set_xlabel("Optimal Solution Value ($)")
    ax2.set_ylabel("Probablity")
    plt.savefig("Pictures/Simulation.png")
    plt.show()

    # One-sample t-test
    tstat, pval = stats.ttest_1samp(opt,popmean=opt[500]) # Weekday
    print("The t-statistic is {}, and the p-value for weekdays is {}.".format(tstat,pval))
    tstat, pval = stats.ttest_1samp(wopt,popmean=wopt[500]) # Weekend
    print("The t-statistic is {}, and the p-value for weekends is {}.".format(tstat,pval))

if __name__ == "__main__":
    main()



    # f, (ax1, ax2) = plt.subplots(1, 2)
    # x = stats.norm.rvs(loc = 10, scale = 2, size = 100)+stats.uniform.rvs(loc=-2,scale=8,size=100)
    # xlower, xupper = sms.DescrStatsW(x).tconfint_mean(alpha = 0.05)
    # print(xlower, xupper)
    # ax1.hist(x, density=True, bins = 10, histtype='stepfilled', alpha=0.2)
    # ax1.axvline(x=xlower, color='r', linewidth=3)
    # ax1.axvline(x=xupper, color='r', linewidth=3)
    # plt.show()