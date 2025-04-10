from data_loader import DataLoader
from a import create_network, annuity
import results_plotter as plot

def add_storage(network: pypsa.Network):
    #Create a new carrier
    network.add("Carrier", "H2")

    #Create a new bus
    network.add("Bus", "H2", carrier = "H2")

    #Connect the store to the bus
    network.add(
        "Store",
        "H2 Tank",
        bus = "H2",
        e_nom_extendable = True,
        e_cyclic = True,
        capital_cost = annuity(25, 0.07)*57000*(1+0.011)
    )

    #Add the link "H2 Electrolysis" that transport energy from the electricity bus (bus0) to the H2 bus (bus1)
    #with 80% efficiency
    network.add("Link",
            "H2 Electrolysis",
            bus0 = "electricity bus",
            bus1 = "H2",
            p_nom_extendable = True,
            efficiency = 0.8,
            capital_cost = annuity(25, 0.07)*600000*(1+0.05))

    #Add the link "H2 Fuel Cell" that transports energy from the H2 bus (bus0) to the electricity bus (bus1)
    #with 58% efficiency
    network.add("Link",
            "H2 Fuel Cell",
            bus0 = "H2",
            bus1 = "electricity bus",
            p_nom_extendable = True,
            efficiency = 0.58,
            capital_cost = annuity(10, 0.07)*1300000*(1+0.05))
    
    return network


if __name__ == "__main__":
    data = DataLoader(country="ESP", discount_rate=0.07)
    # Create the network
    network = create_network(data)
    network = add_storage(network)

    # Optimize the network
    network.optimize()

    # Plot the results
    plot.plot_series(network) #, filename="storage_plot.png")
