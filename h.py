import pypsa
import numpy as np
from data_loader import DataLoader
from a import create_network, annuity
from b import add_co2_constraint, create_co2_limits
from d import add_storage
import results_plotter as plot
import matplotlib.pyplot as plt
import pandas as pd

if __name__ == '__main__':
    data = DataLoader(country="ESP", discount_rate=0.07)


    co2_limit = 0 # 50 MT CO2 limit

    # Create the network
    network = create_network(data)
    network = add_storage(network, data)
    network = add_co2_constraint(network, co2_limit)
    network.remove("Generator", "Rain to DamWater")


    # Optimize the network
    network.optimize()

    plot.plot_electricity_mix(network) #, filename="f_electricity_mix.png")

        # Ensure the index is a DateTimeIndex
    e = network.stores_t.e
    e.index = pd.to_datetime(e.index)

    # Get raw Battery timeseries (in hourly resolution), converted to GWh
    storage = e[["Battery","H2 Storage", "PumpedHydro", "DamReservoir"]].div(1e3)

    # Plot
    storage.plot(figsize=(14, 6),alpha=0.6, )
    plt.ylabel("GWh")
    plt.xlabel("Time (Hourly Resolution)")
    plt.title("Storage Levels: Battery, Hydro and H2")
    plt.legend(title="Storage Type")
    plt.tight_layout()
    plt.show()

    print(0)
