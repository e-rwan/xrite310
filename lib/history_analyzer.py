# lib/history_analyser.py

from typing import List, Dict
from statistics import mean
from datetime import datetime
from model.measurement_set import MeasurementSet
from lib.gamma import GammaAnalyzer


CHANNEL_DISPLAY_ORDER = ("V", "R", "G", "B", "C", "M", "Y")


class HistoryAnalyzer:

    """Analyzes historical measurement data to track changes in curves and gamma values.

    This class handles a collection of measurement sets, allowing for the comparison
    of these measurements against a reference. It provides methods to analyze and
    extract trends in gamma, minimum, and maximum density values over time.

    Attributes:
        reference (MeasurementSet): The baseline measurement set for comparison.
        measurements (List[MeasurementSet]): A chronologically sorted list of measurement sets.
    """


    def __init__(self, reference: MeasurementSet, measurements: List[MeasurementSet]):
        """Initializes HistoryAnalyzer with reference and a list of measurements.

        Args:
            reference (MeasurementSet): The reference measurement set.
            measurements (List[MeasurementSet]): List of measurement sets to analyze.
        """
        self.reference = reference
        self.measurements = sorted(measurements, key=lambda m: m.date)


    def get_dates(self) -> List[datetime]:
        """Returns the dates of the measurement sets.

        Returns:
            List[datetime]: A list of dates from the measurement sets.
        """
        return [m.date for m in self.measurements]


    def get_average_curve(self, channel: str) -> List[float]:
        """Calculates the average curve values for a given channel.

        Args:
            channel (str): The color channel ('R', 'G', 'B').

        Returns:
            List[float]: The average curve values for the specified channel.
        """
        grouped = zip(*[m.curves[channel].values for m in self.measurements if channel in m.curves])
        return [mean(point_group) for point_group in grouped]


    def get_reference_curve(self, channel: str) -> List[float]:
        """Retrieves the reference curve values for a specified channel.

        Args:
            channel (str): The color channel ('R', 'G', 'B').

        Returns:
            List[float]: The reference curve values, or a list of zeros if the channel is absent.
        """
        return self.reference.curves[channel].values if channel in self.reference.curves else [0.0]*21


    def _get_channels(self) -> List[str]:
        """Returns every available channel found in the reference or measurements."""
        channels = set(self.reference.curves.keys())
        for measurement in self.measurements:
            channels.update(measurement.curves.keys())

        ordered_channels = [channel for channel in CHANNEL_DISPLAY_ORDER if channel in channels]
        remaining_channels = sorted(channel for channel in channels if channel not in CHANNEL_DISPLAY_ORDER)
        return ordered_channels + remaining_channels


    def _get_gamma_metric_evolution(self, metric_name: str) -> Dict[str, List[float]]:
        """Tracks the evolution of a gamma-reading metric across measurements."""
        result = {channel: [] for channel in self._get_channels()}
        analyzer = GammaAnalyzer()

        for m in self.measurements:
            for channel in result:
                curve = m.curves.get(channel)
                if curve:
                    reading = analyzer.get_gamma_from_values(curve.values)
                    result[channel].append(getattr(reading, metric_name, None))
                else:
                    result[channel].append(None)
        return result



    def get_gamma_evolution(self) -> Dict[str, List[float]]:
        """Tracks the evolution of gamma values across measurements.

        Returns:
            Dict[str, List[float]]: A dictionary with gamma evolutions for each channel.
        """
        return self._get_gamma_metric_evolution("gamma")


    def get_ld_evolution(self) -> Dict[str, List[float]]:
        """Tracks the evolution of LD values across measurements."""
        return self._get_gamma_metric_evolution("ld")


    def get_md_evolution(self) -> Dict[str, List[float]]:
        """Tracks the evolution of MD values across measurements."""
        return self._get_gamma_metric_evolution("md")


    def get_hd_evolution(self) -> Dict[str, List[float]]:
        """Tracks the evolution of HD values across measurements."""
        return self._get_gamma_metric_evolution("hd")


    def get_contrast_evolution(self) -> Dict[str, List[float]]:
        """Tracks the evolution of contrast values across measurements."""
        result = {channel: [] for channel in self._get_channels()}
        analyzer = GammaAnalyzer()

        for m in self.measurements:
            for channel in result:
                curve = m.curves.get(channel)
                if not curve:
                    result[channel].append(None)
                    continue

                reading = analyzer.get_gamma_from_values(curve.values)
                if reading.hd is None or reading.ld is None:
                    result[channel].append(None)
                else:
                    result[channel].append(reading.hd - reading.ld)
        return result



    def get_dmin_evolution(self) -> Dict[str, List[float]]:
        """Determines the evolution of minimum density values for each channel.

        Returns:
            Dict[str, List[float]]: A dictionary with minimum density evolution for each channel.
        """
        result = {channel: [] for channel in self._get_channels()}
        for m in self.measurements:
            for channel in result:
                curve = m.curves.get(channel)
                result[channel].append(min(curve.values) if curve else None)
        return result



    def get_dmax_evolution(self) -> Dict[str, List[float]]:
        """Determines the evolution of maximum density values for each channel.

        Returns:
            Dict[str, List[float]]: A dictionary with maximum density evolution for each channel.
        """
        result = {channel: [] for channel in self._get_channels()}
        for m in self.measurements:
            for channel in result:
                curve = m.curves.get(channel)
                result[channel].append(max(curve.values) if curve else None)
        return result



    def get_d11_evolution(self) -> Dict[str, List[float]]:
        """Determines the evolution of D-11 values for each channel."""
        result = {channel: [] for channel in self._get_channels()}
        for m in self.measurements:
            for channel in result:
                curve = m.curves.get(channel)
                result[channel].append(curve.values[10] if curve and len(curve.values) > 10 else None)
        return result