import os
import re
import glob

from datetime import datetime

from PySide6.QtWidgets import QApplication, QWidget, QFileDialog
from PySide6.QtWidgets import QMessageBox
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, Signal

import cv2

from functools import partial

import subprocess

import threading

import progress_bar



class SlateFFMPEG(QWidget):

    RENDER_PROCESS_ING = Signal(int)

    def __init__(self):
        super().__init__()

        self._set_ui_file()
        self._set_event()
        self._set_data_value()
        self._set_ui_value()
        self._file_dialog()

    def _set_ui_file(self):
        """
        UI File을 Open하고 self.ui에 설정해주는 Method
        """
        ui_file_path = "./slate_info.ui"
        ui_file = QFile(ui_file_path)
        ui_file.open(QFile.ReadOnly)
        
        loader = QUiLoader()
        self.ui = loader.load(ui_file, self)

        ui_file.close()
    
    def _set_event(self):
        self.ui.pushButton_run.clicked.connect(self._make_cmd)

    def _set_data_value(self):
        """
        ffmpeg 명령어에 필요한 file data를 지정하는 method
        """
        self.basic_path = "/home/rapa/show/insideout2/seq/CYR/CYR_0100/comp/dev/" # FileDialog가 열릴 때 열리는 기본 경로
        self.input_file_data = {
            "project" : "",
            "shot" : "",
            "task" : "",
            "version" : "",
            "timecode&frame" : "",
            "date" : "",
        }
        self.first_frame = 1001
        self.last_frame = 1001
        self.input_file_path = ""
        self.out_file_path = ""
        self.font_file_path = "/usr/share/fonts/Courier_Prime"

        self.input_ext = ""
        self.output_ext = ".mov"

    def _set_ui_value(self):
        """
        코드 단순화를 위해 ui 객체를 저장할 value를 지정하는 method
        """
        self.slate_cb = {
            "top_left" : "",
            "top_center" : "",
            "top_right" : "",
            "bottom_left" : "",
            "bottom_center" : "",
            "bottom_right" : ""
        }

        self.slate_label = {
            "top_left" : "",
            "top_center" : "",
            "top_right" : "",
            "bottom_left" : "",
            "bottom_center" : "",
            "bottom_right" : ""
        }

        self.slate_location = {
            "top_left" : ["10", "0"],
            "top_center" : ["(w-tw)/2", "0"],
            "top_right" : ["w-tw", "0"],
            "bottom_left" : ["10", "h-(2*lh)"],
            "bottom_center" : ["(w-tw)/2", "h-(2*lh)"],
            "bottom_right" : ["w-tw", "h-(2*lh)"]
        }

        self._ui_set_slate_combo_boxes()
        self._ui_set_font_combo_box()
        self._ui_set_ext_combo_box()
        self._ui_set_slate_label()

    def _ui_set_slate_combo_boxes(self):
        """
        UI의 comboBox 객체들을 저장하고 값을 설정해주는 메서드
        """
        for key in self.slate_cb.keys():
            self.slate_cb[key] = getattr(self.ui, f"comboBox_{key}")

        for key, cb in self.slate_cb.items():
            cb.addItem("--None--")
            cb.addItems(self.input_file_data.keys())
            cb.currentTextChanged.connect(partial(self._change_label_text, key))

    def _change_label_text(self, key, val):
        """
        comboBox가 변경될 때마다 해당 값을 label에 띄우는 메서드
        """
        if val == "--None--" : 
            text = ""
        else :
            text = self.input_file_data[val]
        self.slate_label[key].setText(text)

    def _ui_set_slate_label(self):
        """
        UI의 label 객체들을 저장하고 값을 설정해주는 메서드
        """
        for key in self.slate_label.keys():
            self.slate_label[key] = getattr(self.ui, f"label_{key}")

    def _ui_set_font_combo_box(self):
        """
        UI의 font 설정을 위한 comboBox 객체에 값을 설정해주는 메서드
        """
        font_list = os.listdir(self.font_file_path)
        self.ui.comboBox_font.addItems(font_list)

    def _ui_set_ext_combo_box(self):
        """
        UI에서 output 파일의 확장자 설정을 위한 comboBox 객체에 값을 설정해주는 메서드
        """
        ext_list = [".mov", ".mp4"]
        self.ui.comboBox_ext.addItems(ext_list)
        self.ui.comboBox_ext.currentTextChanged.connect(self._change_ext)

    def _change_ext(self, val):
        """
        comboBox의 값이 달라질 때마다 해당 값을 저장하는 메서드
        """
        self.output_ext = val

    def _file_dialog(self) :
        """
        Program이 시작되자마자 Pop되는 FileDialog
        """

        file_path, _ = QFileDialog.getOpenFileName(self, "Select Input File",
                                                 self.basic_path, 
                                                 "")

        if file_path == '' :
            exit() 

        # 파일을 성공적으로 불러왔을 경우
        self._set_input_file_data(file_path)
        self.show() 

    def _set_input_file_data(self, path):
        # FileDialog에서 선택한 file의 path에서 필요한 정보를 추출하여 저장
        parse = re.compile("[/][s][h][o][w][/].*")
        p_data = parse.search(path).group()
        
        dirs = p_data.split('/')

        file = os.path.basename(path)
        file_name, file_ext = os.path.splitext(file)
        dir_name = os.path.dirname(path)
        file_name = file_name.split('.')[0]

        file_split = file_name.split('_')
        self.input_file_path = path
        self._get_frame_range(file_ext, file_name)
        self.out_file_path = f"{dir_name}/{file_name}_slate"

        self.input_file_data["project"] = dirs[2].upper()
        self.input_file_data["shot"] = f"{file_split[0]}_{file_split[1]}"
        self.input_file_data["task"] = file_split[2].upper()
        self.input_file_data["version"] = file_split[3]
        self.input_file_data["timecode&frame"] = "%{n}" + f"\/{self.first_frame}-{self.last_frame}"
        self.input_file_data["date"] = datetime.today().strftime("%Y-%m-%d")
        self.input_ext = file_ext

    def _get_frame_range(self, ext, file_name):
        """
        Slate에 들어갈 프레임의 정보를 가져오는 메서드
        """
        if ext in [".png", ".exr"] :
            files_name = self.input_file_path.split(".")[0]
            files_path = f"{files_name}.*{ext}"
            self.input_file_path = f"{files_name}.%04d{ext}"
            print(files_path)
            files = glob.glob(files_path)
            files.sort()
            parse = re.compile("[.]\d{4}")
            self.first_frame = int(parse.findall(files[0])[0][1:])
            self.last_frame = int(parse.findall(files[-1])[0][1:])

        elif ext == ".mov" :
            cap = cv2.VideoCapture(self.input_file_path)
            length = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            self.last_frame = 1000 + length

    def _make_cmd(self):
        """
        shell에서 실행할 ffmpeg 명령어를 생성하는 메서드
        """
        if self.input_ext in [".png", ".exr"] :
            ffmpeg_cmd = ' '.join(
                [
                    "ffmpeg",
                    "-framerate", "24",
                    "-start_number", self.first_frame
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
                f"-i", f"{self.input_file_path}",
                f"-vf", f"'{self._cmd_padding()}{self._make_drawtext()}'",
                f"-c:v", "prores_ks",
                f"{self.out_file_path}{self.output_ext}",
                "-y"
            ]
        )
        print(cmd)
        self._run_cmd(cmd)

    def _cmd_padding(self):
        """
        slate 정보가 들어갈 box 부분을 생성하는 메서드
        """
        padding_size = self.ui.horizontalSlider_padding.value() / 100
        upside_padding = "".join(
            [
                "drawbox=", "x=0:", "y=0:",
                "w=iw:", f"h=ih*{padding_size}:", "color=black:",
                "t=fill", ","
            ]
        )
        downside_padding = "".join(
            [
                "drawbox=", "x=0:", f"y=ih*(1-{padding_size}):",
                "w=iw:", f"h=ih*{padding_size}:", "color=black:",
                "t=fill", ","
            ]
        )
        padding = "".join([upside_padding, downside_padding])
        return padding

    def _make_drawtext(self):
        """
        ffmpeg 명령어에서 drawtext문을 만들어주는 메서드
        """
        font = f"{self.font_file_path}/{self.ui.comboBox_font.currentText()}"
        font_size = self.ui.horizontalSlider_padding_font_size.value()
        self._update_slate_location_data(font_size)
        drawtext_cmd = ""
        
        for loc, cb in self.slate_cb.items():
            key = cb.currentText()
            if key == "--None--":
                text = ""
            else :
                text = self.input_file_data[key]
            cmd = "drawtext="
            cmd += " ".join(
                [
                f"fontfile={font}:", 
                f"text='{text}':", 
                f"start_number={self.first_frame}:",
                f"x={self.slate_location[loc][0]}: y={self.slate_location[loc][1]}:", 
                f"fontcolor=white@0.7:", 
                f"fontsize={font_size}:", 
            ]
            )
            drawtext_cmd += f"{cmd},"
        return drawtext_cmd[:-1]

    def _update_slate_location_data(self, font_size):
        """
        slate text 위치 이름에 따라 출력 위치 값을 보정해주는 메서드
        """
        padding_size = self.ui.horizontalSlider_padding.value() / 100
        for key, val in self.slate_location.items():
                if "top" in key : self.slate_location[key][1] = f"h*{padding_size/2}-{font_size/2}"
                else : self.slate_location[key][1] = f"h*{1-padding_size/2}-{font_size/2}"
        print(self.slate_location)

    def _run_cmd(self, cmd) : # subprocess
        """
        ffmpeg 명령어와 progress bar를 띄우는 ui를 스레드로 실행하는 메서드
        """
        threads = []

        # Make Thread
        prog_win = threading.Thread(target=self._progress_bar_dialog)
        threads.append(prog_win)

        sub_p = threading.Thread(target=partial(self._subprocess_cmd, cmd))
        threads.append(sub_p)

        for t in threads:
            t.start()

    def _progress_bar_dialog(self):
        """
        progress bar를 가지는 dialog를 선언하고 실행하는 메서드
        """
        win_prog = progress_bar.ProgressBarDialog()
        self.RENDER_PROCESS_ING.connect(win_prog.change_prog_val)
        win_prog.exec()

    def _subprocess_cmd(self, cmd):
        """
        ffmpeg cmd를 subprocess의 Popen으로 실행하는 메서드
        """
        process = subprocess.Popen([cmd], 
                               stdout=subprocess.PIPE, 
                               stderr=subprocess.STDOUT,
                               universal_newlines=True,
                               )
        
        for line in process.stdout :
            if not line.startswith("frame="):
                continue
            parse = re.compile("[f][r][a][m][e][=][ ]*\d*")
            frame_val = int(parse.search(line).group().split(" ")[-1])
            percentage = int(frame_val * 100 / (self.last_frame - self.first_frame + 1))
            self.RENDER_PROCESS_ING.emit(percentage) # 현재 ffmpeg에서 돌아가는 frame 값을 읽어와서 해당 값을 방출
            # 이 값은 progress bar를 통해 보여진다
        

if __name__ == "__main__":
    app = QApplication()
    win = SlateFFMPEG()
    app.exec()
