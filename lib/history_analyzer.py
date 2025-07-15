from typing import List, Dict
from statistics import mean
from datetime import datetime
from model.measurement_set import MeasurementSet
from lib.gamma import GammaAnalyzer


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


    def get_gamma_evolution(self) -> Dict[str, List[float]]:
        """Tracks the evolution of gamma values across measurements.

        Returns:
            Dict[str, List[float]]: A dictionary with gamma evolutions for each channel.
        """
        gamma_evolution = {"R": [], "G": [], "B": []}
        analyzer = GammaAnalyzer()

        for m in self.measurements:
            for channel in gamma_evolution:
                curve = m.curves.get(channel)
                if curve:
                    reading = analyzer.get_gamma_from_values(curve.values)
                    gamma_evolution[channel].append(reading.gamma)
                else:
                    gamma_evolution[channel].append(None)
        return gamma_evolution


    def get_dmin_evolution(self) -> Dict[str, List[float]]:
        """Determines the evolution of minimum density values for each channel.

        Returns:
            Dict[str, List[float]]: A dictionary with minimum density evolution for each channel.
        """
        result = {"R": [], "G": [], "B": []}
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
        result = {"R": [], "G": [], "B": []}
        for m in self.measurements:
            for channel in result:
                curve = m.curves.get(channel)
                result[channel].append(max(curve.values) if curve else None)
        return result