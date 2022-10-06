import os
import sys
from config import config
import time
from pynvml import *
from pynvml.smi import nvidia_smi
from PyQt5 import uic
from PyQt5.QtCore import QCoreApplication
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog
from PyQt5.QtCore import QObject, QThread, pyqtSignal

app = QApplication(sys.argv)


class Updater(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(int)
    nvmlInit()

    def __init__(self, comps=None, parent=None):
        super().__init__(parent)
        self.nvsmi = None
        self.comps = comps

    def run(self):
        self.nvsmi = nvidia_smi.getInstance()
        gpuID = 1

        while True:
            # Update The memory status
            data = self.nvsmi.DeviceQuery('memory.free, memory.total, clocks.current.memory, power.draw, '
                                          'power.max_limit, fan.speed, temperature.gpu, temperature.memory')['gpu']
            # Display Memory Usage
            for gpuID in range(len(data)):
                data_mem = data[gpuID]['fb_memory_usage']

                self.comps[f"mem_pbar{gpuID}"].setMinimum(0)
                self.comps[f"mem_pbar{gpuID}"].setMaximum(int(data_mem['total']))
                self.comps[f"mem_pbar{gpuID}"].setValue(int(data_mem['total'] - data_mem['free']))

                # Display Power Usage
                data_power = data[gpuID]['power_readings']
                self.comps[f"power_pbar{gpuID}"].setMinimum(0)
                self.comps[f"power_pbar{gpuID}"].setMaximum(int(data_power['max_power_limit']))
                self.comps[f"power_pbar{gpuID}"].setValue(int(data_power['power_draw']))

                # Display Fan Speed
                self.comps[f"fan_pbar{gpuID}"].setValue(data[gpuID]['fan_speed'])

                # Display Temperature
                data_temp = data[gpuID]['temperature']
                self.comps[f"temp_pbar{gpuID}"].setMinimum(0)
                self.comps[f"temp_pbar{gpuID}"].setMaximum(int(data_temp['gpu_temp_max_threshold']))
                self.comps[f"temp_pbar{gpuID}"].setValue(int(data_temp['gpu_temp']))


                # Update the GPU clock speed.

                time.sleep(config.refresh_rate)


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        uic.loadUi(os.path.join("ui", "base-ui.ui"), self)

        self.thread = QThread()
        self.comps1 = {"mem_pbar0": self.mem_pbar0,
                       "power_pbar0": self.power_pbar0,
                       "fan_pbar0": self.fan_pbar0,
                       "temp_pbar0": self.temp_pbar0,
                       "mem_pbar1": self.mem_pbar1,
                       "power_pbar1": self.power_pbar1,
                       "fan_pbar1": self.fan_pbar1,
                       "temp_pbar1": self.temp_pbar1,
                       }

        self.worker = Updater(comps=self.comps1)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()


if __name__ == "__main__":
    print(config.refresh_rate)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
