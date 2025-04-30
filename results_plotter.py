import matplotlib.pyplot as plt
import pathlib
import numpy as np
import pypsa
from typing import List, Tuple

REFERENCES  = {'GENERATORS' : ['onshore wind', 'solar', 'OCGT'],
               'LINKS'      : ['HDAM'],
               'LOADS'      : ['load']
               }
COLORS      = {'GENERATORS' : ['green', 'orange', 'brown'],
               'LINKS'      : ['blue'],
               'LOADS'      : ['black']
               }
LABELS      = {'GENERATORS' : ['Onshore Wind', 'Solar', 'Gas (OCGT)'],
               'LINKS'      : ['Hydro (Dam)'],
               'LOADS'      : ['Demand']
               }

def save_figure(filename):
    filepath = str(pathlib.Path(__file__).parent.resolve()) + "/results/" + filename
    plt.tight_layout()
    plt.savefig(filepath, dpi=300)

def plot_series(network, ts: int = 0, filename: str | None = None):
    te = ts + 96
    for ix, load in enumerate(REFERENCES['LOADS']):
        plt.plot(network.loads_t.p[load][ts:te], color=COLORS['LOADS'][ix], label=LABELS['LOADS'][ix])
    for ix, gen in enumerate(REFERENCES['GENERATORS']):
        plt.plot(network.generators_t.p[gen][ts:te], color=COLORS['GENERATORS'][ix], label=LABELS['GENERATORS'][ix])
    for ix, link in enumerate(REFERENCES['LINKS']):
        plt.plot(-network.links_t.p1[link][ts:te], color=COLORS['LINKS'][ix], label=LABELS['LINKS'][ix])
    plt.legend(fancybox=True, shadow=True, loc='best')
    plt.xlabel("Time")
    plt.ylabel("MW")
    plt.xticks(rotation=45)

    if filename is not None: save_figure(filename)

    plt.show()

def plot_electricity_mix(network, filename: str | None = None):
    # Plot the electricity mix
    sizes = []
    colors = []
    labels = []
    for ix, gen in enumerate(REFERENCES['GENERATORS']):
        sizes += [network.generators_t.p[gen].sum()]
        colors += [COLORS['GENERATORS'][ix]]
        labels += [LABELS['GENERATORS'][ix]]
    for ix, link in enumerate(REFERENCES['LINKS']):
        sizes += [-network.links_t.p1[link].sum()]
        colors += [COLORS['LINKS'][ix]]
        labels += [LABELS['LINKS'][ix]]

    plt.pie(sizes,
            colors=colors,
            labels=labels,
            wedgeprops={'linewidth':0},
            autopct='%1.1f%%',)
    plt.axis('equal')

    plt.title('Electricity mix')

    if filename is not None: save_figure(filename)

    plt.show()

def plot_duration_curves(network, filename: str | None = None):
    dur_curves = []
    colors = []
    labels = []
    for ix, load in enumerate(REFERENCES['LOADS']):
        dur_curves += [network.loads_t.p[load].sort_values(ascending=False).values]
        colors += [COLORS['LOADS'][ix]]
        labels += [LABELS['LOADS'][ix]]
    for ix, gen in enumerate(REFERENCES['GENERATORS']):
        dur_curves += [network.generators_t.p[gen].sort_values(ascending=False).values]
        colors += [COLORS['GENERATORS'][ix]]
        labels += [LABELS['GENERATORS'][ix]]
    for ix, link in enumerate(REFERENCES['LINKS']):
        dur_curves += [-network.links_t.p1[link].sort_values(ascending=False).values]
        colors += [COLORS['LINKS'][ix]]
        labels += [LABELS['LINKS'][ix]]
    
    for ix in range(len(dur_curves)):
        plt.plot(range(len(dur_curves[ix])),
                 dur_curves[ix],
                 color=colors[ix],
                 label=labels[ix])

    plt.title('Duration Curves')
    plt.legend()
    plt.xlabel("Duration (hours/yr)")
    plt.ylabel("MW")

    if filename is not None: save_figure(filename)

    plt.show()

