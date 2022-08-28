#!/usr/bin/python3.7
import Adafruit_SSD1306, time, multiprocessing
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import tornado.web 
import asyncio, socket, os, subprocess, glob, sys
from os import path
os.chdir(sys.path[0])

manager = multiprocessing.Manager()
disp = Adafruit_SSD1306.SSD1306_128_32(rst=None)
disp.begin()
font = ImageFont.truetype("FreeSans.ttf", 14)
disp.clear()
disp.display()

car_path = "/home/pi/picar"
action_map={
    "reboot":"sudo shutdown -r now",
    "shutdown":"sudo shutdown -h now",
    "reloadwifi":"sudo wpa_cli -i wlan0 reconfigure"
}

# dict global - multhread
GlobalMap = manager.dict()
GlobalMap['System']=manager.dict()
GlobalMap['Drive']=manager.dict()
GlobalMap['Model']=manager.dict()
GlobalMap['Drive']['Car path']=car_path
action_map['tmux_drivecar']="cd {} ; /home/pi/env/bin/python3.7 manage.py drive --js".format(car_path)

for files in glob.glob(car_path+"/models/*"):
    filename = os.path.basename(files)
    extra_args="--type tflite_linear" if 'tflite' in filename else ""
    GlobalMap['Model'][filename]="tmux_"+filename
    action_map["tmux_"+filename]="cd {} ; /home/pi/env/bin/python3.7 manage.py drive --model=models/{} {}".format(car_path,filename,extra_args)

# init default tmux
os.system("tmux has-session -t oled || tmux new -d -s oled")

# menu - message sur oled
def show_oled(message) :
    GlobalMap['line_display']=message
    disp.clear()
    disp.display()
    width = disp.width
    height = disp.height
    image = Image.new('1', (width, height))
    draw = ImageDraw.Draw(image)
    draw.text((0, 0), message ,  font=font, fill=255)
    disp.image(image)
    disp.display()

class MessageHandler(tornado.web.RequestHandler):
    def initialize(self, shared_dict):
        self.shared_dict = shared_dict
    def get(self):
        thread_info()
        self.render("index.html", **self.shared_dict)
    def post(self):
        data = tornado.escape.json_decode(self.request.body)
        print(data)

class InfoHandler(tornado.web.RequestHandler):
    def initialize(self, shared_dict):
        self.shared_dict = shared_dict
    def get(self):
        self.write(dict(self.shared_dict))
    def post(self):
        data = tornado.escape.json_decode(self.request.body)
        print(data)
        if 'action' in data and data['action'] in action_map:
            run_command(action_map[data['action']],data['action'])

async def runhttp():
    tornado_settings = {
        'static_path': 'static',
        'template_path': 'templates',
        'debug': True
    }
    app = tornado.web.Application([(r"/js/(.*)",tornado.web.StaticFileHandler, {"path":'static/js'}),
                                   (r"/css/(.*)",tornado.web.StaticFileHandler, {"path":'static/css'}),
                                   (r"/data", InfoHandler,dict(shared_dict=GlobalMap)),
                                   (r"/", MessageHandler,dict(shared_dict=GlobalMap))
    ],**tornado_settings)
    app.listen(8888)
    await asyncio.Event().wait()

def run_command(command,key=None):
    print("key: {} -> command:{}".format(key, command))
    if key is not None and 'tmux' in key :
        command = 'tmux send -t oled "{}" ENTER \;'.format(command)
        os.system("tmux has-session -t oled || tmux new -d -s oled") 
        os.system(command)
    else :
        sp = subprocess.Popen(command, stderr=subprocess.PIPE, stdout=subprocess.PIPE,stdin=None, shell=True)
        out, err = sp.communicate()
        return sp.returncode, out.decode("utf-8")

def thread_info(shared_dict=GlobalMap):
    try :
        result=run_command("echo $(hostname -I)")[1]
        GlobalMap['System']['IPv4']=result.split(" ")[0]
    except:
        GlobalMap['System']['IPv4']=None

    # bluetooth
    GlobalMap['System']['Controler js0']=run_command("ls /dev/input/js0 > /dev/null 2>&1 && hcitool dev  | grep hci | awk '{print $2} ' && exit 1 || echo missing && exit 0")[1]

    # Wifi
    GlobalMap['System']['Access Point']=run_command("iwgetid -r")[1]
    GlobalMap['System']['Channel']=run_command("iwgetid -r -c")[1]
    GlobalMap['System']['Heure']=run_command("echo $(date +%T)")[1]

if __name__ == '__main__':
    threadinfo = multiprocessing.Process(target=thread_info, args=())
    threadinfo.start()
    asyncio.run(runhttp())
