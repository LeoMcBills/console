from . import SequenceBase
from pathlib import Path

from PyQt5 import uic
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *  # type: ignore


class SequenceTSE(SequenceBase, registry_key=Path(__file__).stem):
    @classmethod
    def get_readable_name(self) -> str:
        return "3D TSE Demo"

    def setup_ui(self, widget) -> bool:
        """
        Returns the user inteface of the sequence.
        """
        layout = QVBoxLayout()
        layout.addSpacing(4)
        label = QLabel("Resolution")
        layout.addWidget(label)
        item = QSlider()
        item.setOrientation(Qt.Horizontal)
        item.setMaximumWidth(500)
        layout.addWidget(item)
        layout.addSpacing(30)
        label = QLabel("Bandwidth")
        layout.addWidget(label)
        item = QDial()
        item.setMaximumHeight(80)
        item.setMaximumWidth(80)
        item.setNotchesVisible(True)
        item.setStyleSheet("QDial { background-color: #FFF; color: #E0A526; }")
        layout.addWidget(item)
        value_label = QLabel("0 Hz/px")
        layout.addWidget(value_label)
        item.valueChanged.connect(lambda value: value_label.setText(str(value) + " Hz/px"))
        layout.addStretch()
        widget.setLayout(layout)
        return True
