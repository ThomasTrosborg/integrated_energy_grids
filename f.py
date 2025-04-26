import pypsa
import numpy as np
from data_loader import DataLoader
from a import create_network, annuity
from b import add_co2_constraint, create_co2_limits
from d import add_storage
import results_plotter as plot

def add_neighbors(network: pypsa.Network, data: DataLoader):
    
    for neighbor in data.neighbors:
        network.add("Bus", neighbor)
        network.add(
            "Link",
            f"{data.country}-{neighbor}",
            bus0="electricity bus",
            bus1=neighbor,
            p_nom_extendable=True, # capacity is optimised
            p_min_pu=-1,
            length=600, # length (in km) between country a and country b
            capital_cost=400*600, # capital cost * length
        )

        network.add(
            "Load",
            f"{neighbor} load",
            bus=neighbor,
            p_set=data.p_d[neighbor].values,
        )

    network.add(
        "Generator",
        "FR nuke",
        bus="FR",
        p_nom_extendable=False, # capacity is fixed
        p_nom=data.p_d["FR"].max(), # capacity is fixed to the load
        carrier="nuke",
        marginal_cost=0,
    )
    

    return network

if __name__ == '__main__':
    data = DataLoader(country="ESP", discount_rate=0.07)

    co2_limit = 0

    # Create the network
    network = create_network(data)
    network = add_storage(network)
    network = add_co2_constraint(network, co2_limit) # 50 MT CO2 limit
    network = add_neighbors(network, data)

    # Optimize the network
    network.optimize()
