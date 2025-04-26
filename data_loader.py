import pandas as pd
import pathlib

class DataLoader:
    def __init__(self, country: str = 'ESP', neighbors: list = ["FRA", "PRT"], discount_rate: float = 0.07):
        self.country = country
        self.neighbors = neighbors
        self.dates = pd.date_range('2015-01-01 00:00Z', '2015-12-31 23:00Z', freq='h')
        self.r = discount_rate
        self.path = str(pathlib.Path(__file__).parent.resolve()) + "/"
        self.read_electricity_demand()
        self.read_onshore_wind()
        # self.read_offshore_wind()
        self.read_solar()

    def read_electricity_demand(self):
        """ Read electricity demand data from CSV file """

        df_elec = pd.read_csv(self.path + 'data/electricity_demand.csv', sep=';', index_col=0)
        df_elec.index = pd.to_datetime(df_elec.index)

        self.p_d = df_elec[[self.country]+self.neighbors][self.dates]

    def read_onshore_wind(self):
        """ Read onshore wind data from CSV file """

        df_onshorewind = pd.read_csv(self.path + 'data/onshore_wind_1979-2017.csv', sep=';', index_col=0)
        df_onshorewind.index = pd.to_datetime(df_onshorewind.index)

        self.cf_onw = df_onshorewind[self.country][self.dates]
    
    # def read_offshore_wind(self):
    #     """ Read offshore wind data from CSV file """

    #     df_offshorewind = pd.read_csv('data/offshore_wind_1979-2017.csv', sep=';', index_col=0)
    #     df_offshorewind.index = pd.to_datetime(df_offshorewind.index)

    #     self.cf_offw = df_offshorewind[self.country][self.dates]

    def read_solar(self):
        """ Read solar data from CSV file """

        df_solar = pd.read_csv(self.path + 'data/pv_optimal.csv', sep=';', index_col=0)
        df_solar.index = pd.to_datetime(df_solar.index)

        self.cf_solar = df_solar[self.country][self.dates]
