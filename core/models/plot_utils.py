import matplotlib.pyplot as plt


class PlotSettings:
    rows: int = 2
    cols: int = 3
    index: int = 1
    
    x: list[float]
    y: list[list[float]]
    labels: list[str]

    yBottom: float = 0
    yTop: float

    xLabel: str
    yLabel: str
    title: str
    suptitle: str

    fileName: str = 'plot'
    fileIndex: int = 1

    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols


def get_color(i: int = 0):

    colors = ['b', 'g', 'r', 'c', 'm', 'y', 'k', 'w']
    linestyles = ['-', '--', '-.', ':']

    color = colors[i % len(colors)]
    linestyle = linestyles[i % len(linestyles)]

    style = color + linestyle
    return style


def create_figure(suptitle): 

    plt.figure(figsize=(16, 12))
    
    plt.suptitle(suptitle, fontsize=14, fontweight='bold')
    

def save_figure(file_name):

    plt.tight_layout()

    plt.savefig(f'{file_name}.png', dpi=300, bbox_inches='tight')
    plt.savefig(f'{file_name}.pdf', bbox_inches='tight')

    print("\n✅ Графики сохранены в файлы")



def create_plot(settings: PlotSettings):
    
    if (settings.index > settings.rows * settings.cols):

        save_figure(f'{settings.fileName} ({settings.fileIndex})')
        create_figure(settings.suptitle)
        
        settings.index = 1
        settings.fileIndex += 1


    ax = plt.subplot(settings.rows, settings.cols, settings.index)
    
    x = settings.x

    
    for i in range(len(settings.y)):
        
        y = settings.y[i]
        label = settings.labels[i]

        style = get_color(i)

        ax.plot(x, y, style, linewidth=2.5, label=label)
    
    ax.set_xlabel(settings.xLabel)
    ax.set_ylabel(settings.yLabel)
    ax.set_title(settings.title)
    
    ax.grid(True, alpha=0.3)
    ax.legend()

    max_value = max(map(max, settings.y))

    ax.set_ylim(settings.yBottom, max_value*1.05)

    return ax


