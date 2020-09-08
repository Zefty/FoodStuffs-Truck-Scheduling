ORSkey = '5b3ce3597851110001cf6248b1727d42fc2949e6b106028a682c47a0' 

import numpy as np
import pandas as pd
import folium
import openrouteservice as ors
from ast import literal_eval
from os import sep
import seaborn as sns

locationData = pd.read_csv("Data" + sep + "FoodstuffLocations.csv")
locationData.loc[locationData["Supermarket"] == "Fresh Collective Alberton", "Type"] = "Four Square"

def getindex(locations, store):
    return locations.loc[locations["Supermarket"] == store].index[0]

def VisualiseRoutes(locations, routes, name=None, times=None, demands=None): # TODO add more arguments depending on output of routeselection
    """
    This function plots the travel path of routes on a folium map in different colours.

    Inputs:
        locations : pandas.DataFrame
            The dataframe containing store names and coordinates
        routes : list
            The list of lists of store names representing routes through supermarkets
        times : array-like ? TODO
            Array representing times for each route for potential visualisation
        demands : array-like ? TODO
            Array representing demands for each route for potential visualisation

    Outputs:
        routes_map.html
            An HTML file containing an interactive map with supermarket locations and routes plotted
    """
    coords = locations[['Long', 'Lat']]
    coords = coords.to_numpy().tolist()

    # Initialise folium map
    m = folium.Map(location = list(reversed(coords[0])), zoom_start=10)

    # Draw warehouse node
    folium.Marker(list(reversed(coords[0])), popup = locations.Supermarket[0], icon = folium.Icon(color = 'black')).add_to(m)

    # Draw supermarket nodes
    for i in range(1, len(coords)):
        if locations.Type[i] == "New World":
            iconCol = "red"
        elif locations.Type[i] == "Pak 'n Save":
            iconCol = "orange"
        else:
            iconCol = "green"
        folium.Marker(list(reversed(coords[i])), popup = locations.Supermarket[i], icon = folium.Icon(color = iconCol)).add_to(m)

    palette = sns.color_palette("husl", 20).as_hex()

    # Fetch and draw routes
    client = ors.Client(key=ORSkey)

    #lineColors = ["red", "orange", "green", "blue", "black"]
    for i in range(len(routes)):
        stores = routes[i]
        print(stores)
        route = client.directions(
            coordinates = [coords[getindex(locations, store)] for store in stores],
            profile     = 'driving-hgv',
            format      = 'geojson',
            validate    = False
        )
        lineCol = palette[i % len(palette)]
        folium.PolyLine(locations = [list(reversed(coord)) for coord in route['features'][0]['geometry']['coordinates']], color = lineCol).add_to(m)
    if name:
        m.save('routes_map_' + name + '.html')
    else:
        m.save('routes_map.html')


    ################################################################
    # Map 2
    m2 = folium.Map(location = list(reversed(coords[0])), zoom_start=10)

    # Draw warehouse node
    folium.Marker(list(reversed(coords[0])), popup = locations.Supermarket[0], icon = folium.Icon(color = 'black')).add_to(m2)

    # Draw supermarket nodes
    for i in range(1, len(coords)):
        if locations.Type[i] == "New World":
            iconCol = "red"
        elif locations.Type[i] == "Pak 'n Save":
            iconCol = "orange"
        else:
            iconCol = "green"
        folium.Marker(list(reversed(coords[i])), popup = locations.Supermarket[i], icon = folium.Icon(color = iconCol)).add_to(m2)

    # Fetch and draw routes
    for i in range(len(routes)):
        lineCol = palette[i % len(palette)]
        folium.PolyLine(locations = [list(reversed(coords[getindex(locations, store)])) for store in routes[i]], color = lineCol).add_to(m2)

    if name:
        m2.save('routes_straightline_map_' + name + '.html')
    else:
        m2.save('routes_straightline_map.html')
    '''
    ################################################################
    # Map 3
    m2 = folium.Map(location = list(reversed(coords[0])), zoom_start=10)

    # Draw warehouse node
    folium.Marker(list(reversed(coords[0])), popup = locations.Supermarket[0], icon = folium.Icon(color = 'black')).add_to(m2)

    # Draw supermarket nodes
    for i in range(1, len(coords)):
        if locations.Type[i] == "New World":
            iconCol = "red"
        elif locations.Type[i] == "Pak 'n Save":
            iconCol = "orange"
        else:
            iconCol = "green"
        folium.Marker(list(reversed(coords[i])), popup = locations.Supermarket[i], icon = folium.Icon(color = iconCol)).add_to(m2)

    # Fetch and draw routes
    for i in range(len(routes)):
        lineCol = palette[i % len(palette)]
        folium.PolyLine(locations = [list(reversed(coords[getindex(locations, store)])) for store in routes[i]], color = lineCol).add_to(m2)

    m2.save('routes_straightline_map.html')
    '''


'''
optimalSolution = pd.read_csv("Data" + sep + "chosenRoutes.csv", converters = {"Route": literal_eval})
print(optimalSolution)
optimalSolutionRoutes = optimalSolution['Route'].tolist()
print(optimalSolutionRoutes)

VisualiseRoutes(locationData, optimalSolutionRoutes)
'''