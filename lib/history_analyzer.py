from typing import List, Dict
from statistics import mean
from datetime import datetime
from model.measurement_set import MeasurementSet
from lib.gamma import GammaAnalyzer


class HistoryAnalyzer:
    def __init__(self, reference: MeasurementSet, measurements: List[MeasurementSet]):
        self.reference = reference
        self.measurements = sorted(measurements, key=lambda m: m.date)

    def get_dates(self) -> List[datetime]:
        return [m.date for m in self.measurements]

    def get_average_curve(self, channel: str) -> List[float]:
        grouped = zip(*[m.curves[channel].values for m in self.measurements if channel in m.curves])
        return [mean(point_group) for point_group in grouped]

    def get_reference_curve(self, channel: str) -> List[float]:
        return self.reference.curves[channel].values if channel in self.reference.curves else [0.0]*21

    def get_gamma_evolution(self) -> Dict[str, List[float]]:
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
        result = {"R": [], "G": [], "B": []}
        for m in self.measurements:
            for channel in result:
                curve = m.curves.get(channel)
                result[channel].append(min(curve.values) if curve else None)
        return result

    def get_dmax_evolution(self) -> Dict[str, List[float]]:
        result = {"R": [], "G": [], "B": []}
        for m in self.measurements:
            for channel in result:
                curve = m.curves.get(channel)
                result[channel].append(max(curve.values) if curve else None)
        return result