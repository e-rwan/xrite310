# lib/curves.py

from PySide6.QtCore import QObject, Signal
import json
import time
from typing import Union
from utils.plot_utils import ColorChannelSet
from constants import COLOR_SET

class CurveManager(QObject):
    
    data_updated = Signal(dict)


    def __init__(self):
        """
        Init
        """
        super().__init__()

        self.data: dict[str, list[Union[float, None]]] = {
            k: [None] * 21 for k in [
                'ref_a', 'ref_b', 'ref_c', 'ref_d',
                'meas_a', 'meas_b', 'meas_c', 'meas_d'
            ]
        }
        
        self.color_set = COLOR_SET

        self.color_mode = 'vrgb'


    def set_value(self, kind: str, color: str, index: int, value: float | None):
        """
        Update graph with value
        Args:
            kind (str): ref or meas
            color (str): color channel
            index (int)
            value (float)
        """
        key = f'{kind}_{color}'
        if key in self.data and 0 <= index < 21:
            self.data[key][index] = value  # type: ignore
            self.data_updated.emit(self.data)


    def clear_all(self):
        """
        Clear values from graph
        """
        for key in self.data:
            self.data[key] = [None] * 21
        self.data_updated.emit(self.data)


    def import_from_file(self, filepath: str) -> tuple[str, str, dict]:
        """
        Import measurement values from file.
        Returns: (color_mode, values) for reuse by GUI
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            payload = json.load(f)

        name = payload.get("name", "sensito")
        self.color_mode = payload.get("color", "vrgb")
        values = payload.get("values", {})

        color_set = self.color_set[self.color_mode]
        for channel, vals in values.items():
            abcd = color_set.channel_to_abcd.get(channel)
            if not abcd:
                continue
            key = f"meas_{abcd}"
            for i in range(min(21, len(vals))):
                self.data[key][i] = vals[i]

        self.data_updated.emit(self.data)
        return name, self.color_mode, values


    def export_to_file(self, filepath: str, name: str = "sensito"):
        """
        Export measurement values to JSON file using color set mapping.
        """
        color_set = self.color_set[self.color_mode]
        values = {}

        for channel in color_set.order:  # e.g. ['v', 'r', 'g', 'b']
            abcd = color_set.channel_to_abcd[channel]  # e.g. 'v' → 'a'
            key = f"meas_{abcd}"
            channel_data = self.data.get(key, [None] * 21)
            if any(channel_data):  # inclure uniquement les canaux utilisés
                values[channel] = [v if v is not None else 0.0 for v in channel_data]

        output = {
            "name": name,
            "color": self.color_mode,
            "date": time.strftime("%Y-%m-%d_%H%M"),
            "values": values
        }
        

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2)

