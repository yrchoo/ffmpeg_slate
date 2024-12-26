
import os
import re
import glob

from datetime import datetime

import cv2
import shutil


FILE_DIALOG_PATH = "/Users/yerin/Documents/NetflixAcademy/ToyProject/show"

SLATE_LABEL_LOCATION = {
    "top_left": ["10", "h*0.01"],
    "top_center": ["(w-tw)/2", "h*0.01"],
    "top_right": ["w-tw", "h*0.01"],
    "bottom_left": ["10", "h*0.96"],
    "bottom_center": ["(w-tw)/2", "h*0.96"],
    "bottom_right": ["w-tw", "h*0.96"]
}

class FFMPEGData:
    """
    Data Class for saving data for FFMPEG command
    """
    def __init__(self, file_path):
        # Data about input files
        self.input_file_data = {
            "Project": "",
            "Shot": "",
            "Task": "",
            "Version": "",
            "Timecode&Frame": "",
            "Date": "",
        }

        self.first_frame = 1001
        self.last_frame = 1001

        self.input_file_path = ""
        self.out_file_path = "" # This will create automatically based on input file data

        self.font_file_path = "/System/Library/Fonts/Supplemental/Courier New Bold.ttf"
        self.font_size = 30

        self.input_ext = ""
        self.output_ext = ".mov"

        self.slate_label = { key : "" for key in SLATE_LABEL_LOCATION.keys() }

        self._set_input_file_data(file_path)


    def _set_input_file_data(self, path):
        """
        Collect data from input file
        Args:
            path: file path of input file for FFMPEG

        """

        parse = re.compile("[/][s][h][o][w][/].*")
        p_data = parse.search(path).group()

        dirs = p_data.split('/')

        file = os.path.basename(path)
        file_name, file_ext = os.path.splitext(file)
        dir_name = os.path.dirname(path)
        file_name = file_name.split('.')[0]

        file_split = file_name.split('_')
        self.input_file_path = path
        self._get_frame_range(file_ext)
        self.out_file_path = f"{dir_name}/{file_name}_slate"

        self.input_file_data["Project"] = dirs[2].upper()
        self.input_file_data["Shot"] = f"{file_split[0]}_{file_split[1]}"
        self.input_file_data["Task"] = file_split[2].upper()
        self.input_file_data["Version"] = file_split[3]
        self.input_file_data["Timecode&Frame"] = "%{n}" + f"/{self.first_frame}-{self.last_frame}"
        self.input_file_data["Date"] = datetime.today().strftime("%Y-%m-%d")
        self.input_ext = file_ext

    def _get_frame_range(self, ext):
        """
        Read frame data and get font size from file

        Args:
            ext: input file's extension
            file_name: input file's name

        """
        if ext.lower() in [".png", ".exr"] :
            files_name = self.input_file_path.split(".")[0]
            files_path = f"{files_name}.*{ext}"
            self.input_file_path = f"{files_name}.%04d{ext}"
            print(files_path)
            files = glob.glob(files_path)
            files.sort()
            parse = re.compile("[.]\\d{4}")
            self.first_frame = int(parse.findall(files[0])[0][1:])
            self.last_frame = int(parse.findall(files[-1])[0][1:])

            image = cv2.imread(self.input_file_path)

            if image is not None:
                height, width, channels = image.shape
                self.font_size = int(height * 0.03)

        elif ext.lower() == ".mov" :
            cap = cv2.VideoCapture(self.input_file_path)
            length = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            self.last_frame = 1000 + length
            self.font_size = int(int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) * 0.03)



    def get_thumbnail_image(self):
        # TODO: Get image of frame located 30% of input file and show on UI thumbnail
        #       Now this works only for mov. Need to add EXR
        dir_name = os.path.dirname(self.input_file_path) + "/thumbnail"
        if not os.path.exists(dir_name):
            os.mkdir(dir_name)
        file_name, ext = os.path.splitext(os.path.basename(self.input_file_path))
        frame_number = int((self.last_frame - self.first_frame) * 0.3)

        output_image_path = None

        if ext.lower() in [".png", ".exr"]: # image source
            src_file = (f'{self.input_file_path.split(".")[0]}.{1001 + frame_number}'
                        f'.{self.input_file_path.split(".")[-1]}')
            output_image_path = f'{dir_name}/{file_name}.{frame_number}.jpg'
            if not os.path.exists(output_image_path):
                shutil.copy(src_file, output_image_path)

        elif ext.lower() == ".mov":
            output_image_path = f"{dir_name}/{file_name}.jpg"
            if not os.path.exists(output_image_path):
                capture = cv2.VideoCapture(self.input_file_path)
                capture.set(cv2.CAP_PROP_POS_FRAMES, frame_number - 1)
                ret, frame = capture.read()
                if ret:
                    cv2.imwrite(output_image_path, frame)

        return output_image_path
