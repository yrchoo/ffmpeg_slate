import os

from PySide6.QtWidgets import QApplication, QDialog

from ui_slate_progress import Ui_Dialog

import time

class ProgressBarDialog(QDialog, Ui_Dialog):
    def __init__(self):
        super().__init__()
        self.path = os.path.dirname(__file__)
        
        self._set_ui_file()

    def _set_ui_file(self):

        self.setupUi(self)

    def change_prog_val(self, n):
        cur = self.progressBar.value()
        while cur != n :
            cur += 1
            self.progressBar.setValue(cur)
            time.sleep(0.001)
        print("ProgressBar val : " + str(n))
        if n == 100 :
            self.progressBar.setValue(cur)
            time.sleep(1)
            self.done(1)


if __name__ == "__main__":
    app = QApplication()
    win = ProgressBarDialog()
    win.show()
    app.exec()
