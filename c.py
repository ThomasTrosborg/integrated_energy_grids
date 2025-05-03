from data_loader import DataLoader
from a import create_network
import results_plotter as plot
import numpy as np

weather_years = [1980,1985,1990,1995,2000,2010,2015]

mixes = []

for w_year in weather_years:

    data = DataLoader(country="ESP", discount_rate=0.07, weather_year=w_year)
    # Create the network
    network = create_network(data)
    network.optimize.create_model()

    #TODO : Beslut om det er med eller uden CO2 constraint
    network.add("GlobalConstraint",
            "co2_limit: MT",
            type="primary_energy",
            carrier_attribute="co2_emissions",
            sense="<=",
            constant=20e6)
    network.optimize()
    mix = []
    for ix, gen in enumerate(plot.REFERENCES['GENERATORS']):
        mix += [network.generators.p_nom_opt[gen]]
    for ix, link in enumerate(plot.REFERENCES['LINKS']):
        mix += [network.links.p_nom_opt[link]]
    mixes += [mix]
    #mixes += [[network.generators_t.p[label].sum() for label in plot.LABELS]]

print("Mixes: ", np.array(mixes).T)

plot.plot_weather_variability(mixes)