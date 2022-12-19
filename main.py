import tkinter as tk
from tkinter import filedialog
from tkinter.filedialog import askopenfile
from PIL import Image, ImageTk
import imutils
import cv2
from imutils.video import VideoStream
import threading
import time
import os

STICKER_PATH = '/stickers'
NUM_STICKERS_SHOWN = 3
STICKER_INDEX = 0

RECTANGLE_ID = []
STICKER_ID = []
STICKER_NAME = None
STICKER_IMAGE = None
STICKER_PHOTO_IMAGE = None
STICKER_WIDTH = None
STICKER_HEIGHT = None

MODE = {
	"DEFAULT" : 0,
	"STICKER" : 1
}
CURR_MODE = MODE["DEFAULT"]

PANEL = None
STOP_EVENT = None
THREAD = None
FRAME = None

# VIDEO STREAM
VS = VideoStream(0).start()
time.sleep(2.0)

window = tk.Tk()
window.geometry("729x356")
window.title('Face Detection')
window.wm_protocol("WM_DELETE_WINDOW", lambda:on_close())

stickers = os.listdir(os.getcwd() + STICKER_PATH)
stickers_amount = len(stickers)

def change_sticker_status(sticker_name, spec_status = False):
	global CURR_MODE
	global STICKER_NAME
	global STICKER_ID
	
	# TO FLUSH
	global STICKER_IMAGE
	global STICKER_PHOTO_IMAGE
	global STICKER_WIDTH
	global STICKER_HEIGHT

	STICKER_IMAGE = None
	STICKER_PHOTO_IMAGE = None
	STICKER_HEIGHT = None
	STICKER_WIDTH = None

	for id in STICKER_ID:
		PANEL.delete(id)
	
	for id in RECTANGLE_ID:
		PANEL.delete(id)

	CURR_MODE = not CURR_MODE

	if(spec_status):
		CURR_MODE = spec_status

	if(STICKER_NAME is None):
		STICKER_NAME = sticker_name
	else:
		STICKER_NAME = None

def show_sticker():
	global FRAME
	global STICKER_IMAGE
	global STICKER_PHOTO_IMAGE
	global STICKER_WIDTH
	global STICKER_HEIGHT
	global RECTANGLE_ID
	global STICKER_ID

	cascPath = "data/haarcascade_frontalface_default.xml"
	faceCascade = cv2.CascadeClassifier(cascPath)

	FRAME_TO_DETECT = imutils.resize(FRAME, width=300*2, height= 168*2)

	gray = cv2.cvtColor(FRAME_TO_DETECT, cv2.COLOR_BGR2GRAY)
	
	faces = faceCascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(30, 30),
        flags=cv2.CASCADE_SCALE_IMAGE
    )

	if(CURR_MODE == MODE["STICKER"] and STICKER_IMAGE is None):
		print(STICKER_IMAGE)
		STICKER_IMAGE = Image.open(STICKER_NAME)
		rgba = STICKER_IMAGE.convert("RGBA")
		data = rgba.getdata()

		new_data = []
		for item in data:
			if(item[0] == 255 and item[1] == 255 and item[2] == 255):
				new_data.append((255,255,255,0))
			else:
				new_data.append(item)

		rgba.putdata(new_data)

		STICKER_IMAGE = rgba		

	for (x, y, w, h) in faces:
		if(CURR_MODE == MODE["DEFAULT"]):
			RECTANGLE_ID.append(PANEL.create_line(x,y,x+w,y,x+w,y+h,x,y+h,x,y,fill="red"))
		else:
			if(not (STICKER_WIDTH == w and STICKER_HEIGHT == h)):	
				STICKER_WIDTH = w
				STICKER_HEIGHT = h	
				sticker_resized = STICKER_IMAGE.resize((w,h))
				STICKER_PHOTO_IMAGE = ImageTk.PhotoImage(sticker_resized)

			STICKER_ID.append(PANEL.create_image(x,y, image=STICKER_PHOTO_IMAGE, anchor=tk.NW))
	
def upload_file():
	f_types = [('Jpg Files', '*.jpg')]
	filename = filedialog.askopenfilename(filetypes=f_types)
	
	change_sticker_status(filename, MODE["STICKER"])

	STICKER_IMAGE = Image.open(filename)

	rgba = STICKER_IMAGE.convert("RGBA")
	data = rgba.getdata()

	new_data = []
	for item in data:
		if(item[0] == 255 and item[1] == 255 and item[2] == 255):
			new_data.append((255,255,255,0))
		else:
			new_data.append(item)

	rgba.putdata(new_data)

	STICKER_IMAGE = rgba	
	print("upload_file",STICKER_IMAGE)

