import matplotlib.pyplot as plt
import pathlib
import numpy as np
import pandas as pd
import pypsa
from typing import List, Dict
from brokenaxes import brokenaxes

import seaborn as sns

sns.set_theme(style="whitegrid")
# Set the default font size for all plots
plt.rcParams.update({'font.size': 12})
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['xtick.labelsize'] = 10
plt.rcParams['ytick.labelsize'] = 10

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
    te = ts + 7*24
    plt.figure(figsize=(10, 2.5))
    for ix, load in enumerate(REFERENCES['LOADS']):
        plt.plot(network.loads_t.p[load][ts:te], color=COLORS['LOADS'][ix], label=LABELS['LOADS'][ix])
    for ix, gen in enumerate(REFERENCES['GENERATORS']):
        plt.plot(network.generators_t.p[gen][ts:te], color=COLORS['GENERATORS'][ix], label=LABELS['GENERATORS'][ix])
    for ix, link in enumerate(REFERENCES['LINKS']):
        plt.plot(-network.links_t.p1[link][ts:te], color=COLORS['LINKS'][ix], label=LABELS['LINKS'][ix])
    plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), fancybox=True, ncol=5)
    plt.ylabel("MW")
    plt.xlim(network.snapshots[ts], network.snapshots[te-1])
    plt.ylim(0, 1.02 * network.loads_t.p[load].max())
    plt.xticks(rotation=0)

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
        dur_curves += [-network.links_t.p1[link].sort_values(ascending=True).values]
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

def plot_capacity_variation_under_varying_co2_limits(network_sols, co2_limits, system_costs, filename: str | None = None):
    mixes = np.array(network_sols).T*1e-3 # in GW
    
    colors = []
    labels = []
    for ix, gen in enumerate(REFERENCES['GENERATORS']):
        colors += [COLORS['GENERATORS'][ix]]
        labels += [LABELS['GENERATORS'][ix]]
    for ix, link in enumerate(REFERENCES['LINKS']):
        colors += [COLORS['LINKS'][ix]]
        labels += [LABELS['LINKS'][ix]]
    fig, (ax_upper, ax_lower) = plt.subplots(2, 1, sharex=True, figsize=(8, 6),
                               gridspec_kw={'height_ratios': [0.7, 2]})
    ax_upper.grid(False)
    ax_lower.grid(False)
    ax_upper.spines['bottom'].set_visible(False)
    ax_lower.spines['top'].set_visible(False)
    ax_upper.tick_params(labelbottom=False)
    d = .01  # size of diagonal lines
    kwargs = dict(transform=ax_upper.transAxes, color='k', clip_on=False)
    ax_upper.plot((-d, +d), (-d, +d), **kwargs)        # top-left diagonal
    ax_upper.plot((1 - d, 1 + d), (-d, +d), **kwargs)  # top-right diagonal

    kwargs.update(transform=ax_lower.transAxes)
    ax_lower.plot((-d, +d), (1 - d, 1 + d), **kwargs)  # bottom-left diagonal
    ax_lower.plot((1 - d, 1 + d), (1 - d, 1 + d), **kwargs)  # bottom-right diagonal

    ax_lower.set_xlabel(r"CO2 limit (Mt CO$_2$)")
    ax_lower.set_xticks(co2_limits, [str(int(x/1e6)) for x in co2_limits])

    ylims = [[(0.9*np.max(mixes), 1.05*np.max(mixes)),  (0.9*np.max(system_costs), 1.1*np.max(system_costs))],
             [(0, 0.25*np.max(mixes)),  (0, 0.25*np.max(system_costs))]]
    for ix, ax in enumerate((ax_upper, ax_lower)):
        ax2 = ax.twinx()
        if ix == 1:
            ax.set_ylabel('Capacity (GW)')
            ax2.set_ylabel('System cost (M€)')

        ax2.plot(co2_limits, system_costs, '--o', label='System cost', color='black')

        for ix2, label in enumerate(labels):
            ax.plot(co2_limits, mixes[ix2], '--o', label=label, color=colors[ix2])
        
        ax.set_ylim(ylims[ix][0])
        ax2.set_ylim(ylims[ix][1])
    
    h, l = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax_lower.legend(h + h2, l + l2, loc='best', fancybox=True)

    if filename is not None: save_figure(filename)

    plt.show() 

def plot_weather_variability(network_sols, filename: str = None):
    colors = []
    labels = []
    for ix, gen in enumerate(REFERENCES['GENERATORS']):
        colors += [COLORS['GENERATORS'][ix]]
        labels += [LABELS['GENERATORS'][ix]]
    mixes = np.array(network_sols)
    boxprops = dict(color='black')  # Default box properties
    medianprops = dict(color='red')  # Default median line properties

    fig, ax = plt.subplots()

    for i, color in enumerate(colors):
        ax.boxplot(
            mixes[:, i],
            positions=[i + 1],
            patch_artist=True,
            boxprops=dict(facecolor=color, color=color),
            medianprops=medianprops,
            label=labels[i],
            showmeans=True,
            meanprops=dict(marker='o', markerfacecolor='blue', markersize=5, markeredgecolor='black'),
        )

    mean_handle = ax.plot([], [], color="blue", marker='o', linestyle='None',
                         markersize=8, label='Mean')
    median_handle = ax.plot([], [], color="red", linestyle='-', label='Median')
    # Add legend to the plot
    

    plt.xticks(ticks=range(1, len(labels) + 1), labels=labels)
    plt.ylim(0, 1.05 * max(mixes.flatten()))
    plt.xlabel(r"Generator technology")
    plt.ylabel(r"Capacity Variation (MW)")

    handles, labels = ax.get_legend_handles_labels()
    handles.append(mean_handle)
    labels.append('Mean')
    handles.append(median_handle)
    labels.append('Median')

    plt.legend(handles=handles, labels=labels, loc='best', fancybox=True, shadow=True)
    plt.title(r'Capacity mixes using different weather years')

    if filename is not None: save_figure(filename)
    plt.show()