def plot_generation_mixes(network_sols, co2_limits, filename: str | None = None):
    colors = []
    labels = []
    for ix, gen in enumerate(REFERENCES['GENERATORS']):
        colors += [COLORS['GENERATORS'][ix]]
        labels += [LABELS['GENERATORS'][ix]]
    for ix, link in enumerate(REFERENCES['LINKS']):
        colors += [COLORS['LINKS'][ix]]
        labels += [LABELS['LINKS'][ix]]
        
    mixes = np.array(network_sols).T
    for ix, label in enumerate(labels):
        plt.plot(co2_limits, mixes[ix], '--bo', label=label, color=colors[ix])
    plt.xlabel(r"CO2 limit (Mt CO$_2$)")
    plt.xticks(co2_limits, [str(int(x/1e6)) for x in co2_limits])
    plt.ylabel(r"Generation (MWh)")
    plt.legend()
    plt.title(r'Generation mixes under emissions limitations')

    if filename is not None: save_figure(filename)

    plt.show()


def plot_weather_variability(network_sols, filename: str = None):

    labels = ['onshorewind', 'solar', 'OCGT']
    colors = ['blue', 'orange', 'brown']
    mixes = np.array(network_sols)
    boxprops = dict(color='black')  # Default box properties
    medianprops = dict(color='red')  # Default median line properties

    for i, color in enumerate(colors):
        plt.boxplot(
            mixes[:, i],
            positions=[i + 1],
            patch_artist=True,
            boxprops=dict(facecolor=color, color=color),
            medianprops=medianprops,
            label=labels[i]
        )

    plt.xticks(ticks=range(1, len(labels) + 1), labels=labels)

    plt.xlabel(r"Generator technology")
    plt.ylabel(r"Mean Capacity (MW)")
    plt.legend()
    plt.title(r'Average generation mixes using different weather years')

    if filename is not None: save_figure(filename)
    plt.show()

    
def plot_storage_day(network: pypsa.Network, filename: str | None = None):
    plt.plot(
        network.loads_t.p['load'].groupby(network.snapshots.hour).mean(), 
        color='black', 
        label='demand',
    )
    plt.plot(
        network.generators_t.p['onshore wind'].groupby(network.snapshots.hour).mean(), 
        color='blue', 
        label='onshore wind',
    )
    plt.plot(
        network.generators_t.p['solar'].groupby(network.snapshots.hour).mean(), 
        color='orange', 
        label='solar',
    )
    plt.plot(
        network.generators_t.p['OCGT'].groupby(network.snapshots.hour).mean(), 
        color='brown', 
        label='gas (OCGT)',
    )
    plt.plot(
        network.links_t.p0['H2 Electrolysis'].groupby(network.snapshots.hour).mean(), 
        color='green', 
        label='Electrolysis',
        linestyle='dotted',
    )
    plt.plot(
        - network.links_t.p1['H2 Fuel Cell'].groupby(network.snapshots.hour).mean(), 
        color='green', 
        label='Fuel Cell',
        linestyle='dashdot',
    )
    plt.legend(fancybox=True, shadow=True, loc='best')
    plt.xlabel("Hour of the day")
    plt.ylabel("MW")
    plt.xticks(rotation=45)

    if filename is not None: save_figure(filename)

    plt.show()

def plot_storage_season(networks: List[pypsa.Network], filename: str | None = None):
    for network in networks:
        plt.plot(
            network.stores_t.e['H2 Tank'],
            color='black', 
            label='H2 stored',
        )
        plt.legend(fancybox=True, shadow=True, loc='best')
        plt.xlabel("date")
        plt.ylabel("MWh")
        plt.xticks(rotation=45)

    if filename is not None: save_figure(filename)

    plt.show()

def plot_co2_limit_vs_price(co2_limits: np.ndarray, co2_prices: np.ndarray, filename: str | None = None):
    plt.plot(co2_limits/1e6, co2_prices, 'bo-')
    # 62.54 EUR/tonCO2 in 2023 (Net Effective Carbon Rates)
    # https://www.oecd.org/content/dam/oecd/en/topics/policy-sub-issues/carbon-pricing-and-energy-taxes/carbon-pricing-spain.pdf
    plt.axhline(y=62.54, color='r', linestyle='--', label='62.54 €/ton CO$_2$')
    plt.legend(fancybox=True, shadow=True, loc='best')
    plt.xlabel(r"CO$_2$ limit [Mt CO$_2$]")
    plt.ylabel(r"Price [€/Mton CO$_2$]")
    plt.title(r'Price vs CO$_2$ limit')

    if filename is not None: save_figure(filename)

    plt.show()


