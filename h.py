import pypsa
import numpy as np
from data_loader import DataLoader
from a import create_network, annuity
from b import add_co2_constraint, create_co2_limits
from d import add_storage
import results_plotter as plot
import matplotlib.pyplot as plt

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
    network.plot(margin=0.4)
    plt.show()

    network.generators.p_nom_opt.div(10**3).plot.barh()
    plt.show()
    plot.plot_electricity_mix(network) #, filename="f_electricity_mix.png")

    network.stores_t.e.groupby(network.stores_t.e.index.month).mean().div(1e3).plot()
    plt.ylabel("GWh")
    plt.xlabel("Month")
    plt.title("Average storage level per month")
    plt.show()

    print(0)