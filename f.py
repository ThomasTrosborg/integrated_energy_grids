import pypsa
import numpy as np
from data_loader import DataLoader
from a import create_network, annuity
from b import add_co2_constraint, create_co2_limits
from d import add_storage
import results_plotter as plot

def add_neighbors(network: pypsa.Network, data: DataLoader):
    length = {"FRA": 400, "PRT": 90} # km source: https://www.ren.pt/en-gb/activity/main-projects/portugal-spain-interconnection
    for neighbor in data.neighbors:
        network.add(
            "Bus", 
            neighbor, 
            y = data.coordinates[neighbor][0],
            x = data.coordinates[neighbor][1],
            carrier="AC",
        )
        
        network.add(
            "Line",
            f"{data.country}-{neighbor}",
            bus0="electricity bus",
            bus1=neighbor,
            p_nom_extendable=True, # capacity is optimised
            p_min_pu=-1,
            r=0.02, # reactance [ohm/km]
            x=0.3, # resistance [ohm/km]
            length=length[neighbor], # length [km] between country a and country b
            capital_cost=2000*length[neighbor], # capital cost of 2000 [EUR/(MW*km)] * length [km]
        )
    
        network.add(
            "Load",
            f"{neighbor} load",
            bus=neighbor,
            p_set=data.p_d[neighbor].values,
        )

    multiplier = 1.5 # scaling factor for production in the neighboring countries

    network.add("Carrier", "nuke")
    network.add(
        "Generator",
        "FRA nuke",
        bus="FRA",
        p_nom_extendable=False, # capacity is fixed
        p_nom=61.4 * 1000 * multiplier, 
        carrier="nuke",
        marginal_cost=0,
    )

    capital_cost_onshorewind = annuity(30, data.r)*910000*(1+0.033) # in €/MW
    network.add(
        "Generator",
        "FRA wind",
        bus="FRA",
        p_nom_extendable=False, # capacity is fixed
        p_nom=24.6 * 1000, # capacity is fixed to the load
        carrier="onshore wind",
        marginal_cost=0,
        p_max_pu=data.cf_onw["FRA"].values, # capacity factor
        capital_cost = capital_cost_onshorewind,
    )

    capital_cost_solar = annuity(25,data.r)*425000*(1+0.03) # in €/MW
    network.add(
        "Generator",
        "FRA solar",
        bus="FRA",
        p_nom_extendable=False, # capacity is fixed
        p_nom= 21.2 * 1000 * multiplier, # capacity is fixed to the load
        carrier="solar",
        marginal_cost=0,
        p_max_pu=data.cf_solar["FRA"].values, # capacity factor
        capital_cost = capital_cost_solar,
    )

    # Add a generator in Portugal
    network.add(
        "Generator",
        "PRT wind",
        bus="PRT",
        p_nom_extendable=False, # capacity is fixed
        p_nom= 5.4 * 1000, # capacity is fixed to the load
        carrier="onshore wind",
        marginal_cost=0,
        p_max_pu=data.cf_onw["PRT"].values, # capacity factor
        capital_cost = capital_cost_onshorewind,
    )

    network.add(
        "Generator",
        "PRT solar",
        bus="PRT",
        p_nom_extendable=False, # capacity is fixed
        p_nom= 2.6 * 1000 * multiplier, # capacity is fixed to the load
        carrier="solar",
        marginal_cost=0,
        p_max_pu=data.cf_solar["PRT"].values, # capacity factor
        capital_cost = capital_cost_solar,
    )

    network.add(
        "Generator",
        "PRT gas",
        bus="PRT",
        p_nom_extendable=False, # capacity is fixed
        p_nom= 4.4 * 1000 * multiplier, # capacity is fixed to the load
        carrier="gas",
        marginal_cost=0,
        capital_cost = 0,
    )

    # Dammed hydro generator as a run of river generator. This is a simplification.
    # In reality, dammed hydro can store energy and is therefore a storage generator.
    # We will introduce this in the following exercises.
    network.add("Carrier", "Water")
    network.add("Bus", "DamWater PT", carrier = "Water")
    network.add( # The inflow of rainwater to the dam is modeled as a generator
        "Generator",
        "Rain to DamWater PT",
        bus = "DamWater PT",
        p_nom = 4.6 * 1000, 
        carrier = "Water",
        capital_cost = 0,
        marginal_cost = 0,
        p_max_pu = data.cf_hydro_PRT.values/max(data.cf_hydro_PRT.values),
    )
    
    network.add(
        "Link",
        "HDAM PT",
        bus0="DamWater PT",
        bus1="PRT",
        p_nom= 4.6 * 1000, 
        capital_cost = 0,
        marginal_cost = 0,
        efficiency = 0.95, # MWh_elec/MWh_potential_energy
    )

    return network

if __name__ == '__main__':
    data = DataLoader(country="ESP", discount_rate=0.07)

    co2_limit = 0

    # Create the network
    network = create_network(data)
    network = add_storage(network, data)
    # network = add_co2_constraint(network, co2_limit) # 50 MT CO2 limit
    network = add_neighbors(network, data)

    # Optimize the network
    network.optimize()
    network.plot(margin=0.4)

    print(0)