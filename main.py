import pandas as pd
import pypsa

def annuity(n,r):
    """ Calculate the annuity factor for an asset with lifetime n years and
    discount rate  r """

    if r > 0:
        return r/(1. - 1./(1.+r)**n)
    else:
        return 1/n


class DataLoader:
    def __init__(self, country: str = 'ESP'):
        self.country = country
        self.dates = pd.date_range('2015-01-01 00:00Z', '2015-12-31 23:00Z', freq='h')
        self.p_d = self.read_electricity_demand()
        self.p_onw = self.read_onshore_wind()
        self.p_solar = self.read_solar()

    def read_electricity_demand(self):
        """ Read electricity demand data from CSV file """

        df_elec = pd.read_csv('data/electricity_demand.csv', sep=';', index_col=0)
        df_elec.index = pd.to_datetime(df_elec.index)

        self.p_d = df_elec[self.country][self.dates]

    def read_onshore_wind(self):
        """ Read onshore wind data from CSV file """

        df_onshorewind = pd.read_csv('data/onshore_wind_1979-2017.csv', sep=';', index_col=0)
        df_onshorewind.index = pd.to_datetime(df_onshorewind.index)

        self.cf_onw = df_onshorewind[self.country][self.dates]

    def read_solar(self):
        """ Read solar data from CSV file """

        df_solar = pd.read_csv('data/pv_optimal.csv', sep=';', index_col=0)
        df_solar.index = pd.to_datetime(df_solar.index)

        self.cf_solar = df_solar[self.country][self.dates]


data = DataLoader(country="ESP")

# Create a new PyPSA network
network = pypsa.Network()

network.set_snapshots(data.dates.values)
