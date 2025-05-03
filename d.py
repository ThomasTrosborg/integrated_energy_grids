import pypsa
from data_loader import DataLoader
from a import create_network, annuity
from b import add_co2_constraint, create_co2_limits
import results_plotter as plot

def add_hydrogen(network: pypsa.Network, data: DataLoader):
    #Create a new carrier
    network.add("Carrier", "H2")

    #Create a new bus
    network.add(
        "Bus", 
        "H2", 
        y = data.coordinates[data.country][0],
        x = data.coordinates[data.country][1],
        carrier = "H2",
    )

    #Connect the store to the bus
    network.add(
        "Store",
        "H2 Storage",
        bus = "H2",
        e_nom_extendable = True,
        e_cyclic = True,
        capital_cost=data.costs.at["hydrogen storage underground", "capital_cost"],
        marginal_cost=data.costs.at["hydrogen storage underground", "marginal_cost"],
        efficiency=data.costs.at["hydrogen storage underground", "efficiency"],
    )

    #Add the link "H2 Electrolysis" that transport energy from the electricity bus (bus0) to the H2 bus (bus1)
    #with 80% efficiency
    network.add(
        "Link",
        "H2 Electrolysis",
        bus0 = "electricity bus",
        bus1 = "H2",
        p_nom_extendable = True,
        capital_cost=data.costs.at["electrolysis", "capital_cost"],
        marginal_cost=data.costs.at["electrolysis", "marginal_cost"],
        efficiency=data.costs.at["electrolysis", "efficiency"],
    )

    #Add the link "H2 Fuel Cell" that transports energy from the H2 bus (bus0) to the electricity bus (bus1)
    #with 58% efficiency
    network.add(
        "Link",
        "H2 Fuel Cell",
        bus0 = "H2",
        bus1 = "electricity bus",
        p_nom_extendable = True,
        capital_cost=data.costs.at["fuel cell", "capital_cost"],
        marginal_cost=data.costs.at["fuel cell", "marginal_cost"],
        efficiency=data.costs.at["fuel cell", "efficiency"],
    )
    return network

def add_battery_storage(network: pypsa.Network, data: DataLoader):
    # Create a new bus for the battery storage
    # Source for costs: https://www.nrel.gov/docs/fy23osti/85332.pdf
    network.add(
        "Bus", 
        "Battery",
        y = data.coordinates[data.country][0],
        x = data.coordinates[data.country][1], 
        carrier="AC",
    )

    # Add a store for the battery storage
    network.add(
        "Store",
        "Battery",
        bus = "Battery",
        e_nom_extendable = True,
        e_cyclic = True,
        capital_cost=data.costs.at["battery storage", "capital_cost"],
    )

    # Add a link for the battery storage
    network.add(
        "Link",
        "AC-DC Converter",
        bus0 = "electricity bus",
        bus1 = "Battery",
        p_nom_extendable = True,
        capital_cost=data.costs.at["battery inverter", "capital_cost"]/2,
        marginal_cost=data.costs.at["battery inverter", "marginal_cost"],
        efficiency=data.costs.at["battery inverter", "efficiency"],
    )

    network.add(
        "Link",
        "DC-AC Inverter",
        bus0 = "Battery",
        bus1 = "electricity bus",
        p_nom_extendable = True,
        capital_cost=data.costs.at["battery inverter", "capital_cost"]/2,
        marginal_cost=data.costs.at["battery inverter", "marginal_cost"],
        efficiency=data.costs.at["battery inverter", "efficiency"],
    )
    return network

def add_hydro_storages(network: pypsa.Network, data: DataLoader):
    network.add(
        "Bus", 
        "PumpedHydro",
        y = data.coordinates[data.country][0],
        x = data.coordinates[data.country][1],
        carrier="Water",
    )
    network.add(
        "Store",
        "PumpedHydro",
        bus = "PumpedHydro",
        e_nom = data.hydro_capacities["pumped_hydro_storage"].values[0],
        e_cyclic = True,
        capital_cost = 0,
    )
    capital_cost_hydro = annuity(80, data.r)*2000000*(1+0.01) # in €/MW
    network.add(
        "Link",
        "PumpedHydroTurbine",
        bus0 = "PumpedHydro",
        bus1 = "electricity bus",
        p_nom = data.hydro_capacities["pumped_hydro_power"].values[0],
        capital_cost=data.costs.at["PHS", "capital_cost"]/2,
        marginal_cost=data.costs.at["PHS", "marginal_cost"],
        efficiency=data.costs.at["PHS", "efficiency"],
    )
    network.add(
        "Link",
        "PumpedHydroPump",
        bus0 = "electricity bus",
        bus1 = "PumpedHydro",
        p_nom = data.hydro_capacities["pumped_hydro_power"].values[0],
        capital_cost=data.costs.at["PHS", "capital_cost"]/2,
        marginal_cost=data.costs.at["PHS", "marginal_cost"],
        efficiency=data.costs.at["PHS", "efficiency"],
    )
    return network

def add_storage(network: pypsa.Network, data: DataLoader):
    """ Add storage to the network """

    # Add hydro storage
    network = add_hydro_storages(network, data)

    # Add hydrogen storage
    network = add_hydrogen(network, data)

    # Add battery storage
    network = add_battery_storage(network, data)
    
    return network

def compare_co2_limits(network: pypsa.Network, co2_limits: list):
    networks = []
    for co2_limit in co2_limits:
        net = create_network(data)
        net = add_storage(net, data)
        # net = network.copy()
        net = add_co2_constraint(net, co2_limit)
        net.optimize()
        networks.append(net)
    
    plot.plot_storage_season(networks) #, filename="storage_season_co2_plot.png")


if __name__ == "__main__":
    data = DataLoader(country="ESP", discount_rate=0.07)

    co2_limit = 0

    # Create the network
    network = create_network(data)
    network = add_storage(network, data)
    network = add_co2_constraint(network, co2_limit) # 50 MT CO2 limit

    # Optimize the network
    network.optimize()

    # Plot the results
    plot.plot_storage_day(network) #, filename="d_storage_day_plot.png")
    plot.plot_storage_season([network]) #, filename="d_storage_season_plot.png")
    # plot.plot_series(network) #, filename="d_storage_plot.png")

    # Compare the results with and without the CO2 constraint
    co2_limits = create_co2_limits(n_opts=5)
    compare_co2_limits(network, co2_limits)
