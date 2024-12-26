
import re
import threading
import subprocess

from functools import partial

from PySide6.QtWidgets import QApplication, QWidget, QFileDialog
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, Signal, Qt
from PySide6.QtGui import QPixmap

import ffmpeg_data
import progress_bar
# import qthreads


class SlateMaker(QWidget):
    RUNNING_RENDER_PROCESS = Signal(int)

    def __init__(self):
        """
        Initialize setup
        """
        super().__init__()
        input_path = self.show_file_dialog()

        self.data = ffmpeg_data.FFMPEGData(input_path)

        self._set_ui_file()
        self.show()

    def _set_ui_file(self):
        """
        Load UI file and set it at self.ui
        """
        ui_file_path = "ui/slate_maker.ui"
        ui_file = QFile(ui_file_path)
        ui_file.open(QFile.ReadOnly)

        loader = QUiLoader()
        self.ui = loader.load(ui_file, self)

        ui_file.close()

        self._set_ui()
        self._set_event()

    def _set_event(self):
        """
        Set UI events
        """
        self.ui.pushButton_run.clicked.connect(self._make_cmd)

    def _set_ui(self):
        """
        Functions which should run before show UI window
        """
        self._set_slate_combo_box()
        self._set_slate_label()
        self._ui_set_ext_combo_box()
        self._show_info_ui()

    def _set_slate_label(self):
        """
        Save label objects into dict value for simplify code
        """
        self.slate_label = {key: getattr(self.ui, f"label_{key}")
                            for key in ffmpeg_data.SLATE_LABEL_LOCATION.keys()}

    def _set_slate_combo_box(self):
        """Setup Combo Box object.
        Each Combo Box shows data that will be display on slate.
        """
        # Save combobox objects into dict value for simplify code
        self.slate_combo = {key: getattr(self.ui, f"comboBox_{key}")
                            for key in ffmpeg_data.SLATE_LABEL_LOCATION.keys()}

        # Add Items in combo box
        for key, cb in self.slate_combo.items():
            cb.addItem("--None--")
            cb.addItems(self.data.input_file_data.keys())
            cb.currentTextChanged.connect(partial(self._change_label_text, key))

    def _ui_set_ext_combo_box(self):
        """
        Set combo box data for output extension value
        """
        ext_list = [".mov", ".mp4"]
        self.ui.comboBox_ext.addItems(ext_list)
        self.ui.comboBox_ext.currentTextChanged.connect(self._change_extension)

    def _show_info_ui(self):
        self.ui.projectLineEdit.setText(self.data.input_file_data["Project"])
        self.ui.shotLineEdit.setText(self.data.input_file_data["Shot"])
        self.ui.taskLineEdit.setText(self.data.input_file_data["Task"])
        self.ui.versionLineEdit.setText(self.data.input_file_data["Version"])

        thumbnail_path = self.data.get_thumbnail_image()
        if thumbnail_path:
            pixmap = QPixmap(thumbnail_path)

            pixmap = pixmap.scaled(self.ui.frame.size(), Qt.KeepAspectRatioByExpanding,
                                   Qt.SmoothTransformation)

            self.ui.frame.setAutoFillBackground(True)

            palette = self.ui.frame.palette()
            palette.setBrush(self.ui.frame.backgroundRole(), pixmap)
            self.ui.frame.setPalette(palette)


    def _change_extension(self, val):
        """Save changed extension value
        This method triggered by currentTextChanged signal of extension combo box

        Args:
            val: Current extension value of extension combo box

        """
        self.data.output_ext = val

    def _change_label_text(self, key, val):
        """When combobox value is changed, update text in label at same location with combo box

        Args:
            key (str): key value for slate_label dictionary
            val (str): current value of slate_combo[key]
        """
        if val == "--None--" :
            text = ""
        else :
            text = self.data.input_file_data[val]
        self.slate_label[key].setText(text)

    def show_file_dialog(self):
        """
        Show QFileDialog to select input file for FFMPEG

        Returns:
            file_path (str): File path of selected file from QFileDialog

        """
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Input File",
                                                   ffmpeg_data.FILE_DIALOG_PATH)

        if not file_path:
            exit()

        return file_path

    def _make_cmd(self):
        """
        Make FFMPEG command running on shell
        """
        if self.data.input_ext in [".png", ".exr"] :
            ffmpeg_cmd = ' '.join(
                [
                    "ffmpeg",
                    "-framerate", "24",
                    "-start_number", self.data.first_frame
                ]
            )
        else: # input == video
            ffmpeg_cmd = ' '.join(
                [
                    "ffmpeg"
                ]
            )
        cmd = ' '.join(
            [
                ffmpeg_cmd,
                f"-i", f"{self.data.input_file_path}",
                f"-vf", f'"{self.padding}{self.drawtext}"',
                f"-c:v", "prores_ks",
                f"{self.data.out_file_path}{self.data.output_ext}",
                "-y"
            ]
        )
        print(cmd)
        self.run_thread(cmd)

    @property
    def padding(self):
        """
        Returns:
            padding(str) : command string for drawing black box for slate
        """
        upside_padding = "".join(
            [
                "drawbox=", "x=0:", "y=0:",
                "w=iw:", f"h=ih*0.05:", "color=black:",
                "t=fill", ","
            ]
        )
        downside_padding = "".join(
            [
                "drawbox=", "x=0:", f"y=ih*(1-0.05):",
                "w=iw:", f"h=ih*0.05:", "color=black:",
                "t=fill", ","
            ]
        )
        padding = "".join([upside_padding, downside_padding])
        return padding

    @property
    def drawtext(self):
        """

        Returns:
            drawtext (str): command string for drawing text with each data for slate

        """
        drawtext_cmd = ""

        for loc, cb in self.slate_combo.items():
            key = cb.currentText()
            if key == "--None--":
                text = ""
            else:
                text = self.data.input_file_data[key]
            cmd = "drawtext="
            cmd += " ".join(
                [
                    f"fontfile={self.data.font_file_path}:",
                    f"text='{text}':",
                    f"start_number={self.data.first_frame}:",
                    f"x={ffmpeg_data.SLATE_LABEL_LOCATION[loc][0]}: "
                    f"y={ffmpeg_data.SLATE_LABEL_LOCATION[loc][1]}:",
                    f"fontcolor=white@0.7:",
                    f"fontsize='{self.data.font_size}':",
                ]
            )
            drawtext_cmd += f"{cmd},"
        return drawtext_cmd[:-1]

    def _progress_bar_dialog(self):
        """Show progress bar dialog"""
        prog_dialog = progress_bar.ProgressBarDialog()
        self.RUNNING_RENDER_PROCESS.connect(prog_dialog.change_prog_val)
        prog_dialog.exec()


    def _run_ffmpeg_subprocess(self, cmd):
        """Run ffmpeg command with subprocess and get frame number where ffmpeg is working on
        and emit it

        Args:
            cmd: ffmpeg command
        """
        process = subprocess.Popen([cmd],
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

    def run_thread(self, cmd):
        """
        Make ffmpeg subprocess and progress bar dialog run in different thread

        Args:
            cmd: ffmpeg command
        """
        # TODO: There's some problem with run every function with thread in MacOS...
        #       But still FFMPEG command works well :).......

        threads = []

        progress = threading.Thread(target=self._progress_bar_dialog)
        threads.append(progress)

        sub = threading.Thread(target=partial(self._run_ffmpeg_subprocess, cmd))
        threads.append(sub)

        for t in threads:
            t.start()


if __name__ == "__main__":
    app = QApplication()
    win = SlateMaker()
    app.exec()


