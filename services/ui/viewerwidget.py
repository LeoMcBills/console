import json
from pathlib import Path
from typing import Optional
from PyQt5 import uic
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *  # type: ignore
import qtawesome as qta  # type: ignore

import pyqtgraph as pg
import pydicom
import numpy as np

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import common.logger as logger
from common.types import ResultTypes

log = logger.get_logger()


class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        plt.style.use("dark_background")
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)


class ViewerWidget(QWidget):
    # layout: QBoxLayout
    widget: Optional[QWidget] = None
    series_name = ""

    def __init__(self):
        super(ViewerWidget, self).__init__()
        self.setLayout(QVBoxLayout(self))
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)
        self.set_empty_viewer()

    def set_series_name(self, name: str):
        self.series_name = name
        self.update()

    def view_data(self, file_path: str, viewer_mode: ResultTypes):
        self.clear_view()
        if viewer_mode == "dicom":
            self.load_dicoms()
        elif viewer_mode == "plot":
            self.load_plot()
        else:
            self.set_empty_viewer()

    def clear_view(self):
        if self.widget:
            self.layout().removeWidget(self.widget)
            self.widget.deleteLater()
            self.widget = None

    def view_scan(self, file_path: Path):
        self.clear_view()
        dcm_path = file_path / "dicom"
        other_path = file_path / "other"
        if list(dcm_path.glob("**/*.dcm")):
            self.load_dicoms(str(dcm_path))
            return True
        elif others := list(other_path.glob("*.json")):
            self.load_plot(json.loads(others[0].read_text()))
            return False

    def load_dicoms(self, input_path="/vagrant/classDcm"):
        lstFilesDCM = [str(p) for p in Path(input_path).glob("**/*.dcm")]
        lstFilesDCM.sort()
        if len(lstFilesDCM) < 1:
            self.set_empty_viewer()
            return
        ds = pydicom.dcmread(lstFilesDCM[0])

        ConstPixelDims = (len(lstFilesDCM), int(ds.Rows), int(ds.Columns))

        ArrayDicom = np.zeros(ConstPixelDims, dtype=ds.pixel_array.dtype)

        for filenameDCM in lstFilesDCM:
            ds = pydicom.dcmread(filenameDCM)
            ArrayDicom[lstFilesDCM.index(filenameDCM), :, :] = ds.pixel_array

        pg.setConfigOptions(imageAxisOrder="row-major")
        viewer_widget = pg.image(ArrayDicom)

        viewer_widget.ui.histogram.hide()
        viewer_widget.ui.roiBtn.hide()
        viewer_widget.ui.menuBtn.hide()

        # text = pg.LabelItem("Patient ID", color=(255, 255, 255), bold=True, size="18px")
        # text.setPos(-30, -10)
        # viewer_widget.addItem(text)

        # Another option to display text
        # label = QLabel("Patient ID")
        # label.move(0, 0)
        # label.setStyleSheet("background-color: #000;")
        # self.layout.addWidget(label)

        self.layout().addWidget(viewer_widget)
        self.widget = viewer_widget

    def load_plot(self, array=None):
        sc = MplCanvas(self)
        if array is None:
            array = np.random.normal(size=10)
        sc.axes.plot(array)
        self.layout().addWidget(sc)
        self.widget = sc

    def set_empty_viewer(self):
        self.widget = QWidget()
        self.widget.setStyleSheet("background-color: #000;")
        self.layout().addWidget(self.widget)
