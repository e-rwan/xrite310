# lib/curves.py

from PySide6.QtCore import QObject, Signal
from typing import Union

class CurveManager(QObject):
    """Manages curve data and updates for a graphical plot.

    This class handles the management of curve data for different color
    channels, allowing updates and clearing of the data. It also emits
    signals when data changes, enabling integration with other parts of
    an application.

    Attributes:
        data_updated (Signal): Signal emitted when the data is updated.
    """
    
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