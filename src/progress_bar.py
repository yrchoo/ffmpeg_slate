from PySide6.QtWidgets import QApplication, QDialog, QProgressBar, QVBoxLayout

from src.create_slate import FFMPEGWorker

import time

class ProgressBarDialog(QDialog):
    def __init__(self, ffmpeg_worker : FFMPEGWorker):
        super().__init__()
        self._set_ui()

        self.worker = ffmpeg_worker
        self.worker.RUNNING_RENDER_PROCESS.connect(self.change_prog_val)

    def _set_ui(self):
        self.setWindowTitle("Running FFMPEG...")
        self.setGeometry(50, 50, 350, 70)

        layout = QVBoxLayout()

        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)

        layout.addWidget(self.progress_bar)
        self.setLayout(layout)

    def exec(self):
        self.worker.start()
        super().exec()

    def change_prog_val(self, n):
        cur = self.progress_bar.value()
        if n == -1:
            self.done(0)
        while cur != n :
            cur += 1
            self.progress_bar.setValue(cur)
            time.sleep(0.001)
        print("ProgressBar val : " + str(n))
        if n == 100 :
            self.progress_bar.setValue(cur)
            time.sleep(1)
            self.done(1)