def show_stickers(window,stickers,index):
	global sticker1
	global sticker2
	global sticker3

	curr_stickers = stickers[(index*NUM_STICKERS_SHOWN):(index+1)*NUM_STICKERS_SHOWN]

	sticker1 = Image.open('.' + STICKER_PATH + '/' + curr_stickers[0])
	sticker2 = Image.open('.' + STICKER_PATH + '/' + curr_stickers[1])
	sticker3 = Image.open('.' + STICKER_PATH + '/' + curr_stickers[2])

	width = 79
	height = 79

	sticker1_resized = sticker1.resize((width,height))
	sticker2_resized = sticker2.resize((width,height))
	sticker3_resized = sticker3.resize((width,height))

	sticker1 = ImageTk.PhotoImage(sticker1_resized)
	sticker2 = ImageTk.PhotoImage(sticker2_resized)
	sticker3 = ImageTk.PhotoImage(sticker3_resized)

	sticker1_btn = tk.Button(window,image=sticker1, command=lambda: change_sticker_status('.' + STICKER_PATH + '/' + curr_stickers[0]))
	sticker2_btn = tk.Button(window,image=sticker2, command=lambda: change_sticker_status('.' + STICKER_PATH + '/' + curr_stickers[1]))
	sticker3_btn = tk.Button(window,image=sticker3, command=lambda: change_sticker_status('.' + STICKER_PATH + '/' + curr_stickers[2]))

	sticker1_btn.grid(row=1,column=2, padx=10,pady=5)
	sticker2_btn.grid(row=2,column=2, padx=10,pady=5)
	sticker3_btn.grid(row=3,column=2, padx=10,pady=5)

def browse_btn():
	upload_btn = tk.Button(window, text='browse', 
	width=5,command = lambda:upload_file())
	upload_btn.grid(row=4,column=2) 

def video_loop():
	global PANEL
	global FRAME
	global LAST_FRAME

	# DISCLAIMER:
	# I'm not a GUI developer, nor do I even pretend to be. This
	# try/except statement is a pretty ugly hack to get around
	# a RunTime error that Tkinter throws due to threading
	try:
		# keep looping over frames until we are instructed to stop
		while not STOP_EVENT.is_set():
			# grab the frame from the video stream and resize it to
			# have a maximum width of 300 pixels
			FRAME = VS.read()
			FRAME = imutils.resize(FRAME, width=300)
	
			# OpenCV represents images in BGR order; however PIL
			# represents images in RGB order, so we need to swap
			# the channels, then convert to PIL and ImageTk format
			image = cv2.cvtColor(FRAME, cv2.COLOR_BGR2RGB)
			image = Image.fromarray(image)
			width, height = image.size
			image = image.resize((width*2,height*2))
			image = ImageTk.PhotoImage(image)
	
			# if the panel is not None, we need to initialize it
			if PANEL is None:
				PANEL = tk.Canvas(height=image.height(),width=image.width(), bg="white")
				PANEL.grid(row=1, column=1, rowspan=4, padx=10,pady=10)

				LAST_FRAME = PANEL.create_image(0,0, image=image, anchor=tk.NW)
				PANEL.image = image
	
			# otherwise, simply update the panel
			else:
				PANEL.itemconfig(LAST_FRAME, image=image)
				PANEL.image = image
			
			if(CURR_MODE == MODE["DEFAULT"] and len(RECTANGLE_ID) > 0):
				for id in RECTANGLE_ID:
					PANEL.delete(id)

			show_sticker()
				
	except RuntimeError:
		print("[INFO] caught a RuntimeError")

def on_close():
	global STOP_EVENT
	# set the stop event, cleanup the camera, and allow the rest of
	# the quit process to continue
	STOP_EVENT.set()
	VS.stop()
	window.quit()


show_stickers(window, stickers, STICKER_INDEX)
browse_btn()

# start a thread that constantly pools the video sensor for
# the most recently read frame
STOP_EVENT = threading.Event()
THREAD = threading.Thread(target=video_loop, args=())
THREAD.start()

window.mainloop()  # Keep the window open

    
