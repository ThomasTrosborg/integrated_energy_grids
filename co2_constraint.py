from data_loader import DataLoader
from a import create_network
import results_plotter as plot
import numpy as np

labels = ['onshorewind',
        'solar',
        'OCGT']
colors=['blue', 'orange', 'brown']

data = DataLoader(country="ESP", discount_rate=0.07)
# Create the network
network = create_network(data)
network.optimize.create_model()
# Spain's CO2 emissions data: https://www.iea.org/countries/spain/emissions
# It is at 49 MT CO2 in 2022, down from 118 MT in 2007. Was at 40 MT in 2020.
n_opts = 10
co2_limits = np.append(np.array([50e6]), np.linspace(20e6, 0, n_opts-1)) #tonCO2

mixes = []

for lim in co2_limits:
    network.add("GlobalConstraint",
            "co2_limit:" + str(lim/1e6) + "MT",
            type="primary_energy",
            carrier_attribute="co2_emissions",
            sense="<=",
            constant=lim)
    network.optimize()
    mixes += [[network.generators_t.p[label].sum() for label in labels]]

plot.plot_generation_mixes(mixes, co2_limits, filename="co2_limit.png")
