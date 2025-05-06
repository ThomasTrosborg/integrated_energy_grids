import pypsa
import numpy as np
from data_loader import DataLoader
from a import create_network, annuity
from b import add_co2_constraint, create_co2_limits
from d import add_storage
import results_plotter as plot

if __name__ == "__main__":
    data = DataLoader(country="ESP", discount_rate=0.07)

    # Create the CO2 limits
    co2_limits = create_co2_limits(10)

    co2_prices = []
    for co2_limit in co2_limits:
        # Create the network
        network = create_network(data)
        network = add_storage(network, data)
        network = add_co2_constraint(network, co2_limit)

        # Optimize the network
        network.optimize()

        # Retrieve CO2 price
        co2_price = - network.global_constraints.mu.iloc[0]
        print(f"CO2 limit: {co2_limit} tonCO2")
        print(f"CO2 price: {np.round(co2_price / 1000, 2)} t€/tonCO2")
        co2_prices.append(np.round(co2_price, 2))

    plot.plot_co2_limit_vs_price(co2_limits=co2_limits, co2_prices=np.array(co2_prices)) #, filename="e_co2_limit_vs_price.png")

# co2_limits = [50000000., 20000000., 16000000., 12000000., 8000000., 4000000., 2000000., 0.]
# co2_prices = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 87.16, 26605.84]