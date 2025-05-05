import pandas as pd
import pathlib


def annuity(r,n):
    """ Calculate the annuity factor for an asset with lifetime n years and
    discount rate  r """

    if r > 0:
        return r/(1. - 1./(1.+r)**n)
    else:
        return 1/n


class DataLoader:
    def __init__(
            self, 
            country: str = 'ESP', 
            neighbors: list = ["FRA", "PRT"],
            coordinates: dict = {'ESP': (40.8, -2.4), 'PRT': (38.74, -9.15), 'FRA': (47.1, 2.29)},
            discount_rate: float = 0.07, 
            weather_year: int = 2015,
            cost_year: int = 2030,
        ):
        self.country = country
        self.neighbors = neighbors
        self.coordinates = coordinates
        self.dates = pd.date_range('2015-01-01 00:00Z', '2015-12-31 23:00Z', freq='h')
        self.weather_dates = pd.date_range(f'{weather_year}-01-01 00:00Z', f'{weather_year}-12-31 23:00Z', freq='h')
        self.r = discount_rate
        self.path = str(pathlib.Path(__file__).parent.resolve()) + "/"
        self.read_costs(cost_year)
        self.read_electricity_demand()
        self.read_onshore_wind()
        # self.read_offshore_wind()
        self.read_solar()
        self.read_hydro_capacities()
        self.read_hydro_inflows()
        self.read_hydro_inflows_PRT()

    def read_costs(self, cost_year: int):
        # Import data
        url = f"https://raw.githubusercontent.com/PyPSA/technology-data/master/outputs/costs_{cost_year}.csv"
        costs = pd.read_csv(url, index_col=[0, 1])
        costs.loc[costs.unit.str.contains("/kW"), "value"] *= 1e3
        costs.unit = costs.unit.str.replace("/kW", "/MW")

        defaults = {
            "FOM": 0,
            "VOM": 0,
            "efficiency": 1,
            "fuel": 0,
            "investment": 0,
            "lifetime": 25,
            "CO2 intensity": 0,
            "discount rate": 0.07,
        }
        costs = costs.value.unstack().fillna(defaults)

        # Set OCGT values to gas values
        costs.at["OCGT", "fuel"] = 35 # costs.at["gas", "fuel"]
        costs.at["OCGT", "CO2 intensity"] = costs.at["gas", "CO2 intensity"]
        costs.at["central solid biomass CHP CC", "fuel"] = costs.at["solid biomass", "fuel"]
        #costs.at["central solid biomass CHP CC", "CO2 intensity"] = costs.at["solid biomass", "CO2 intensity"]

        # Calculate marginal costs
        costs["marginal_cost"] = costs["VOM"] + costs["fuel"] / costs["efficiency"]

        # Calculate capital costs including annuity
        annuity_ = costs.apply(lambda x: annuity(x["discount rate"], x["lifetime"]), axis=1)
        costs["capital_cost"] = (annuity_ + costs["FOM"] / 100) * costs["investment"]

        self.costs = costs

    def read_electricity_demand(self):
        """ Read electricity demand data from CSV file """

        df_elec = pd.read_csv(self.path + 'data/electricity_demand.csv', sep=';', index_col=0)
        df_elec.index = pd.to_datetime(df_elec.index)

        self.p_d = df_elec[[self.country]+self.neighbors].loc[self.dates]

    def read_onshore_wind(self):
        """ Read onshore wind data from CSV file """
        df_onshorewind = pd.read_csv(self.path + 'data/onshore_wind_1979-2017.csv', sep=';', index_col=0)
        df_onshorewind.index = pd.to_datetime(df_onshorewind.index)


        df_onshorewind = df_onshorewind[[self.country]+self.neighbors].loc[self.weather_dates]
        self.cf_onw = df_onshorewind[~((df_onshorewind.index.month == 2) & (df_onshorewind.index.day == 29))]

    def read_hydro_inflows(self):
        """Read hydro data from CSV file and expand it to hourly resolution for 2013–2022"""

        # Load CSV and parse date
        df_hydro = pd.read_csv(self.path + 'data/Hydro_Inflow_ES.csv', sep=',')
        df_hydro['date'] = pd.to_datetime(df_hydro[['Year', 'Month', 'Day']])
        df_hydro['date'] = df_hydro['date'].dt.tz_localize('UTC')
        df_hydro.set_index('date', inplace=True)
        df_hydro.drop(columns=['Year', 'Month', 'Day'], inplace=True)

        # Convert daily inflow to hourly (divide by 24 and repeat)
        daily_values = df_hydro.copy()
        daily_values = daily_values.loc[daily_values.index.repeat(24)]
        daily_values.index = pd.date_range(
            start=df_hydro.index.min(),
            periods=len(daily_values),
            freq='h',
            tz='UTC'
        )
        daily_values['Inflow [GWh]'] /= 24

        # Repeat inflow values to cover 2013–2022
        target_index = pd.date_range(
            start='1983-01-01 00:00:00',
            end='2023-01-02 23:00:00',
            freq='h',
            tz='UTC'
        )
        num_hours_needed = len(target_index)
        hourly_cycle = daily_values['Inflow [GWh]'].values
        repeats = -(-num_hours_needed // len(hourly_cycle))  # Ceiling division
        full_inflow = pd.Series(hourly_cycle.tolist() * repeats, index=target_index)[:num_hours_needed]

        #Create final DataFrame with correct hourly index
        df_expanded = pd.DataFrame({'Inflow [MWh]': full_inflow*1000}) # Convert GWh to MWh
        df_expanded.index.name = 'datetime'

        self.cf_hydro = df_expanded.loc[self.weather_dates, 'Inflow [MWh]']
        self.cf_hydro= self.cf_hydro[~((self.cf_hydro.index.month == 2) & (self.cf_hydro.index.day == 29))] # Select only the dates we need
    
    def read_hydro_inflows_PRT(self):
        """Read hydro data from CSV file and expand it to hourly resolution for 2013–2022"""

        # Load CSV and parse date
        df_hydro = pd.read_csv(self.path + 'data/Hydro_Inflow_PT.csv', sep=',')
        df_hydro['date'] = pd.to_datetime(df_hydro[['Year', 'Month', 'Day']])
        df_hydro['date'] = df_hydro['date'].dt.tz_localize('UTC')
        df_hydro.set_index('date', inplace=True)
        df_hydro.drop(columns=['Year', 'Month', 'Day'], inplace=True)

        # Convert daily inflow to hourly (divide by 24 and repeat)
        daily_values = df_hydro.copy()
        daily_values = daily_values.loc[daily_values.index.repeat(24)]
        daily_values.index = pd.date_range(
            start=df_hydro.index.min(),
            periods=len(daily_values),
            freq='h',
            tz='UTC'
        )
        daily_values['Inflow [GWh]'] /= 24

        # Repeat inflow values to cover 2013–2022
        target_index = pd.date_range(
            start='2013-01-01 00:00:00',
            end='2023-01-01 23:00:00',
            freq='h',
            tz='UTC'
        )
        num_hours_needed = len(target_index)
        hourly_cycle = daily_values['Inflow [GWh]'].values
        repeats = -(-num_hours_needed // len(hourly_cycle))  # Ceiling division
        full_inflow = pd.Series(hourly_cycle.tolist() * repeats, index=target_index)[:num_hours_needed]

        #Create final DataFrame with correct hourly index
        df_expanded = pd.DataFrame({'Inflow [MWh]': full_inflow*1000}) # Convert GWh to MWh
        df_expanded.index.name = 'datetime'

        self.cf_hydro_PRT = df_expanded.loc[self.dates, 'Inflow [MWh]'] # Select only the dates we need
    

    # def read_offshore_wind(self):
    #     """ Read offshore wind data from CSV file """

    #     df_offshorewind = pd.read_csv('data/offshore_wind_1979-2017.csv', sep=';', index_col=0)
    #     df_offshorewind.index = pd.to_datetime(df_offshorewind.index)

    #     self.cf_offw = df_offshorewind["FRA"][self.dates]

    def read_solar(self):
        """ Read solar data from CSV file """

        df_solar = pd.read_csv(self.path + 'data/pv_optimal.csv', sep=';', index_col=0)
        df_solar.index = pd.to_datetime(df_solar.index)

        df_solar = df_solar[[self.country]+self.neighbors].loc[self.weather_dates]
        self.cf_solar = df_solar[~((df_solar.index.month == 2) & (df_solar.index.day == 29))]

    def read_hydro_capacities(self):
        """ Read hydro data from CSV file """

        df_hydro_capacities = pd.read_csv(self.path + 'data/jrc-hydro-power-plant-database.csv', sep=',')
        df_hydro_capacities = df_hydro_capacities[df_hydro_capacities['country_code'] == self.country[:2]]
        df_hydro_capacities = df_hydro_capacities[['installed_capacity_MW', 'type', 'storage_capacity_MWh']]
        pumped_hydro_power = df_hydro_capacities[df_hydro_capacities['type'] == 'HPHS']['installed_capacity_MW'].sum()
        pumped_hydro_storage = df_hydro_capacities[df_hydro_capacities['type'] == 'HPHS']['storage_capacity_MWh'].sum()
        run_of_river_power = df_hydro_capacities[df_hydro_capacities['type'] == 'HROR']['installed_capacity_MW'].sum()
        dammed_hydro_power = df_hydro_capacities[df_hydro_capacities['type'] == 'HDAM']['installed_capacity_MW'].sum()
        dammed_hydro_storage = df_hydro_capacities[df_hydro_capacities['type'] == 'HDAM']['storage_capacity_MWh'].sum()
        self.hydro_capacities = pd.DataFrame({
            'pumped_hydro_power': [pumped_hydro_power],
            'pumped_hydro_storage': [pumped_hydro_storage],
            'run_of_river_power': [run_of_river_power],
            'dammed_hydro_power': [dammed_hydro_power],
            'dammed_hydro_storage': [dammed_hydro_storage]
        }) # Create DataFrame with hydro capacities in MW and MWh
        self.hydro_capacities.index = [self.country] # Set index to country code

if __name__ == "__main__":
    data = DataLoader(country="ESP", discount_rate=0.07)
    print(data.p_d.head())
    print(data.cf_onw.head())
    # print(data.cf_offw.head())
    print(data.cf_solar.head())
    print(data.hydro_capacities.head())
    print(data.cf_hydro.head())