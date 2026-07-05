# ui/history_charts.py

from utils.plot_utils import draw_curve_graph, build_curve_data
from lib.gamma import GammaAnalyzer


CHANNEL_COLORS = {
    "v": "grey",
    "r": "red",
    "g": "green",
    "b": "blue",
    "c": "cyan",
    "m": "magenta",
    "y": "gold",
}


def _get_channel_color(channel: str):
    """Returns the plotting color associated with a channel."""
    return CHANNEL_COLORS.get(channel.lower()) if channel else None


def _get_ref_gamma_reading_value(values, attribute: str):
    """Returns a gamma-reading attribute from a reference curve."""
    reading = GammaAnalyzer().get_gamma_from_values(values)
    return getattr(reading, attribute, None)


def _get_ref_contrast_value(values):
    """Returns the reference contrast value computed as HD - LD."""
    reading = GammaAnalyzer().get_gamma_from_values(values)
    if reading.hd is None or reading.ld is None:
        return None
    return reading.hd - reading.ld


def draw_gamma_plot(ax, canvas, analyzer, ref, dates):
    """Plots the evolution of gamma values over time.

    This function calculates and plots both the reference gamma values and the
    evolution of gamma values over the given dates for each color channel.

    Args:
        ax: The matplotlib axis to plot on.
        canvas: The canvas associated with the plot for rendering updates.
        analyzer: The HistoryAnalyzer instance to get gamma data from.
        ref: The reference measurement set for comparison.
        dates: A list of date strings corresponding to each measurement.
    """
    gamma_data = analyzer.get_gamma_evolution()
    gamma_ref = {}
    gamma_tool = GammaAnalyzer()

    for ch, curve in ref.curves.items():
        try:
            reading = gamma_tool.get_gamma_from_values(curve.values)
            gamma_ref[ch] = reading.gamma
        except Exception as e:
            print(f"Erreur gamma ref {ch}: {e}")
    curves = {
        ch: {
            "x": dates,
            "y": values,
            "color": _get_channel_color(ch),
            "linestyle": "-"
        }
        for ch, values in gamma_data.items()
    }
    for ch, val in gamma_ref.items():
        curves[f"Réf {ch.upper()}"] = {
            "x": dates,
            "y": [val] * len(dates),
            "color": _get_channel_color(ch),
            "linestyle": "--"
        }
    draw_curve_graph(
        ax=ax,
        canvas=canvas,
        curves=curves,
        title="Évolution du gamma",
        xlabel="Date",
        ylabel="Gamma",
        nb_x_ticks=len(dates)
    )


def draw_dmin_plot(ax, canvas, analyzer, ref, dates):
    """Plots the evolution of D-min values over time.

    This function generates and plots the minimum density (Dmin) evolution
    based on measurement data compared to reference levels.

    Args:
        ax: The matplotlib axis to plot on.
        canvas: The canvas associated with the plot for rendering updates.
        analyzer: The HistoryAnalyzer instance to get Dmin data from.
        ref: The reference measurement set for comparison.
        dates: A list of date strings corresponding to each measurement.
    """
    curves = build_curve_data(
        analyzer_func=analyzer.get_dmin_evolution,
        dates=dates,
        ref=ref,
        ref_func=min,
        ylabel="Dmin",
        linestyle="-",
        ref_linestyle="--"
    )
    draw_curve_graph(
        ax=ax,
        canvas=canvas,
        curves=curves,
        title="Dmin",
        xlabel="Date",
        ylabel="Dmin",
        nb_x_ticks=len(dates)
    )


