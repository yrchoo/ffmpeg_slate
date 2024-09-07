import os

os.system("""ffmpeg -start_number 1001 -i ./OPN_0010_plate/OPN_0010_plate_v001.%04d.png -vf "drawtext=fontfile=Arial.ttf: text='%{localtime\:%Y_%m_%d_%H_%M_%S}': start_number=1: x=(w-tw)/2: y=h-(2*lh): fontcolor=black: fontsize=20: box=1: boxcolor=white: boxborderw=5" ./OPN_0010_plate/output/OPN_0010_plate_v002.mp4""")