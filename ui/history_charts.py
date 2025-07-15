# ui/history_charts.py
from utils.plot_utils import draw_curve_graph, build_curve_data
from lib.gamma import GammaAnalyzer


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
            "color": {"r": "red", "g": "green", "b": "blue"}.get(ch.lower()),
            "linestyle": "-"
        }
        for ch, values in gamma_data.items()
    }
    for ch, val in gamma_ref.items():
        curves[f"Réf {ch.upper()}"] = {
            "x": dates,
            "y": [val] * len(dates),
            "color": {"r": "red", "g": "green", "b": "blue"}.get(ch.lower()),
            "linestyle": "--"
        }
    draw_curve_graph(
        ax=ax,
        canvas=canvas,
        curves=curves,
        title="Évolution des gammas",
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
        title="Dmin RGB",
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
        title="Dmax RGB",
        xlabel="Date",
        ylabel="Dmax",
        nb_x_ticks=len(dates)
    )
