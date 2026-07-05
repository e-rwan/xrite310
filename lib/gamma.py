#lib/gamma.py

from dataclasses import dataclass
from typing import List, NamedTuple, Optional
from statistics import mean

STEP_VALUE = 0.15
HIGH_PCT = 0.2
LOW_PCT = 0.20
MIN_DIFF = 0.03
NUM_STEPS = 4


class Range(NamedTuple):
	"""Class to contain search or gamma range."""
	start: int
	end: int


@dataclass
class GammaReading:
	"""Class containing values related to gamma readings."""
	gamma: float
	step_value: float
	d_min: float
	d_max: float
	search_range: Range
	gamma_range: Range
	ld: Optional[float] = None
	md: Optional[float] = None
	hd: Optional[float] = None

	def __str__(self):
		ld = "--" if self.ld is None else f"{self.ld:.2f}"
		md = "--" if self.md is None else f"{self.md:.2f}"
		hd = "--" if self.hd is None else f"{self.hd:.2f}"
		return (
			f"gamma\t\t\t: {self.gamma:.2f}\n"
			f"step_value\t\t: {self.step_value:.2f}\n"
			f"d_min\t\t\t: {self.d_min:.2f}\n"
			f"d_max\t\t\t: {self.d_max:.2f}\n"
			f"LD\t\t\t: {ld}\n"
			f"MD\t\t\t: {md}\n"
			f"HD\t\t\t: {hd}\n"
			f"search_range\t\t: [{self.search_range.start} - {self.search_range.end}]\n"
			f"gamma_range\t\t: [{self.gamma_range.start} - {self.gamma_range.end}]"
		)



