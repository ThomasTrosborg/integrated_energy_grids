import pypsa
import numpy as np
from data_loader import DataLoader
from a import create_network, annuity
from b import add_co2_constraint, create_co2_limits
from d import add_storage
import results_plotter as plot

def add_neighbors(network: pypsa.Network):
    network.add("Bus", "FR", carrier="electricity")
    network.add("Bus", "PT", carrier="electricity")

    network.add(
        "Link",
        "ESP-FR",
        bus0="electricity bus",
        bus1="FR",
        p_nom_extendable=True,
        efficiency=1,
        capital_cost=0, #annuity(30, 0.07) * 1000000 * (1 + 0.05),
    )

    network.add(
        "Link",
        "ESP-FR",
        bus0="electricity bus",
        bus1="FR",
        p_nom_extendable=True, # capacity is optimised
        p_min_pu=-1,
        length=600, # length (in km) between country a and country b
        capital_cost=400*600, # capital cost * length
    )

    network.add(
        "Link",
        "ESP-PT",
        bus0="electricity bus",
        bus1="PT",
        p_nom_extendable=True, # capacity is optimised
        p_min_pu=-1,
        length=600, # length (in km) between country a and country b
        capital_cost=400*600, # capital cost * length
    )

    network.add(
        "Load",
        "FR load",
        bus="electricity bus",
        p_set=0, #data.p_d.values,
    )

    network.add(
        "Load",
        "PT load",
        bus="electricity bus",
        p_set=0, #data.p_d.values,
    )

    network.add(
        "Generator",
        "FR nuke",
        bus="electricity bus",
        p_nom_extendable=False, # capacity is fixed
        p_nom=1000,
        carrier="nuke",
    )

    return network

if __name__ == '__main__':
    data = DataLoader(country="ESP", discount_rate=0.07)

    co2_limit = 0

    # Create the network
    network = create_network(data)
    network = add_storage(network)
    network = add_co2_constraint(network, co2_limit) # 50 MT CO2 limit
    network = add_neighbors(network)

    # Optimize the network
    network.optimize()
