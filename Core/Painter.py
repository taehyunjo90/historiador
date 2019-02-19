import sys
from PyQt5.QtWidgets import *
from PyQt5 import uic
from Core.DataProcessor import *

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

# form_class = uic.loadUiType("Data\\mainwindow.ui")[0]
form_class = uic.loadUiType("..\\Data\\mainwindow.ui")[0]

class MyWindow(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        # DataProcessor
        self.dp = DataProcessor()

        # 조회 버튼
        self.button_enter.clicked.connect(self.btn_clicked)

        # add Canvas
        self.addCanvas()

    def addCanvas(self):
        self.fig = plt.Figure()
        self.fig.patch.set_visible(False)
        self.canvas = FigureCanvas(self.fig)
        self.chart.addWidget(self.canvas)

    def btn_clicked(self):
        code = str(self.edit_code.text())
        start_date = str(self.edit_start.text())
        end_date = str(self.edit_end.text())

        df = self.dp.getHistoricalPBR(code, start_date, end_date)
        times = df.index
        pbrs = df.loc[:,'PBR']

        ax = self.fig.add_subplot(111)
        ax.plot(times, pbrs)
        ax.grid()

        self.canvas.draw()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow = MyWindow()
    myWindow.show()
    app.exec_()