import matplotlib.pyplot as plt
import pathlib
import numpy as np
import pypsa
from typing import List, Tuple

LABELS = ['onshore wind', 'solar', 'OCGT']

def save_figure(filename):
    filepath = str(pathlib.Path(__file__).parent.resolve()) + "/results/" + filename
    plt.tight_layout()
    plt.savefig(filepath, dpi=300)

def plot_series(network, ts: int = 0, filename: str | None = None):
    te = ts + 96
    plt.plot(network.loads_t.p['load'][ts:te], color='black', label='demand')
    plt.plot(network.generators_t.p['onshore wind'][ts:te], color='blue', label='onshore wind')
    plt.plot(network.generators_t.p['solar'][ts:te], color='orange', label='solar')
    plt.plot(network.generators_t.p['OCGT'][ts:te], color='brown', label='gas (OCGT)')
    plt.legend(fancybox=True, shadow=True, loc='best')
    plt.xlabel("Time")
    plt.ylabel("MW")
    plt.xticks(rotation=45)

    if filename is not None: save_figure(filename)

    plt.show()

def plot_electricity_mix(network, filename: str | None = None):
    sizes = [network.generators_t.p['onshore wind'].sum(),
            network.generators_t.p['solar'].sum(),
            network.generators_t.p['OCGT'].sum()]

    colors=['blue', 'orange', 'brown']

    plt.pie(sizes,
            colors=colors,
            labels=LABELS,
            wedgeprops={'linewidth':0})
    plt.axis('equal')

    plt.title('Electricity mix')

    if filename is not None: save_figure(filename)

    plt.show()

def plot_duration_curves(network, filename: str | None = None):
    dur_curves = [network.generators_t.p[label].sort_values(ascending=False).values for label in LABELS]
    # capacities = [network.generators_t.p_nom_opt[label] for label in LABELS]
    colors=['blue', 'orange', 'brown']
    
    for ix in range(len(LABELS)):
        plt.plot(range(len(dur_curves[ix])), dur_curves[ix],
                color=colors[ix],
                label=LABELS[ix])
    plt.plot(range(len(dur_curves[ix])), network.loads_t.p['load'].sort_values(ascending=False).values, color='black', label='demand')

    plt.title('Duration Curves')
    plt.legend()
    plt.xlabel("Duration (hours/yr)")
    plt.ylabel("MW")

    if filename is not None: save_figure(filename)

    plt.show()

def plot_generation_mixes(network_sols, co2_limits, filename: str | None = None):
    colors=['blue', 'orange', 'brown']
    mixes = np.array(network_sols).T
    for ix, label in enumerate(LABELS):
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
