import sys

from PyQt5.QtWidgets import *
from PyQt5 import uic
from PyQt5.QtWidgets import QMessageBox

from Core.Historiador import Historiador
from Util.windowUtil import *

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

# form_class = uic.loadUiType("UI\\mainwindow.ui")[0]
form_class = uic.loadUiType("..\\UI\\mainwindow.ui")[0]

class MyWindow(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        # DataProcessor
        self.hs = Historiador()

        #StatusBar
        self.statusBar = QStatusBar(self)
        self.setStatusBar(self.statusBar)

        # Text edit chaged fucntion
        self.edit_code.textChanged.connect(self.edit_code_Changed)

        # 조회 버튼
        self.button_enter.clicked.connect(self.btn_clicked)

        # add Canvas & bool_
        self.addCanvas()

    def addCanvas(self):
        self.fig = plt.Figure()
        # self.fig.patch.set_visible(False)
        self.canvas = FigureCanvas(self.fig)
        self.chart_layout.addWidget(self.canvas)


    def edit_code_Changed(self):
        input_code = self.edit_code.text()

        bl, ret = checkCodes(input_code, self.hs.dp.df_codeinfo)
        if bl:
            msg = '\"' + ret + '\"' + "에 대한 조사를 시작합니다."
        else:
            if ret == "no-exist":
                msg = "종목코드를 재확인 부탁드립니다."
            elif ret == "no-enter":
                msg = "종목코드를 입력바랍니다. (6자리)"
            elif ret == "no-format":
                msg = "종목코드의 자릿수 초과 입력. (6자리)"

        self.statusBar.showMessage(msg)

    def btn_clicked(self):

        # Inputs

        code = str(self.edit_code.text())
        start_date = qtDateToString(self.edit_start.date())
        end_date = qtDateToString(self.edit_end.date())
        range_years = self.edit_years_range.value()
        bool_csd_trea = self.check_treasury.isChecked()

        # Check input Integrity
        if checkCodes(code, self.hs.dp.df_codeinfo)[0] == False:
            QMessageBox.about(self, "Error", "종목코드 입력값이 잘못되었습니다. 재확인 바랍니다.")
            return

        self.statusBar.showMessage("데이터를 찾고 있습니다...")
        # Check RadioButton
        if self.button_PBR.isChecked():
            self.runPBR(code, start_date, end_date, bool_csd_trea)
            # QMessageBox.about(self, "test", "PBR SELECTED")
        elif self.button_PBRROE.isChecked():
            self.runPBRROE(code, start_date, end_date, range_years, bool_csd_trea)
            # QMessageBox.about(self, "test", "PBRROE SELECTED")
        elif self.button_PER.isChecked():
            self.runPER(code, start_date, end_date, range_years, bool_csd_trea)
            # QMessageBox.about(self, "test", "PER SELECTED")
        else:
            QMessageBox.about(self, "Error", "지표를 선택해주십시오.")

    def runPBR(self, code, start_date, end_date, csd_trea):
        df_process = self.hs.getHistoricalPBR(code, start_date, end_date, csd_trea)
        sr_to_plot = df_process.loc[:,'PBR']
        x = sr_to_plot.index
        y = sr_to_plot.values
        self.drawOneYChart(x,y, "PBR")
        self.statusBar.showMessage("완료")

    def runPER(self, code, start_date, end_date, range_years, csd_trea):
        df_process = self.hs.getHistoricalPER(code, start_date, end_date, range_years, csd_trea)
        sr_to_plot = df_process.loc[:,'PER']
        x = sr_to_plot.index
        y = sr_to_plot.values
        self.drawOneYChart(x,y, "PER")
        self.statusBar.showMessage("완료")

    def runPBRROE(self, code, start_date, end_date, range_years, csd_trea):
        df_process = self.hs.getHistoricalPBRandROE(code, start_date, end_date, range_years, csd_trea)
        sr_to_plot_one = df_process.loc[:,'PBR']
        sr_to_plot_two = df_process.loc[:,'ROE']

        x_one = sr_to_plot_one.index
        y_one = sr_to_plot_one.values
        y_two = sr_to_plot_two.values

        self.drawTwoChart(x_one, y_one, y_two, "PBR", "ROE")
        self.statusBar.showMessage("완료")

    def drawOneYChart(self, x, y, y_label):
        ax = self.fig.add_subplot(111)
        ax.plot(x,y,'-b')
        ax.set_xlabel('Time')
        ax.set_ylabel(y_label)
        self.canvas.draw()
        self.fig.clear() # fig에서 삭제해줌 -> 실제로 보이는 건 삭제 되진 않으나 다시 self.cavas.draw() 할때 겹치지 않음

    def drawTwoChart(self, x, y_one, y_two, y_label_one, y_label_two):
        ax1 = self.fig.add_subplot(111)
        ax2 = ax1.twinx()
        ax1.plot(x, y_one, '-b')
        ax2.plot(x, y_two, '-r')

        ax1.set_xlabel('Time')
        ax1.set_ylabel(y_label_one)

        ax2.set_ylabel(y_label_two)

        self.canvas.draw()
        self.fig.clear()  # fig에서 삭제해줌 -> 실제로 보이는 건 삭제 되진 않으나 다시 self.cavas.draw() 할때 겹치지 않음

        #
        # df_process = self.hs.getHistoricalPBRandROE(code, start_date, end_date, range_years, csd_trea=True)
        # ax1 = self.fig.add_subplot(111)
        # ax2 = ax1.twinx()
        # ax1.plot(df_process.loc[:, 'PBR'].index, df_process.loc[:, 'PBR'].values, 'g-')
        # ax2.plot(df_process.loc[:, 'ROE'].index, df_process.loc[:, 'ROE'].values, 'b-')
        #
        # ax1.set_xlabel('Times')
        # ax1.set_ylabel('PBR', color='g')
        # ax2.set_ylabel('ROE', color='b')
        # self.canvas.draw()



if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow = MyWindow()
    myWindow.show()
    app.exec_()