def draw_dmax_plot(ax, canvas, analyzer, ref, dates):
    """Plots the evolution of D-max values over time.

    This function generates and plots the maximum density (Dmax) evolution
    based on measurement data compared to reference levels.

    Args:
        ax: The matplotlib axis to plot on.
        canvas: The canvas associated with the plot for rendering updates.
        analyzer: The HistoryAnalyzer instance to get Dmax data from.
        ref: The reference measurement set for comparison.
        dates: A list of date strings corresponding to each measurement.
    """
    curves = build_curve_data(
        analyzer_func=analyzer.get_dmax_evolution,
        dates=dates,
        ref=ref,
        ref_func=max,
        ylabel="Dmax",
        linestyle="-",
        ref_linestyle="--"
    )
    draw_curve_graph(
        ax=ax,
        canvas=canvas,
        curves=curves,
        title="Dmax",
        xlabel="Date",
        ylabel="Dmax",
        nb_x_ticks=len(dates)
    )


def draw_d11_plot(ax, canvas, analyzer, ref, dates):
    """Plots the evolution of D-11 values over time.

    This function generates and plots the density of density 11 (D-11) evolution
    based on measurement data compared to reference levels.

    Args:
        ax: The matplotlib axis to plot on.
        canvas: The canvas associated with the plot for rendering updates.
        analyzer: The HistoryAnalyzer instance to get D11 data from.
        ref: The reference measurement set for comparison.
        dates: A list of date strings corresponding to each measurement.
    """
    curves = build_curve_data(
        analyzer_func=analyzer.get_d11_evolution,
        dates=dates,
        ref=ref,
        ref_func=lambda values: values[10],
        ylabel="D11",
        linestyle="-",
        ref_linestyle="--"
    )
    draw_curve_graph(
        ax=ax,
        canvas=canvas,
        curves=curves,
        title="D11",
        xlabel="Date",
        ylabel="D11",
        nb_x_ticks=len(dates)
    )


def draw_ld_plot(ax, canvas, analyzer, ref, dates):
    """Plots the evolution of LD values over time."""
    curves = build_curve_data(
        analyzer_func=analyzer.get_ld_evolution,
        dates=dates,
        ref=ref,
        ref_func=lambda values: _get_ref_gamma_reading_value(values, "ld"),
        ylabel="LD",
        linestyle="-",
        ref_linestyle="--"
    )
    draw_curve_graph(
        ax=ax,
        canvas=canvas,
        curves=curves,
        title="LD",
        xlabel="Date",
        ylabel="LD",
        nb_x_ticks=len(dates)
    )


def draw_md_plot(ax, canvas, analyzer, ref, dates):
    """Plots the evolution of MD values over time."""
    curves = build_curve_data(
        analyzer_func=analyzer.get_md_evolution,
        dates=dates,
        ref=ref,
        ref_func=lambda values: _get_ref_gamma_reading_value(values, "md"),
        ylabel="MD",
        linestyle="-",
        ref_linestyle="--"
    )
    draw_curve_graph(
        ax=ax,
        canvas=canvas,
        curves=curves,
        title="MD",
        xlabel="Date",
        ylabel="MD",
        nb_x_ticks=len(dates)
    )


def draw_hd_plot(ax, canvas, analyzer, ref, dates):
    """Plots the evolution of HD values over time."""
    curves = build_curve_data(
        analyzer_func=analyzer.get_hd_evolution,
        dates=dates,
        ref=ref,
        ref_func=lambda values: _get_ref_gamma_reading_value(values, "hd"),
        ylabel="HD",
        linestyle="-",
        ref_linestyle="--"
    )
    draw_curve_graph(
        ax=ax,
        canvas=canvas,
        curves=curves,
        title="HD",
        xlabel="Date",
        ylabel="HD",
        nb_x_ticks=len(dates)
    )


def draw_contrast_plot(ax, canvas, analyzer, ref, dates):
    """Plots the evolution of contrast values over time."""
    curves = build_curve_data(
        analyzer_func=analyzer.get_contrast_evolution,
        dates=dates,
        ref=ref,
        ref_func=_get_ref_contrast_value,
        ylabel="Contrast",
        linestyle="-",
        ref_linestyle="--"
    )
    draw_curve_graph(
        ax=ax,
        canvas=canvas,
        curves=curves,
        title="Contrast",
        xlabel="Date",
        ylabel="Contrast",
        nb_x_ticks=len(dates)
    )
