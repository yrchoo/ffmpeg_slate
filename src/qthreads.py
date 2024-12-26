from PySide6.QtCore import Signal, QThread

import subprocess
import re

import progress_bar


class SubprocessFFMPEG(QThread):
    RUNNING_RENDER_PROCESS = Signal(int)

    def __init__(self, cmd, data):
        super().__init__()
        self.cmd = cmd
        self.data = data

    def run(self):
        process = subprocess.Popen([self.cmd],
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT,
                                   universal_newlines=True,
                                   )

        for line in process.stdout:
            if not line.startswith("frame="):
                continue
            parse = re.compile("[f][r][a][m][e][=][ ]*\\d*")
            frame_val = int(parse.search(line).group().split(" ")[-1])
            percentage = int(frame_val * 100 / (self.data.last_frame - self.data.first_frame + 1))
            self.RUNNING_RENDER_PROCESS.emit(percentage)


class ProgressBar(QThread):
    def __init__(self):
        super().__init__()
        self.progress_bar = progress_bar.ProgressBarDialog()

    def run(self):
        self.progress_bar.exec()
