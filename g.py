import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import pypsa
from data_loader import DataLoader
import results_plotter as plot
from a import create_network
from b import add_co2_constraint
from d import add_storage
from f import add_neighbors
import warnings
warnings.filterwarnings("ignore", category=FutureWarning, module="pypsa")

def load_heating_demand_data():
    """
    Load heating demand data from a CSV file and set the index to the datetime column.
    
    Returns:
        pd.DataFrame: DataFrame containing the heating demand data with datetime index.
    """
    # Load the heating demand data
    # Assuming the CSV file is in the same directory as this script
    # and has a column 'utc_time' for datetime values
    data_HD = pd.read_csv('data/heat_demand.csv', sep=';')
    data_HD.index = pd.DatetimeIndex(data_HD['utc_time'])
    data_HD = data_HD[['ESP']]
    annual_hot_water = np.min(data_HD.ESP)*8760  # MWh/a
    annual_space_heating = np.sum(data_HD.ESP) - annual_hot_water  # MWh/a
    return data_HD, annual_space_heating, annual_hot_water

def load_temperature_data():
    """
    Load temperature data from a CSV file and set the index to the datetime column.
    
    Returns:
        pd.DataFrame: DataFrame containing the temperature data with datetime index.
    """
    # Load the temperature data
    # Assuming the CSV file is in the same directory as this script
    # and has a column 'utc_time' for datetime values
    data_T = pd.read_csv('data/temperature_PRT.csv',sep=';')
    data_T.index = pd.DatetimeIndex(data_T['utc_time'])
    data_T = data_T[['PRT']]
    return data_T

def create_heating_demand_profile(temperature_data, annual_space_heating, annual_hot_water):
    T_th=17 #ºC

    HDH=T_th-temperature_data['PRT']
    HDH[HDH<0]=0

    scale=annual_space_heating/HDH.sum()
    heating_demand=scale*HDH+annual_hot_water/8760

    return heating_demand

def cop(t_source, t_sink=55):
    delta_t = t_sink - t_source
    return 6.81 - 0.121 * delta_t + 0.00063 * delta_t**2

def couple_el_and_heat_sector(n:pypsa.Network, data:DataLoader):
    """
    Create the heat sector in the network.
    
    Parameters:
        n (pypsa.Network): The PyPSA network object.
        heat_demand_profile (pd.Series): The heating demand profile.
    
    Returns:
        pypsa.Network: The updated PyPSA network object with the heat sector added.
    """
    # Add a link for the heat pump
    n.add("Link",
        "heat pump",
        bus0="electricity bus",
        bus1="heat bus",
        p_nom_extendable=True,
        efficiency=cop(load_temperature_data().PRT.values),
        capital_cost=data.costs.at["central air-sourced heat pump", "capital_cost"],
        marginal_cost=data.costs.at["central air-sourced heat pump", "marginal_cost"],
    )
    
    # Add a multilink for CHP
    n.add("Bus", "biomass bus", carrier="biomass", x=data.coordinates[data.country][0], y=data.coordinates[data.country][1])

    # We add a gas store with energy capacity and an initial filling level much higher than the required gas consumption, 
    # this way gas supply is unlimited
    n.add("Generator",
          "Biomass Supply",
          carrier="biomass",
          bus="biomass bus",
          p_nom_extendable=True,
          capital_cost=0,
          ) 

    n.add(
        "Link",
        "CHP",
        bus0="biomass bus",
        bus1="electricity bus",
        bus2="heat bus",
        p_nom_extendable=True,
        capital_cost=data.costs.at["central solid biomass CHP CC", "capital_cost"],
        marginal_cost=data.costs.at["central solid biomass CHP CC", "marginal_cost"],
        efficiency=data.costs.at["central solid biomass CHP CC", "efficiency"],
        efficiency2=data.costs.at["central solid biomass CHP CC", "efficiency"],
    )

    return n

def create_non_coupled_el_and_heat_network(data:DataLoader, heat_demand_profile:pd.Series):
    """
    Create and run the heat network.
    
    Parameters:
        data (DataLoader): The data loader object containing the data.
        heat_demand_profile (pd.Series): The heating demand profile.
    
    Returns:
        pypsa.Network: The optimized PyPSA network object.
    """
    # Create the network
    n = create_network(data)
    n = add_storage(n, data)
    n.add("Carrier", "heat")
    # Add a bus for the heat sector
    n.add("Bus", "heat bus", carrier="heat", x=data.coordinates[data.country][0], y=data.coordinates[data.country][1])
    # Add a load for the heating demand
    n.add("Load", "heating demand", bus="heat bus", p_set=heat_demand_profile.values)
    #n.add("Gener", "BiomassStore", e_initial=1e6, e_nom=1e6, bus="biomass", capital_cost=0)
    n.add(
        "Generator",
        "Biomass Boiler",
        carrier="biomass",
        bus="heat bus",
        p_nom_extendable=True,
        capital_cost=data.costs.at["biomass boiler", "capital_cost"],
        marginal_cost=data.costs.at["biomass boiler", "marginal_cost"],
        efficiency=data.costs.at["biomass boiler", "efficiency"],
    )
    
    return n

if __name__ == "__main__":
    data = DataLoader(country="ESP", discount_rate=0.07)

    # Load the heating demand data
    heating_demand_data, annual_space_heating, annual_hot_water = load_heating_demand_data()
    
    # Load the temperature data
    temperature_data = load_temperature_data()

    # Create COP data
    cop_data = cop(temperature_data.PRT.values)
    
    # Create the heating demand profile
    heating_demand_profile = create_heating_demand_profile(temperature_data, annual_space_heating, annual_hot_water)
    
    # Plot the heating demand profile
    plt.figure(figsize=(10, 5))
    #plt.plot(heating_demand_profile.index, heating_demand_profile.values, label='Heating Demand Profile From Temperature', alpha=0.5)
    plt.plot(data.p_d.index, data.p_d.ESP.values, label='Electricity Data', alpha=0.5)
    plt.plot(heating_demand_data.index, heating_demand_data.values, label='Heating Data', alpha=0.5)
    plt.xlabel('Date')
    plt.ylabel('Demand (MWh/h)')
    plt.title("Spain's Electricity & Heating Demand Profile (2015)")
    plt.xlim(heating_demand_profile.index[0], heating_demand_profile.index[-1])
    plt.legend()
    plt.grid()
    plot.save_figure("heating_demand_profile.png")
    plt.close()
    raise()
    # Create the heat network
    isolated_sectors = create_non_coupled_el_and_heat_network(data, heating_demand_profile)
    # isolated_sectors.optimize()
    print("Combined system costs for simple heating solution: ", isolated_sectors.objective/1e6) # in million EUR

    # Create the network
    coupled_sectors = couple_el_and_heat_sector(isolated_sectors, data)
    coupled_sectors.optimize()
    print("Combined system cost for coupled heating solution: ", coupled_sectors.objective/1e6)

    plot.plot_series(coupled_sectors) #, filename="d_storage_plot.png")
    plot.plot_storage_season([coupled_sectors]) #, filename="d_storage_season_plot.png")
    plot.plot_generation_series(coupled_sectors, filename="g_generation_plot.png")
