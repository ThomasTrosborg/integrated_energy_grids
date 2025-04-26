import pandas as pd
import pypsa
from data_loader import DataLoader
import results_plotter as plot
import warnings
warnings.filterwarnings("ignore", category=FutureWarning, module="pypsa")

def annuity(n,r):
    """ Calculate the annuity factor for an asset with lifetime n years and
    discount rate  r """

    if r > 0:
        return r/(1. - 1./(1.+r)**n)
    else:
        return 1/n

def create_network(data: DataLoader):
    # Create a new PyPSA network
    network = pypsa.Network()
    network.set_snapshots(data.dates.values)

    # add the different carriers, only gas emits CO2
    network.add("Carrier", "gas", co2_emissions=0.19) # in t_CO2/MWh_th
    network.add("Carrier", "electricity", co2_emissions=0)
    network.add("Carrier", "onshore wind")
    network.add("Carrier", "offshore wind")
    network.add("Carrier", "solar")

     # add the electricity bus
    network.add("Bus", "electricity bus", carrier="electricity")

    # add load to the bus
    network.add(
        "Load",
        "load",
        bus="electricity bus",
        p_set=data.p_d[data.country].values
    )

    # add onshore wind generator
    capital_cost_onshorewind = annuity(30, data.r)*910000*(1+0.033) # in €/MW
    network.add(
        "Generator",
        "onshore wind",
        bus="electricity bus",
        p_nom_extendable=True,
        carrier="onshore wind",
        #p_nom_max=1000, # maximum capacity can be limited due to environmental constraints
        capital_cost = capital_cost_onshorewind,
        marginal_cost = 0,
        p_max_pu = data.cf_onw.values,
    )

    # add offshore wind generator
    capital_cost_offshorewind = annuity(25, data.r)*2506000*(1+0.03) # in €/MW
    network.add(
        "Generator",
        "offshore wind",
        bus="electricity bus",
        p_nom_extendable=True,
        carrier="offshore wind",
        #p_nom_max=1000, # maximum capacity can be limited due to environmental constraints
        capital_cost = capital_cost_offshorewind,
        marginal_cost = 0,
        p_max_pu = data.cf_onw.values, #TODO use offshore wind data
    )

    # add solar PV generator
    capital_cost_solar = annuity(25,data.r)*425000*(1+0.03) # in €/MW
    network.add(
        "Generator",
        "solar",
        bus="electricity bus",
        p_nom_extendable=True,
        carrier="solar",
        #p_nom_max=1000, # maximum capacity can be limited due to environmental constraints
        capital_cost = capital_cost_solar,
        marginal_cost = 0,
        p_max_pu = data.cf_solar.values,
    )

    # add OCGT (Open Cycle Gas Turbine) generator
    capital_cost_OCGT = annuity(25, data.r)*560000*(1+0.033) # in €/MW
    fuel_cost = 21.6 # in €/MWh_th
    efficiency = 0.39 # MWh_elec/MWh_th
    marginal_cost_OCGT = fuel_cost/efficiency # in €/MWh_el
    network.add(
        "Generator",
        "OCGT",
        bus="electricity bus",
        p_nom_extendable=True,
        carrier="gas",
        #p_nom_max=1000,
        capital_cost = capital_cost_OCGT,
        marginal_cost = marginal_cost_OCGT,
    )

    # Dammed hydro generator as a run of river generator. This is a simplification.
    # In reality, dammed hydro can store energy and is therefore a storage generator.
    # We will introduce this in the following exercises.
    network.add("Carrier", "Water")
    network.add("Bus", "DamWater", carrier = "Water")
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
    capital_cost_hydro = annuity(80, data.r)*2000000*(1+0.01) # in €/MW
    network.add(
        "Link",
        "HDAM",
        bus0="DamWater",
        bus1="electricity bus",
        p_nom=data.hydro_capacities['dammed_hydro_power'].values[0],
        capital_cost = capital_cost_hydro,
        marginal_cost = 0,
        efficiency = 0.95, # MWh_elec/MWh_potential_energy
    )
    
    return network


if __name__ == "__main__":

    data = DataLoader(country="ESP", discount_rate=0.07)

    # Create the network
    network = create_network(data)
    network.optimize()

    plot.plot_series(network, ts=180*24) #, filename="a_series_summer.png")
    plot.plot_series(network, ts=0) #, filename="a_series_winter.png")
    plot.plot_electricity_mix(network) #, filename="a_electricity_mix.png")
    plot.plot_duration_curves(network) #, filename="a_duration_curves.png")