def plot_storage_day(network: pypsa.Network, filename: str | None = None):
    network.generators_t.p[REFERENCES['GENERATORS']].groupby(network.snapshots.hour).mean().div(1e3).reindex(np.arange(0,25)).ffill().plot(drawstyle="steps-post")
    # (- network.links_t.p1["HDAM"]).groupby(network.snapshots.hour).mean().div(1e3).reindex(np.arange(0,25)).ffill().plot(drawstyle="steps-post", label="Dam Hydro")
    for store in ["DamWater", "PumpedHydro", "Battery", "H2"]:
        charge = (network.links.loc[network.links['bus1'] == store].index[0] if store != "DamWater" else [])
        discharge = network.links.loc[network.links['bus0'] == store].index[0]
        # plt.plot(
        #     (- network.links_t.p1[discharge].groupby(network.snapshots.hour).mean() if store != "DamWater" else 0) - network.links_t.p0[charge].groupby(network.snapshots.hour).mean(), 
        #     label=store,
        # )
        plt.step(
            x=network.links_t.p1[discharge].groupby(network.snapshots.hour).mean().div(1e3).reindex(np.arange(0,25)).ffill().index,
            y= (
                - network.links_t.p1[discharge].groupby(network.snapshots.hour).mean().div(1e3).reindex(np.arange(0,25)).ffill() 
                - (network.links_t.p0[charge].groupby(network.snapshots.hour).mean().div(1e3).reindex(np.arange(0,25)).ffill()  if store != "DamWater" else 0)
            ), 
            label=store,
            where='post',
        )
    plt.fill_between(
        x=network.loads_t.p['load'].groupby(network.snapshots.hour).mean().div(1e3).reindex(np.arange(0,25)).ffill().index,
        y1=network.loads_t.p['load'].groupby(network.snapshots.hour).mean().div(1e3).reindex(np.arange(0,25)).ffill(), 
        color='grey', 
        label='demand',
        alpha=0.5,
        step='post',
    )
    plt.legend(fancybox=True, loc='center left', bbox_to_anchor=(1, 0.5))
    plt.xlabel("Hour of the day")
    plt.ylabel("GW")
    plt.xticks(np.arange(25), np.arange(25), rotation=45)
    plt.xlim(
        network.loads_t.p['load'].groupby(network.snapshots.hour).mean().index[0], 
        network.loads_t.p['load'].groupby(network.snapshots.hour).mean().index[-1]+1,
    )

    if filename is not None: save_figure(filename)

    plt.show()

def plot_storage_season(network: pypsa.Network, filename: str | None = None):
    network.stores_t.e.groupby(network.stores_t.e.index.month).mean().div(1e3).plot()
    plt.legend(fancybox=True, shadow=True, loc='best')
    plt.xlabel("Month")
    plt.ylabel("Stored energy [GWh]")
    plt.xticks(np.arange(1,13), ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])
    plt.xlim(1, 12)

    if filename is not None: save_figure(filename)

    plt.show()

def capacity_mixes_storage(networks: Dict[str, pypsa.Network], filename: str | None = None):    
    # Create dataframe for the capacity mixes
    gen_capacities = pd.DataFrame(index=REFERENCES['GENERATORS'])
    objs = []
    for (name, network) in networks.items():
        gen_capacities[name] = network.generators.p_nom_opt[REFERENCES['GENERATORS']].values
        objs.append(network.objective/1e6) # in million EUR
    gen_capacities.loc["system cost"] = objs
    gen_capacities = gen_capacities.T*1e-3 # in GW

    # Plot the capacity mixes
    for color, label in zip(COLORS['GENERATORS'], REFERENCES['GENERATORS']):
        plt.plot(gen_capacities[label], '--o', color=color, label=label)
    # plt.plot(gen_capacities, style='--o', color=COLORS['GENERATORS'])
    # gen_capacities.plot(style='--o', color=COLORS['GENERATORS'], xticks=gen_capacities.index)
    plt.ylabel("Capacity [GW]")
    plt.xlabel("Scenario")
    plt.xticks(np.arange(len(gen_capacities)), gen_capacities.index)
    plt.legend()
    plt.title('Capacity Mixes')

    if filename is not None: save_figure(filename)

    plt.show()

def plot_co2_limit_vs_price(co2_limits: dict, co2_prices: dict, filename: str | None = None):
    for label in co2_limits.keys():
        plt.plot(co2_limits[label]/1e6, co2_prices[label], 'o-', label=label)
    # 62.54 EUR/tonCO2 in 2023 (Net Effective Carbon Rates)
    # https://www.oecd.org/content/dam/oecd/en/topics/policy-sub-issues/carbon-pricing-and-energy-taxes/carbon-pricing-spain.pdf
    plt.axhline(y=62.54, color='r', linestyle='--', label='62.54 €/ton CO$_2$')
    plt.legend(fancybox=True, shadow=True, loc='best')
    plt.xlabel(r"CO$_2$ limit [Mt CO$_2$]")
    plt.ylabel(r"Price [€/ton CO$_2$]")
    plt.yscale('log')
    plt.title(r'Price vs CO$_2$ limit')
    # plt.ylim(0, 500)

    # if filename is not None: save_figure(filename)

    plt.show()