class GammaAnalyzer:
	"""Analyzes gamma values from a set of density readings."""

	def get_search_range(self, values: List[float], low_pct=LOW_PCT, high_pct=HIGH_PCT) -> Range:
		"""Calculates the index range to search for gamma analysis."""
		d_min = min(values)
		d_max = max(values)

		min_threshold = d_min + low_pct * (d_max - d_min)
		max_threshold = d_max - high_pct * (d_max - d_min)

		start = next((i for i, v in enumerate(values) if v > min_threshold), 0)
		end = next((i for i, v in enumerate(values) if v > max_threshold), len(values)) - 1

		start = max(1, start)
		end = min(len(values) - 1, end)

		return Range(start, end)

	def get_gamma_range(self, values: List[float], search_range: Range, num_steps=NUM_STEPS) -> Range:
		"""Finds the most linear range using the minimum sum of acceleration."""
		speeds = self.get_derivatives(values)
		accelerations = self.get_derivatives(speeds)

		best_start = search_range.start
		min_acc_sum = float("inf")

		for i in range(search_range.start, search_range.end - num_steps + 1):
			acc_sum = sum(abs(a) for a in accelerations[i:i + num_steps])
			if acc_sum < min_acc_sum:
				min_acc_sum = acc_sum
				best_start = i

		return Range(best_start, best_start + num_steps)

	def get_derivatives(self, values: List[float]) -> List[float]:
		"""Calculates central derivatives of a list."""
		n = len(values)
		derivatives = [0.0]
		for i in range(1, n - 1):
			derivatives.append(values[i + 1] - values[i - 1])
		derivatives.append(derivatives[-1])
		return derivatives

	def get_gamma(self, gamma_range: Range, values: List[float], step_value: float = STEP_VALUE) -> float:
		"""Computes the gamma value from the slope of the computed gamma range."""
		delta_y = values[gamma_range.end] - values[gamma_range.start]
		delta_x = (gamma_range.end - gamma_range.start) * step_value
		return delta_y / delta_x

	def get_density_for_step(self, values: List[float], step: int) -> Optional[float]:
		"""Returns the density for a 21-step wedge step number."""
		index = 21 - step
		if 0 <= index < len(values):
			return values[index]
		return None

	def mean_optional(self, values: List[Optional[float]]) -> Optional[float]:
		"""Returns the mean of non-None values."""
		filtered = [value for value in values if value is not None]
		return mean(filtered) if filtered else None


	def get_gamma_from_values(
		self,
		values: List[float],
		step_value: float = STEP_VALUE,
		low_pct=LOW_PCT,
		high_pct=HIGH_PCT,
		min_diff=MIN_DIFF,
	) -> GammaReading:
		"""Computes a detailed gamma reading from a list of values."""
		if len(values) < 4:
			raise ValueError("At least 4 values are needed")

		search_range = self.get_search_range(values, low_pct, high_pct)
		gamma_range = self.get_gamma_range(values, search_range)
		gamma = self.get_gamma(gamma_range, values, step_value)

		return GammaReading(
			gamma=gamma,
			step_value=step_value,
			d_min=min(values),
			d_max=max(values),
			search_range=Range(search_range.start + 1, search_range.end + 1),
			gamma_range=Range(gamma_range.start + 1, gamma_range.end + 1),
			ld=self.get_density_for_step(values, 14),
			md=self.get_density_for_step(values, 8),
			hd=self.get_density_for_step(values, 4),
		)


	def get_gamma_from_curve_data(
		self,
		data: dict[str, list[Optional[float]]],
		visible_channels: list[str],
		step_value: float = STEP_VALUE,
	) -> dict[str, GammaReading]:
		"""Computes gamma readings from curve data for each visible channel and combined channels."""
		if not visible_channels:
			return {}

		results: dict[str, GammaReading] = {}
		results_ref: dict[str, GammaReading] = {}

		for ch in visible_channels:
			meas_key = f"meas_{ch}"
			ref_key = f"ref_{ch}"
			meas_vals: list[float] = [v for v in data.get(meas_key, []) if isinstance(v, (int, float))]
			ref_vals: list[float] = [v for v in data.get(ref_key, []) if isinstance(v, (int, float))]

			if len(meas_vals) >= 4:
				results[ch] = self.get_gamma_from_values(meas_vals, step_value=step_value)
			if len(ref_vals) >= 4:
				results_ref[ch] = self.get_gamma_from_values(ref_vals, step_value=step_value)

		if results:
			visible_results = [gr for ch, gr in results.items() if ch in visible_channels]
			results["all"] = GammaReading(
				gamma=mean(gr.gamma for gr in visible_results),
				step_value=step_value,
				d_min=mean(gr.d_min for gr in visible_results),
				d_max=mean(gr.d_max for gr in visible_results),
				search_range=Range(
					round(mean(gr.search_range.start for gr in visible_results)),
					round(mean(gr.search_range.end for gr in visible_results)),
				),
				gamma_range=Range(
					round(mean(gr.gamma_range.start for gr in visible_results)),
					round(mean(gr.gamma_range.end for gr in visible_results)),
				),
				ld=self.mean_optional([gr.ld for gr in visible_results]),
				md=self.mean_optional([gr.md for gr in visible_results]),
				hd=self.mean_optional([gr.hd for gr in visible_results]),
			)


		if results_ref:
			visible_results = [gr for ch, gr in results_ref.items() if ch in visible_channels]
			results["ref"] = GammaReading(
				gamma=mean(gr.gamma for gr in visible_results),
				step_value=step_value,
				d_min=mean(gr.d_min for gr in visible_results),
				d_max=mean(gr.d_max for gr in visible_results),
				search_range=Range(
					round(mean(gr.search_range.start for gr in visible_results)),
					round(mean(gr.search_range.end for gr in visible_results)),
				),
				gamma_range=Range(
					round(mean(gr.gamma_range.start for gr in visible_results)),
					round(mean(gr.gamma_range.end for gr in visible_results)),
				),
				ld=self.mean_optional([gr.ld for gr in visible_results]),
				md=self.mean_optional([gr.md for gr in visible_results]),
				hd=self.mean_optional([gr.hd for gr in visible_results]),
			)


		for k, v in results_ref.items():
			results[f"ref_{k}"] = v

		return results

