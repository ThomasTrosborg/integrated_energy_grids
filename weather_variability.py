from data_loader import DataLoader
from main import create_network
import results_plotter as plot
import numpy as np

labels = ['onshorewind',
        'solar',
        'OCGT']
colors=['blue', 'orange', 'brown']

weather_years = [1981,1990]

mixes = []
variability_onw = []
variability_solar = []
variability_ocgt = []

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

    mixes += [[network.generators_t.p[label].sum() for label in labels]]
    variability_onw += [network.generators_t.p['onshorewind']]
    variability_solar += [network.generators_t.p['solar']]
    variability_ocgt += [network.generators_t.p['OCGT']]

print("Mixes: ", np.array(mixes).T)

plot.plot_weather_variability(mixes)