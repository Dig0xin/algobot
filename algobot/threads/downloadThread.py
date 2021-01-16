import traceback

from data import Data
from PyQt5.QtCore import QObject, QRunnable, pyqtSignal, pyqtSlot


class DownloadSignals(QObject):
    """
    Defines the signals available from a running worker thread.
    """
    csv_finished = pyqtSignal(str)
    finished = pyqtSignal(list)
    error = pyqtSignal(str)
    restore = pyqtSignal()
    progress = pyqtSignal(int, str)
    locked = pyqtSignal()


class DownloadThread(QRunnable):
    def __init__(self, interval, symbol, descending=None, armyTime=None):
        super(DownloadThread, self).__init__()
        self.signals = DownloadSignals()
        self.symbol = symbol
        self.interval = interval
        self.descending = descending
        self.armyTime = armyTime
        self.client: Data or None = None

    @pyqtSlot()
    def run(self):
        """
        Initialise the runner function with passed args, kwargs.
        """
        try:
            self.client = Data(interval=self.interval, symbol=self.symbol, updateData=False)
            data = self.client.custom_get_new_data(progress_callback=self.signals.progress, locked=self.signals.locked)
            if data:
                if self.descending is None and self.armyTime is None:
                    self.signals.finished.emit(data)
                else:  # This means the CSV generator called this thread.
                    self.signals.progress.emit(100, "Creating CSV file...")
                    savedPath = self.client.create_csv_file(descending=self.descending, armyTime=self.armyTime)
                    self.signals.csv_finished.emit(savedPath)
        except Exception as e:
            print(f'Error: {e}')
            traceback.print_exc()
            self.signals.error.emit(str(e))
        finally:
            self.signals.restore.emit()

    def stop(self):
        """
        Stop the download loop if it's running.
        """
        if self.client is not None:
            self.client.downloadLoop = False
