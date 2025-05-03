import pypsa
import numpy as np
from data_loader import DataLoader
from a import create_network, annuity
from b import add_co2_constraint, create_co2_limits
from d import add_storage
import results_plotter as plot
import matplotlib.pyplot as plt

def add_neighbors(network: pypsa.Network, data: DataLoader):
    length = {"FRA": 400, "PRT": 90} # km source: https://www.ren.pt/en-gb/activity/main-projects/portugal-spain-interconnection
    for neighbor in data.neighbors:
        network.add(
            "Bus", 
            neighbor, 
            y = data.coordinates[neighbor][0],
            x = data.coordinates[neighbor][1],
            carrier = "AC",
        )
        
        
        network.add(
            "Line",
            f"{data.country}-{neighbor}",
            bus0="electricity bus",
            bus1=neighbor,
            s_nom_extendable=True, # capacity is optimised
            r=0.02, # reactance [ohm/km]
            x=0.3, # resistance [ohm/km]
            length=length[neighbor], # length [km] between country a and country b
            capital_cost=2000*length[neighbor], # capital cost of 2000 [EUR/(MW*km)] * length [km]
            #type = "Al/St 560/50 4-bundle 750.0", # type of line
        )
        
        network.add(
            "Load",
            f"{neighbor} load",
            bus=neighbor,
            p_set=data.p_d[neighbor].values,
        )

    multiplier = 1 # scaling factor for production in the neighboring countries

    network.add("Carrier", "nuke", co2_emissions=0) # in t_CO2/MWh_th
    network.add(
        "Generator",
        "FRA nuke",
        bus="FRA",
        p_nom_extendable=False, # capacity is fixed
        p_nom=61.4 * 1000 * multiplier,
        carrier="nuke",
        capital_cost=data.costs.at["nuclear", "capital_cost"],
        marginal_cost=data.costs.at["nuclear", "marginal_cost"],
        efficiency=data.costs.at["nuclear", "efficiency"],
    )

    network.add(
        "Generator",
        "FRA wind",
        bus="FRA",
        p_nom_extendable=False, # capacity is fixed
        p_nom=24.6 * 1000, # capacity is fixed to the load
        carrier="onshore wind",
        p_max_pu=data.cf_onw["FRA"].values, # capacity factor
        capital_cost=data.costs.at["onwind", "capital_cost"],
        marginal_cost=data.costs.at["onwind", "marginal_cost"],
    )

    network.add(
        "Generator",
        "FRA solar",
        bus="FRA",
        p_nom_extendable=False, # capacity is fixed
        p_nom= 21.2 * 1000 * multiplier, # capacity is fixed to the load
        carrier="solar",
        p_max_pu=data.cf_solar["FRA"].values, # capacity factor
        capital_cost=data.costs.at["solar", "capital_cost"],
        marginal_cost=data.costs.at["solar", "marginal_cost"],
    )

    # Add a generator in Portugal
    network.add(
        "Generator",
        "PRT wind",
        bus="PRT",
        p_nom_extendable=False, # capacity is fixed
        p_nom= 5.4 * 1000, # capacity is fixed to the load
        carrier="onshore wind",
        p_max_pu=data.cf_onw["PRT"].values, # capacity factor
        capital_cost=data.costs.at["onwind", "capital_cost"],
        marginal_cost=data.costs.at["onwind", "marginal_cost"],
    )

    network.add(
        "Generator",
        "PRT solar",
        bus="PRT",
        p_nom_extendable=False, # capacity is fixed
        p_nom= 2.6 * 1000 * multiplier, # capacity is fixed to the load
        carrier="solar",
        p_max_pu=data.cf_solar["PRT"].values, # capacity factor
        capital_cost=data.costs.at["solar", "capital_cost"],
        marginal_cost=data.costs.at["solar", "marginal_cost"],
    )

    network.add(
        "Generator",
        "PRT gas",
        bus="PRT",
        p_nom_extendable=False, # capacity is fixed
        p_nom= 4.4 * 1000 * multiplier, # capacity is fixed to the load
        carrier="gas",
        capital_cost=data.costs.at["OCGT", "capital_cost"],
        marginal_cost=data.costs.at["OCGT", "marginal_cost"],
        efficiency=data.costs.at["OCGT", "efficiency"],
    )

    # Dammed hydro generator as a run of river generator. This is a simplification.
    # In reality, dammed hydro can store energy and is therefore a storage generator.
    # We will introduce this in the following exercises.
    network.add("Carrier", "Water")
    network.add("Bus", "PRT DamWater", carrier = "Water",y = data.coordinates["PRT"][0],
            x = data.coordinates["PRT"][1],)
    network.add( # The inflow of rainwater to the dam is modeled as a generator
        "Generator",
        "PRT Rain to DamWater",
        bus = "PRT DamWater",
        p_nom = max(data.cf_hydro_PRT.values), 
        carrier = "Water",
        capital_cost = 0,
        marginal_cost = 0,
        p_max_pu = data.cf_hydro_PRT.values/max(data.cf_hydro_PRT.values),
    )
    network.add(
        "Store",
        "DamReservoir PRT",
        bus = "DamWater PRT",
        e_nom = data.hydro_capacities["dammed_hydro_storage"].values[0],
        e_cyclic = True,
        capital_cost = 0,
    )
    network.add(
        "Link",
        "PRT HDAM",
        bus0="PRT DamWater",
        bus1="PRT",
        p_nom_extendable=False, # capacity is fixed
        p_nom= 4.6 * 1000, 
        capital_cost=data.costs.at["hydro", "capital_cost"],
        marginal_cost=data.costs.at["hydro", "marginal_cost"],
        efficiency=data.costs.at["hydro", "efficiency"],
    )

    return network

if __name__ == '__main__':
    data = DataLoader(country="ESP", discount_rate=0.07)

    print(len(data.cf_hydro))
    print(data.cf_hydro.max())
    print(max(data.cf_hydro.values))


    co2_limit = 0

    # Create the network
    network = create_network(data)
    network = add_storage(network, data)
    # network = add_co2_constraint(network, co2_limit) # 50 MT CO2 limit
    network = add_neighbors(network, data)

    # Optimize the network
    network.optimize()
    network.plot(margin=0.4)
    plt.show()

    network.generators.p_nom_opt.div(10**3).plot.barh()
    plt.show()
    plot.plot_electricity_mix(network) #, filename="f_electricity_mix.png")

    print(0)