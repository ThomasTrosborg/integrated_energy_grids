import matplotlib.pyplot as plt
import pathlib
import numpy as np

def save_figure(filename):
    filepath = str(pathlib.Path(__file__).parent.resolve()) + "/results/" + filename
    plt.tight_layout()
    plt.savefig(filepath, dpi=300)

def plot_series(network, ts: int = 180*24, filename: str = None):
    te = ts + 96
    plt.plot(network.loads_t.p['load'][ts:te], color='black', label='demand')
    plt.plot(network.generators_t.p['onshorewind'][ts:te], color='blue', label='onshore wind')
    plt.plot(network.generators_t.p['solar'][ts:te], color='orange', label='solar')
    plt.plot(network.generators_t.p['OCGT'][ts:te], color='brown', label='gas (OCGT)')
    plt.legend(fancybox=True, shadow=True, loc='best')
    plt.xlabel("Time")
    plt.ylabel("MW")
    plt.xticks(rotation=45)

    if filename is not None: save_figure(filename)

    plt.show()

def plot_electricity_mix(network, filename: str = None):
    labels = ['onshore wind',
            'solar',
            'gas (OCGT)']
    sizes = [network.generators_t.p['onshorewind'].sum(),
            network.generators_t.p['solar'].sum(),
            network.generators_t.p['OCGT'].sum()]

    colors=['blue', 'orange', 'brown']

    plt.pie(sizes,
            colors=colors,
            labels=labels,
            wedgeprops={'linewidth':0})
    plt.axis('equal')

    plt.title('Electricity mix')

    if filename is not None: save_figure(filename)

    plt.show()

def plot_duration_curves(network, filename: str = None):
    labels = ['onshorewind',
            'solar',
            'OCGT']
    dur_curves = [network.generators_t.p[label].sort_values(ascending=False).values for label in labels]
    # capacities = [network.generators_t.p_nom_opt[label] for label in labels]
    colors=['blue', 'orange', 'brown']
    
    for ix in range(len(labels)):
        plt.plot(range(len(dur_curves[ix])), dur_curves[ix],
                color=colors[ix],
                label=labels[ix])
    plt.plot(range(len(dur_curves[ix])), network.loads_t.p['load'].sort_values(ascending=False).values, color='black', label='demand')

    plt.title('Duration Curves')
    plt.legend()
    plt.xlabel("Duration (hours/yr)")
    plt.ylabel("MW")

    if filename is not None: save_figure(filename)

    plt.show()

def plot_generation_mixes(network_sols, co2_limits, filename: str = None):
    labels = ['onshorewind',
            'solar',
            'OCGT']
    colors=['blue', 'orange', 'brown']
    mixes = np.array(network_sols).T
    for ix, label in enumerate(labels):
        plt.plot(co2_limits, mixes[ix], '--bo', label = label, color = colors[ix])
    plt.xlabel(r"CO2 limit (Mt CO$_2$)")
    plt.xticks(co2_limits, [str(int(x/1e6)) for x in co2_limits])
    plt.ylabel(r"Generation (MWh)")
    plt.legend()
    plt.title(r'Generation mixes under emissions limitations')

    if filename is not None: save_figure(filename)

    plt.show()
