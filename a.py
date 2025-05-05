import pandas as pd
import pypsa
from data_loader import DataLoader, annuity
import results_plotter as plot
import warnings
warnings.filterwarnings("ignore", category=FutureWarning, module="pypsa")

def create_network(data: DataLoader):
    # Create a new PyPSA network
    network = pypsa.Network()
    network.set_snapshots(data.dates.values)

    # add the different carriers, only gas emits CO2
    network.add("Carrier", "gas", co2_emissions=0.198) # in t_CO2/MWh_th
    network.add("Carrier", "AC", co2_emissions=0)
    network.add("Carrier", "onshore wind")
    network.add("Carrier", "offshore wind")
    network.add("Carrier", "solar")
    network.add("Carrier", "biomass")

     # add the electricity bus
    network.add(
        "Bus", 
        "electricity bus", 
        y = data.coordinates[data.country][0],
        x = data.coordinates[data.country][1],
        carrier = "AC",
    )
    
    # add load to the bus
    network.add(
        "Load",
        "load",
        bus="electricity bus",
        p_set=data.p_d[data.country].values
    )

    # add onshore wind generator
    network.add(
        "Generator",
        "onshore wind",
        bus="electricity bus",
        p_nom_extendable=True,
        carrier="onshore wind",
        #p_nom_max=1000, # maximum capacity can be limited due to environmental constraints
        capital_cost=data.costs.at["onwind", "capital_cost"],
        marginal_cost=data.costs.at["onwind", "marginal_cost"],
        p_max_pu = data.cf_onw[data.country].values,
    )

    # add offshore wind generator
    # network.add(
    #     "Generator",
    #     "offshore wind",
    #     bus="electricity bus",
    #     p_nom_extendable=True,
    #     carrier="offshore wind",
    #     #p_nom_max=1000, # maximum capacity can be limited due to environmental constraints
    #     capital_cost=data.costs.at["offwind", "capital_cost"],
    #     marginal_cost=data.costs.at["offwind", "marginal_cost"],
    #     p_max_pu = data.cf_onw[data.country].values, #TODO use offshore wind data
    # )

    # add solar PV generator
    network.add(
        "Generator",
        "solar",
        bus="electricity bus",
        p_nom_extendable=True,
        carrier="solar",
        #p_nom_max=1000, # maximum capacity can be limited due to environmental constraints
        capital_cost=data.costs.at["solar", "capital_cost"],
        marginal_cost=data.costs.at["solar", "marginal_cost"],
        p_max_pu = data.cf_solar[data.country].values,
    )

    # add OCGT (Open Cycle Gas Turbine) generator
    network.add(
        "Generator",
        "OCGT",
        bus="electricity bus",
        p_nom_extendable=True,
        carrier="gas",
        #p_nom_max=1000,
        capital_cost=data.costs.at["OCGT", "capital_cost"],
        marginal_cost=data.costs.at["OCGT", "marginal_cost"],
        efficiency=data.costs.at["OCGT", "efficiency"],
    )

    # Dammed hydro generator as a run of river generator. This is a simplification.
    # In reality, dammed hydro can store energy and is therefore a storage generator.
    # We will introduce this in the following exercises.
    network.add("Carrier", "Water")
    network.add(
        "Bus", 
        "DamWater", 
        y = data.coordinates[data.country][0],
        x = data.coordinates[data.country][1],
        carrier = "Water",
    )

    network.add( # The inflow of rainwater to the dam is modeled as a generator
        "Generator",
        "Rain to DamWater",
        bus = "DamWater",
        p_nom = max(data.cf_hydro.values),
        carrier = "Water",
        capital_cost = 0,
        marginal_cost = 0,
        p_max_pu = data.cf_hydro.values/max(data.cf_hydro.values),
    )
    
    network.add(
        "Store",
        "DamReservoir",
        bus = "DamWater",
        e_nom = data.hydro_capacities["dammed_hydro_storage"].values[0],
        e_cyclic = True,
        capital_cost = 0,
    )

    network.add(
        "Link",
        "HDAM",
        bus0="DamWater",
        bus1="electricity bus",
        p_nom=data.hydro_capacities['dammed_hydro_power'].values[0],
        capital_cost=data.costs.at["hydro", "capital_cost"],
        marginal_cost=data.costs.at["hydro", "marginal_cost"],
        efficiency=data.costs.at["hydro", "efficiency"],
    )
    
    return network


if __name__ == "__main__":

    data = DataLoader(country="ESP", discount_rate=0.07)

    # Create the network
    network = create_network(data)
    network.optimize()

    plot.plot_series(network, ts=179*24, filename="a_series_summer.png")
    plot.plot_series(network, ts=11*24, filename="a_series_winter.png")
    plot.plot_electricity_mix(network, filename="a_electricity_mix.png")
    plot.plot_duration_curves(network, filename="a_duration_curves.png")
