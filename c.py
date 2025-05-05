from data_loader import DataLoader
from a import create_network
import results_plotter as plot
import numpy as np
import matplotlib.pyplot as plt

#weather_years = [2015]
weather_years = range(1985, 2016) # all years

mixes = []

for w_year in weather_years:

    data = DataLoader(country="ESP", discount_rate=0.07, weather_year=w_year)
    # Create the network
    network = create_network(data)
    network.optimize.create_model()

    network.optimize()
    mix = []
    for ix, gen in enumerate(plot.REFERENCES['GENERATORS']):
        mix += [network.generators.p_nom_opt[gen]]
    for ix, link in enumerate(plot.REFERENCES['LINKS']):
        mix += [network.links.p_nom_opt[link]]
    mixes += [mix]

plot.plot_weather_variability(mixes, filename="c_weather_variability.png")