# utils/plot_utils.py

from matplotlib.ticker import MultipleLocator, FormatStrFormatter
from typing import Callable, Optional

from model.measurement_set import MeasurementSet

class ColorChannelSet:
    """
    Manages color channels for visualization purposes.

    Attributes:
        name (str): The name of the channel set (e.g., 'vcmy', 'vrgb').
        color_name (list[str]): A list of color names corresponding to each channel (e.g., ['grey', 'red', 'green', 'blue']).
        abcd_order (str): A string representing the placeholder order for channels (e.g., 'abcd').

    Methods:
        get_color_name(channel): Returns the color name associated with a given channel.
        abcd_key(channel): Gives the placeholder key associated with the channel.
        channel_from_abcd(abcd): Retrieves the channel name from its placeholder.
    """
    def __init__(self, name: str, color_name: list[str], abcd_order="abcd"):
        self.name = name  # 'vrgb' or 'vcmy'
        self.order = list(name)
        self.color_name = color_name  # e.g., ['grey', 'red', 'green', 'blue']
        self.channel_to_abcd = dict(zip(self.order, abcd_order))
        self.abcd_to_channel = dict(zip(abcd_order, self.order))

    def get_color_name(self, channel: str) -> str:
        """Returns the color name associated with a provided channel."""
        try:
            lowchannel = str(channel.lower())
            idx = self.order.index(lowchannel)
            return self.color_name[idx]
        except ValueError:
            return channel

    def abcd_key(self, channel: str) -> str:
        """Provides the placeholder key associated with the given channel."""
        return self.channel_to_abcd.get(channel, "")

    def channel_from_abcd(self, abcd: str) -> str:
        """Returns the channel name associated with a given placeholder key."""
        return self.abcd_to_channel.get(abcd, "")


def build_curve_data(
    analyzer_func: Callable[[], dict],
    dates: list[str],
    ref: Optional[MeasurementSet] = None,
    ref_func: Optional[Callable[[list[float]], float]] = None,
    ylabel: str = "",
    linestyle: str = "-",
    ref_linestyle: str = "--"
) -> dict:
    """
    Generates data for drawing a curve graph.

    Args:
        analyzer_func (Callable): A function that analyzes data, such as get_dmin_evolution().
        dates (list[str]): List of strings representing dates for the X-axis.
        ref (MeasurementSet, optional): Reference measurement set.
        ref_func (Callable, optional): Function to extract a reference value (min, max, etc.).
        ylabel (str): Label for the Y-axis.
        linestyle (str): Line style for the primary curve.
        ref_linestyle (str): Line style for the reference curve.

    Returns:
        dict: A dictionary containing curve data with keys 'x', 'y', 'color', and 'linestyle'.
    """
    data = analyzer_func()
    curves = {}

    for ch, values in data.items():
        curves[ch] = {
            "x": dates,
            "y": values,
            "color": {"r": "red", "g": "green", "b": "blue"}.get(ch.lower(), None),
            "linestyle": linestyle
        }

    if ref and ref_func:
        for ch in ref.curves:
            ref_val = ref_func(ref.curves[ch].values)
            curves[f"Réf {ch.upper()}"] = {
                "x": dates,
                "y": [ref_val] * len(dates),
                "color": {"r": "red", "g": "green", "b": "blue"}.get(ch.lower(), None),
                "linestyle": ref_linestyle
            }

    return curves


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
    Draws multiple curves on a given matplotlib axis.

    Args:
        ax (matplotlib.axes.Axes): The axis to draw the curves on.
        canvas (FigureCanvas): The canvas object for refreshing the plot.
        curves (dict): Dictionary where keys are legend labels and values are dicts with 'x', 'y', 'color', and 'linestyle'.
        title (str): Title of the plot.
        xlabel (str): X-axis label.
        ylabel (str): Y-axis label.
        show_legend (bool): Flag to indicate if the legend should be shown.
        nb_x_ticks (int): Number of ticks on the X-axis.
        allow_negative (bool): Allows negative ticks if true.

    Returns:
        None
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
        raw_y_vals = data.get("y", [])
        raw_x_vals = data.get("x", [i + 1 for i in range(len(raw_y_vals))])
        # Filter out invalid values
        valid_points = [(x, y) for x, y in zip(raw_x_vals, raw_y_vals) if isinstance(y, (int, float))]
        if not valid_points:
            continue
        x_vals, y_vals = zip(*valid_points)

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

    # Adjust y ticks
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
