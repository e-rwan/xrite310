from dataclasses import dataclass
from typing import List, NamedTuple, Union, Optional
from statistics import mean

STEP_VALUE = 0.15
HIGH_PCT = 0.2
LOW_PCT=0.20
MIN_DIFF = 0.03
NUM_STEPS = 4

class Range(NamedTuple):
	"""
	class to contain search or gamma range
	"""
	start: int
	end: int


@dataclass
class GammaReading:
	"""
	Class to contains values related to gamma readings
	"""
	global_gamma: float
	gamma: float
	gamma_delta: float
	step_value: float
	d_min: float
	d_max: float
	search_range: Range
	gamma_range: Range

	def __str__(self):
		return (
			f"gamma         : {self.gamma:.2f}\n"
			f"global_gamma  : {self.global_gamma:.2f}\n"
			f"gamma_delta   : {self.gamma_delta:.2f}\n"
			f"step_value    : {self.step_value:.2f}\n"
			f"d_min         : {self.d_min:.2f}\n"
			f"d_max         : {self.d_max:.2f}\n"
			f"search_range  : [{self.search_range.start} - {self.search_range.end}]\n"
			f"gamma_range   : [{self.gamma_range.start} - {self.gamma_range.end}]"
		)


class GammaAnalyzer:

	def get_search_range(self, values: List[float], low_pct=LOW_PCT, high_pct=HIGH_PCT) -> Range:
		""" Calculates the index range to search for gamma analysis.
		Args:
			values (List[float]): List of density values.
			low_pct (float, optional): Lower percentage for the range. Defaults to 0.20.
			high_pct (float, optional): Upper percentage for the range. Defaults to 0.20.
		Returns:
			Range: A tuple with start and end index for the search range.
		"""
		d_min = min(values)
		d_max = max(values)

		min_threshold = d_min + low_pct * (d_max - d_min)
		max_threshold = d_max - high_pct * (d_max - d_min)

		# first index > min_threshold
		start = next((i for i, v in enumerate(values) if v > min_threshold), 0)
		# first index > max_threshold -1
		end = next((i for i, v in enumerate(values) if v > max_threshold), len(values)) - 1

		start = max(1, start)
		end = min(len(values) - 1, end)

		return Range(start, end)
		

	def get_derivatives(self, values: List[float]) -> List[float]:
		""" Calculates central derivatives of a list
		Args:
			values (List[float]): List of density values.
		Returns:
			derivatives (List[float]): List of centered derivatives
		"""
		n = len(values)
		derivatives = [0.0]
		for i in range(1, n - 1):
			derivatives.append(values[i + 1] - values[i - 1])
		derivatives.append(derivatives[-1])
		return derivatives


	def get_gamma_range(self, values: List[float], search_range: Range, num_steps = NUM_STEPS) -> Range:
		""" Find the most linear range (minimum sum of acceleration).
		Args:
			values (List[float]): List of density values.
			gamma_range (Range): Index range to compute gamma in.
			step_value (float, optional): Number of step in range
		Returns:
			float: The computed gamma value.
		"""
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


	def get_gamma(self, gamma_range, values, step_value: float = STEP_VALUE):
		""" Computes the gamma value from the slope of the computed gamma range.
		Args:
			gamma_range (Range): Index range to compute gamma in.
			values (List[float]): List of density values.
			step_value (float, optional): Step size used for gamma calculation. Defaults to STEP_VALUE.
		Returns:
			float: The computed gamma value.
		"""
		delta_y = values[gamma_range.end] - values[gamma_range.start]
		delta_x = (gamma_range.end - gamma_range.start) * step_value
		gamma = delta_y / delta_x
		return gamma


	def get_gamma_from_values(self, values: List[float], step_value: float = STEP_VALUE, low_pct=LOW_PCT, high_pct=HIGH_PCT, min_diff= MIN_DIFF) -> GammaReading:
		""" Computes a detailed gamma reading from a list of values.
		Args:
			values (List[float]): List of density values.
			step_value (float, optional): Step size used for gamma calculation. Defaults to STEP_VALUE.
			low_pct (float, optional): Lower percentage the search range. Defaults to 0.20.
			high_pct (float, optional): Upper percentage for the search range. Defaults to 0.20.
			min_diff (float, optional):  Minimum difference threshold to ignore flat segments. Defaults to 0.03.
		Returns:
			GammaReading: Object including gamma data, ranges, and delta.
		Raises:
			ValueError: If fewer than 4 values are provided.
		"""
		if len(values) < 4:
			raise ValueError("At least 4 values are needed")

		search_range = self.get_search_range(values, low_pct, high_pct)
		gamma_range = self.get_gamma_range(values, search_range)
		global_gamma_range = Range(search_range.start, search_range.end)

		gamma = self.get_gamma(gamma_range, values, step_value)
		global_gamma = self.get_gamma(global_gamma_range, values, step_value)

		gamma_delta = abs(gamma - global_gamma)

		return GammaReading(
			global_gamma=global_gamma,
			gamma=gamma,
			gamma_delta=gamma_delta,
			step_value=step_value,
			d_min=min(values),
			d_max=max(values),
			search_range=Range(search_range.start + 1, search_range.end + 1),
			gamma_range=Range(gamma_range.start + 1, gamma_range.end + 1)
		)


	def get_gamma_from_curve_data(self, data: dict[str, list[Optional[float]]], visible_channels: list[str], step_value: float = STEP_VALUE) -> dict[str, GammaReading]:
		"""Computes gamma readings from curve data for each visible channel and combined channels.
		Args:
			data (dict[str, list[Optional[float]]]): Curve data with keys like 'meas_a', 'ref_a'.
			visible_channels (list[str]): Channels to include in the analysis.
			step_value (float, optional): Step size used for gamma calculation. Defaults to STEP_VALUE.
		Returns:
			dict[str, GammaReading]: Gamma results per channel, and for 'all' and 'ref' if applicable.
		"""
		if not visible_channels:
			return {}

		results: dict[str, GammaReading] = {}
		results_ref: dict[str, GammaReading] = {}

		for ch in visible_channels:
			meas_key = f"meas_{ch}"
			ref_key = f"ref_{ch}"
			meas_vals: list[float] = [v for v in data.get(meas_key, []) if isinstance(v, (int, float))]
			ref_vals: list[float]  = [v for v in data.get(ref_key, []) if isinstance(v, (int, float))]

			if len(meas_vals) >= 4:
				reading = self.get_gamma_from_values(meas_vals, step_value=step_value)
				results[ch] = reading
			if len(ref_vals) >= 4:
				reading = self.get_gamma_from_values(ref_vals, step_value=step_value)
				results_ref[ch] = reading
				
		# assign computed values to a GammaReading object for current measurments and ref
		# current measurments
		if results:
			visible_results = [gr for ch, gr in results.items() if ch in visible_channels]
			results["all"] = GammaReading(
				global_gamma=mean(gr.global_gamma for gr in visible_results),
				gamma=mean(gr.gamma for gr in visible_results),
				gamma_delta=abs(mean(gr.gamma for gr in visible_results) - mean(gr.global_gamma for gr in visible_results)),
				step_value=step_value,
				d_min=mean(gr.d_min for gr in visible_results),
				d_max=mean(gr.d_max for gr in visible_results),
				search_range=Range(
					round(mean(gr.search_range.start for gr in visible_results)),
					round(mean(gr.search_range.end for gr in visible_results))
				),
				gamma_range=Range(
					round(mean(gr.gamma_range.start for gr in visible_results)),
					round(mean(gr.gamma_range.end for gr in visible_results))
				)
			)
		# ref
		if results_ref:
			visible_results = [gr for ch, gr in results_ref.items() if ch in visible_channels]
			results["ref"] = GammaReading(
				global_gamma=mean(gr.global_gamma for gr in visible_results),
				gamma=mean(gr.gamma for gr in visible_results),
				gamma_delta=abs(mean(gr.gamma for gr in visible_results) - mean(gr.global_gamma for gr in visible_results)),
				step_value=step_value,
				d_min=mean(gr.d_min for gr in visible_results),
				d_max=mean(gr.d_max for gr in visible_results),
				search_range=Range(
					round(mean(gr.search_range.start for gr in visible_results)),
					round(mean(gr.search_range.end for gr in visible_results))
				),
				gamma_range=Range(
					round(mean(gr.gamma_range.start for gr in visible_results)),
					round(mean(gr.gamma_range.end for gr in visible_results))
				)
			)

		return results
