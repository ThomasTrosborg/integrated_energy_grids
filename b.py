import pypsa
from data_loader import DataLoader
from a import create_network
import results_plotter as plot
import numpy as np

def create_co2_limits(n_opts: int = 10):
    return np.append(np.array([50e6]), np.linspace(20e6, 0, n_opts-1)) #tonCO2

def add_co2_constraint(network: pypsa.Network, co2_limit: float):
    network.add(
        "GlobalConstraint",
        "co2_limit:" + str(co2_limit/1e6) + "MT",
        type="primary_energy",
        carrier_attribute="co2_emissions",
        sense="<=",
        constant=co2_limit,
    )
    return network

def simulate_tests(network: pypsa.Network, n_opts: int = 10):
    co2_limits = create_co2_limits(n_opts)

    mixes = []
    for co2_limit in co2_limits:
        network = add_co2_constraint(network, co2_limit)
        network.optimize()
        mix = []
        for ix, gen in enumerate(plot.REFERENCES['GENERATORS']):
            mix += [network.generators.p_nom_opt[gen]]
        for ix, link in enumerate(plot.REFERENCES['LINKS']):
            mix += [network.links.p_nom_opt[link]]
        mixes += [mix]

    plot.plot_capacity_variation_under_varying_co2_limits(mixes, co2_limits, filename="b_co2_limit.png")


if __name__ == '__main__':
    data = DataLoader(country="ESP", discount_rate=0.07)
    # Create the network
    network = create_network(data)
    network.optimize.create_model()
    # Spain's CO2 emissions data: https://www.iea.org/countries/spain/emissions
    # It is at 49 MT CO2 in 2022, down from 118 MT in 2007. Was at 40 MT in 2020.
    simulate_tests(network, n_opts=2)
