# utils/utils.py

from matplotlib.ticker import MaxNLocator, MultipleLocator, FormatStrFormatter

class ColorChannelSet:
    """
    ColorChannelSet class manage color channels
    Args:
        name (str): channel names (e.g. vcmy, vrgb)
        color_name (list): list or channel color names (e.g. blue, reg, etc...)
        name (str): channel names (e.g. vcmy, vrgb)
        abcd_order (str): channel placeholder order (e.g. abcd)
    """
    def __init__(self, name: str, color_name: list[str], abcd_order="abcd"):

        self.name = name  # 'vrgb' or 'vcmy'
        self.order = list(name)
        self.color_name = color_name  #e.g.  ['grey', 'red', 'green', 'blue']
        self.channel_to_abcd = dict(zip(self.order, abcd_order))
        self.abcd_to_channel = dict(zip(abcd_order, self.order))

    def get_color_name(self, channel: str) -> str:
        try:
            lowchannel = str(channel.lower)
            idx = self.order.index(lowchannel)
            return self.color_name[idx]
        except ValueError:
            return channel

    def abcd_key(self, channel: str) -> str:
        return self.channel_to_abcd.get(channel) or ""

    def channel_from_abcd(self, abcd: str) -> str:
        return self.abcd_to_channel.get(abcd) or ""


def draw_curve_graph(
    ax,
    canvas,
    curves: dict,
    title: str = "",
    xlabel: str = "X",
    ylabel: str = "Y",
    show_legend: bool = True,
    nb_x_ticks: int = 21,
    allow_negative: bool = False
):
    """
    Draw multiple curves on a matplotlib axis.

    Args:
        ax (matplotlib.axes.Axes): The axis to draw on.
        canvas (FigureCanvas): The canvas to refresh.
        curves (dict): Dict[label] = {"y": [...], "color": "red", "x": [...], "linestyle": "-"}.
        title (str): Plot title.
        xlabel (str): X-axis label.
        ylabel (str): Y-axis label.
        show_legend (bool): Whether to show the legend.
        nb_x_ticks (int): number of x-axis ticks.
        allow_negative (bool): allow negative ticks
    """
    ax.clear()
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(True, linestyle="--", linewidth=0.5, alpha=0.2)

    global_ymin, global_ymax = float("inf"), float("-inf")
    x_is_string = False
    x_labels = None

    curve_count = 0
    for label, data in curves.items():
        y_vals = data.get("y", [])
        x_vals = data.get("x", [i + 1 for i in range(len(y_vals))])
        color = data.get("color", None)
        linestyle = data.get("linestyle", "-")

        if not x_vals or not y_vals:
            continue

        if isinstance(x_vals[0], str):
            x_is_string = True
            if x_labels is None:
                x_labels = x_vals
            x_vals = list(range(len(x_vals)))

        ax.plot(x_vals, y_vals, marker=".", label=label, color=color, linestyle=linestyle, alpha=0.8)

        global_ymin = min(global_ymin, min(y_vals))
        global_ymax = max(global_ymax, max(y_vals))

        curve_count += 1
    
    if curve_count == 0:
        print(f"No data to draw in graph titled: {title}")
        canvas.draw()
        return

    # Ajustement des limites Y et des ticks
    y_span = global_ymax - global_ymin
    if y_span <= 0.05:
        step = 0.01
    elif y_span <= 0.2:
        step = 0.02
    elif y_span <= 0.5:
        step = 0.05
    elif y_span <= 1:
        step = 0.1
    elif y_span <= 2:
        step = 0.2
    else:
        step = round(y_span / 10, 1)

    ymin_new = step * (global_ymin // step)
    ymax_new = step * ((global_ymax // step) + 1)
    maxlow = 0.0 if not allow_negative else float("-inf")

    ax.set_ylim(max(maxlow, ymin_new), ymax_new)

    ax.yaxis.set_major_locator(MultipleLocator(base=step))
    ax.yaxis.set_major_formatter(FormatStrFormatter('%.2f'))
    ax.yaxis.set_minor_locator(MultipleLocator(step / 10))
    ax.tick_params(axis='y', which='minor', length=3, width=0.5, color='#999')
    ax.tick_params(axis='y', which='major', length=6, width=1.0)

    if x_is_string and x_labels:
        ax.set_xticks(range(len(x_labels)))
        ax.set_xticklabels(x_labels, rotation=45)
    else:
        ax.set_xlim(1, nb_x_ticks)
        ax.set_xticks(range(1, nb_x_ticks + 1))

    if show_legend:
        ax.legend()
    canvas.draw()