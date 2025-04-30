import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import pypsa
import os
from data_loader import DataLoader
from a import annuity
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

def create_heat_sector(n:pypsa.Network, heat_demand_profile:pd.Series, cop_data):
    """
    Create the heat sector in the network.
    
    Parameters:
        n (pypsa.Network): The PyPSA network object.
        heat_demand_profile (pd.Series): The heating demand profile.
    
    Returns:
        pypsa.Network: The updated PyPSA network object with the heat sector added.
    """
    # Add a bus for the heat sector
    n.add("Bus", "heat ESP", carrier="heat")
    
    # Add a load for the heating demand
    n.add("Load", "heating demand", bus="heat bus", p_set=heat_demand_profile.values)
    
    # Add a link for the heat pump
    heat_pump_marginal_cost = 2.6561 # €/MWh_th
    heat_pump_capital_cost = 906.0988*1000 * (annuity(25, 0.07) + 0.002336)  # €/MW
    n.add("Link", "heat pump", bus0="electricity bus", bus1="heat ESP",
           p_nom_extendable=True, efficiency=cop_data,
           capital_cost=heat_pump_capital_cost, marginal_cost=heat_pump_marginal_cost)
    
    # Add a multilink for CHP
    n.add("Bus", "gas")

    # We add a gas store with energy capacity and an initial filling level much higher than the required gas consumption, 
    # this way gas supply is unlimited
    n.add("Store", "gas", e_initial=1e6, e_nom=1e6, bus="gas") 

    gas_cost = 4  # €/MWh_th
    chp_capital_cost = 906.0988*1000 * (annuity(25, 0.07) + 0.033214)  # €/MW
    fuel_cost = 21.6 # in €/MWh_th
    chp_marginal_cost = 4.4445 + fuel_cost # €/MWh_th
    n.add(
        "Link",
        "CHP",
        bus0="gas",
        bus1="electricity",
        bus2="heat",
        p_nom_extendable=True,
        marginal_cost=chp_marginal_cost,
        capital_cost=chp_capital_cost,
        efficiency=0.41,
        efficiency2=0.41,
    )

    return n


if __name__ == "__main__":
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
    plt.plot(heating_demand_profile.index, heating_demand_profile.values, label='Heating Demand Profile From Temperature', alpha=0.5)
    plt.plot(heating_demand_data.index, heating_demand_data.values, label='Heating Demand Data', alpha=0.5)
    plt.xlabel('Date')
    plt.ylabel('Heating Demand (MWh/h)')
    plt.title('Heating Demand Profile Generation Comparison')
    plt.legend()
    plt.grid()
    plt.show()
