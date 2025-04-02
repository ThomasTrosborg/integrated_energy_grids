import matplotlib.pyplot as plt

def plot_series(network, ts: int = 180*24):
    te = ts + 96
    plt.plot(network.loads_t.p['load'][ts:te], color='black', label='demand')
    plt.plot(network.generators_t.p['onshorewind'][ts:te], color='blue', label='onshore wind')
    plt.plot(network.generators_t.p['solar'][ts:te], color='orange', label='solar')
    plt.plot(network.generators_t.p['OCGT'][ts:te], color='brown', label='gas (OCGT)')
    plt.legend(fancybox=True, shadow=True, loc='best')

def plot_electricity_mix(network):
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

    plt.title('Electricity mix', y=1.07)