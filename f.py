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
            r=0.031, # resistance [ohm/km]
            x=0.29, # reactance [ohm/km]
            length=length[neighbor], # length [km] between country a and country b
            capital_cost=442.1414*length[neighbor], # capital cost of 2000 [EUR/(MW*km)] * length [km]
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
        bus = "PRT DamWater",
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

def compare_capacity_mixes(data: DataLoader, co2_limit: float, filename: str | None = None):
    """ Compare capacity mixes with and without the CO2 constraint and storage """
    n_base = create_network(data)
    n_base.optimize()

    n_storage_co2 = create_network(data)
    n_storage_co2 = add_storage(n_storage_co2, data)
    n_storage_co2 = add_co2_constraint(n_storage_co2, 0) # 0 MT CO2 limit
    n_storage_co2.optimize()

    co2_limit = 0 # 50 MT CO2 limit

    # Create the network
    network = create_network(data)
    network = add_storage(network, data)
    network = add_co2_constraint(network, co2_limit)
    network = add_neighbors(network, data)

    # Optimize the network
    network.optimize()

    networks = {
        "Base": n_base,
        "Storage + CO2": n_storage_co2,
        "Storage + 0 CO2 + interconnections": network,
    }
    plot.capacity_mixes_storage(networks, filename)
    

if __name__ == '__main__':
    data = DataLoader(country="ESP", discount_rate=0.07)
    
    co2_limit = 0 # 50 MT CO2 limi
    compare_capacity_mixes(data, co2_limit, filename="d_capacity_mix_plot.png")

    print(len(data.cf_hydro))
    print(data.cf_hydro.max())
    print(max(data.cf_hydro.values))
    print("PRT DamWater", max(data.cf_hydro_PRT.values))

    

    # Create the network
    network = create_network(data)
    network = add_storage(network, data)
    network = add_co2_constraint(network, co2_limit)
    network = add_neighbors(network, data)

    # Optimize the network
    network.optimize()
    
    plot.plot_storage_day_neighbor(network, filename = "storge_with_interconnectors.png")

    plot.plot_electricity_mix_neighbor_fra(network, filename = "electricity_mix_neighborFRA.png")
    plot.plot_electricity_mix_neighbor_prt(network, filename = "electricity_mix_neighbor_prt.png")


    network.generators.p_nom_opt.div(10**3).plot.barh()
    plt.xlabel("Capacity (GW)")
    plt.show()
    plot.plot_electricity_mix(network) #, filename="f_electricity_mix.png")
    
    

    network.lines_t.p0.groupby(network.lines_t.p0.index.date).mean().plot()
    plt.ylabel("Power (GW) - leaving Spain")
    plt.xlabel("Time (Daily Resolution)")
    plt.title("Power Flow in Lines")
    plt.legend(title="Line")
    plt.tight_layout()
    plt.show()  

    

    network.lines.s_nom_opt.div(1e3).plot.barh()
    plt.xlabel("Capacity (GW)")
    plt.ylabel("Line")
    plt.title("Line Capacity")
    plt.tight_layout()
    plt.show()  

    print(network.links_t.p0)
    print(network.generators_t.p)

    print(0)