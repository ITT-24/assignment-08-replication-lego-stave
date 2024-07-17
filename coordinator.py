import threading
import cv2
import numpy as np
import cv2.aruco as aruco
import sys
import math
from sound_generation import Note, Instrument, SoundGenerator

DEBUG = False # set to true, to see grid -> otherwise wont draw for better performance

NOTE_DURATION_IN_SEC = 0.5
NOTE_VOLUME = 100

REFERENCE_NOTE = 48 # aka
SAMPLING_RATE = 44100
GRID_COLOR = (200, 200, 200)
TIMELINE_COLOR = (0, 0, 0)
ID_TO_INSTRUMENT = {
    0: Instrument.PIANO, # red
    1: Instrument.BASS, # green
    2: Instrument.SAX, # blue
    3: Instrument.WOODBLOCK, # yellow
}

MIDI_INDEX_TO_NOTE = {
    0:"C",
    1:"C#",
    2:"D",
    3:"D#",
    4:"E",
    5:"F",
    6:"F#",
    7:"G",
    8:"G#",
    9:"A",
    10:"A#",
    11:"B"
}

flip_image= False
# INIT VIDEO FEED
cam_id = 0
if len(sys.argv) > 1:
    cam_id = int(sys.argv[1])
if len(sys.argv) > 2:
    if sys.argv[2] in ["-f", "-F", "-flip", "flip"]:
        flip_image = True
    

aruco_dict_border = aruco.getPredefinedDictionary(aruco.DICT_6X6_100)
aruco_dict_notes = aruco.getPredefinedDictionary(aruco.DICT_4X4_100)

aruco_params = aruco.DetectorParameters()
detector_border = aruco.ArucoDetector(aruco_dict_border,aruco_params)
detector_notes = aruco.ArucoDetector(aruco_dict_notes, aruco_params)


# ----- Helper classes ----- #

class Lego:
    """A representation of a lego duplo piece standing on it's side. So smooth sides up."""
    def __init__(self):
        padding_w = 2 # padding added to the physical playfield-grid
        padding_h = 1
        self.width_mm = 18 + padding_w  
        self.height_mm = 31 + padding_h 
        self.marker_mm = 16
        self.marker_size = 0
        self.padding = 0 # add padding if you want -> best if it corresponds to the physical playfield (if used)

    def set_lego_size(self, corners, frame):
        """Measure the rough size of the lego pieces in pixels in the frame. Uses the first detected lego"""
        # partially from: https://pysource.com/2021/05/28/measure-size-of-an-object-with-opencv-aruco-marker-and-python/
        
        if self.marker_size != 0:
            return # only set once
        
        if not coord.has_started:
            return # only set once the user presses enter

        int_corners = np.intp(corners)
        cv2.polylines(frame, int_corners, True, (0, 255, 0), 2) # for debug

        aruco_perimeter = cv2.arcLength(corners[0], True)
        self.marker_size = int(aruco_perimeter / 4)

        mm_in_px = self.marker_size / self.marker_mm # set the transform value

        frame_h, frame_w, _ = frame.shape

        # get initial size for dynamic padding
        # width_px = int(self.width_mm * mm_in_px)
        # height_px = int(self.height_mm * mm_in_px)
        # self.add_dynamic_padding(frame_w, width_px, frame_h, height_px)

        # static padding
        self.width_px = int( self.width_mm * mm_in_px )
        self.height_px = int( self.height_mm * mm_in_px )

        # print(f"lego == {self.width_px} x {self.height_px}")

    def add_dynamic_padding(self, frame_w, width_px, frame_h, height_px):
        """adds dynamic padding to make the cells fit the frame better (works (with, but has some rounding errors))
           so: |[lego+padding][l+p][l+p][l+p]| not |[l+p][l+p][l+p][|
        """

        padding_w = 0
        if frame_w % width_px != 0: # set a padding to fill the width of the frame
            cells_w = int(frame_w / width_px )
            diff_w = frame_w - (width_px * cells_w)
            padding_w = int(diff_w / width_px)
        padding_h = 0
        if frame_h % height_px != 0:
            cells_h = int(frame_h / height_px)
            diff_h = frame_h - (height_px * cells_h)
            padding_h = int(diff_h / cells_h)
        # rounding for cv2 functions
        self.width_px = int( width_px + padding_w )
        self.height_px = int( height_px + padding_h )


class Coordinator:
    """A class that capsules the position detection of the markers"""
    
    def __init__(self):
        self.rows = 0
        self.cols = 0
        self.centers = []
        self.ids = []
        self.has_started = False

    def draw_grid(self, frame):
        """see: https://stackoverflow.com/a/37705365"""
        
        if lego.marker_size == 0:
            return # only draw after marker was successfully detected
        if not self.has_started:
            return 

        # divide the into cells using the lego size
        h, w, _ = frame.shape
        rows, cols = (h//lego.height_px, w//lego.width_px)

        if DEBUG:
            grid_x_idx = 0
            grid_y_idx = 0

            cell_width = lego.width_px
            cell_height = lego.height_px

            for x in range (0, w, cell_width):
                x = int(x)
                cv2.line(frame, (x, 0), (x, h), color=GRID_COLOR, thickness=1)
                cv2.putText(frame, str(grid_x_idx), (x, h), cv2.FONT_HERSHEY_PLAIN, 1, GRID_COLOR)
                grid_x_idx += 1

            for y in range (0, h, cell_height):
                y = int(y)
                cv2.line(frame, (0, y), (w, y), color=GRID_COLOR, thickness=1)
                note_name  = MIDI_INDEX_TO_NOTE[(REFERENCE_NOTE + grid_y_idx) % 12]
                octave = math.floor((REFERENCE_NOTE + grid_y_idx) / 12) - 2
                cv2.putText(frame, note_name + str(octave), (0, y+12), cv2.FONT_HERSHEY_PLAIN, 1, GRID_COLOR)
                grid_y_idx += 1

        self.rows = rows
        self.cols = cols
        self.has_started = True


    def get_marker_center(self, corners, frame):
        """Get the middle of the marker for all markers, see: https://stackoverflow.com/a/64742091"""
        self.centers = [] # override

        for c in corners:
            x_sum = c[0][0][0]+ c[0][1][0]+ c[0][2][0]+ c[0][3][0]
            y_sum = c[0][0][1]+ c[0][1][1]+ c[0][2][1]+ c[0][3][1]
                
            x_centerPixel = int(x_sum*.25)
            y_centerPixel = int(y_sum*.25)

            cv2.circle(frame, (x_centerPixel, y_centerPixel), 5, (0, 0, 255), -1)

            self.centers.append((x_centerPixel, y_centerPixel)) # save centers
        

    def draw_collision(self, frame):
        """Show the cell the marker is currently colliding with"""
        if self.rows == 0:
            return
        for center in self.centers:
            # get which cell the center is in
            cell = self.get_cell_of_marker_center(center)

    def get_cell_of_marker_center(self, center, reversed_cols=False):
        """Detect which cell the marker is in, see: https://stackoverflow.com/a/37705365"""
        
        h, w, _ = frame.shape
        rows, cols = (h//lego.height_px, w//lego.width_px)

        x, y = center
        row = int( x / lego.width_px )
        col = int( y / lego.height_px) 
        if reversed_cols:
            col = cols - col

        # print(f"row: {row} + col: {col}")

        x = row * lego.width_px
        y = col * lego.height_px
        cv2.rectangle(frame, (x, y), (x+lego.width_px, y+lego.height_px), (255, 255, 255), 2)
        
        cell = Cell(row, col)
        return cell


class Player:
    """Capsules the media-player aspect of the application."""
    def __init__(self):
        self.color = TIMELINE_COLOR
        self.x = 0
        self.column = 0
        self.start = False
        self.is_paused = True
        self.timer = None
        self.active_cells = []
        pass

    def draw_timeline(self, frame):
        if lego.marker_size == 0:
            return 
        
        if coord.has_started and not self.start: 
            # start the timer once on initialization of the grid
            self.start_timer()
            self.start = True
        
        h, w, _ = frame.shape

        if self.x >= w: # reset the timeline and loop the player
            # print("out of frame", self.x, w)
            self.x = 0 # reset
            self.column = 0

        cv2.line(frame, (self.x, 0), (self.x, h), color=self.color, thickness=2)

        # uncomment if check every frame
        # self.play_cells() # checks often    

    def play_cells(self):
        """Checks the current column for markers.
           Do this every frame, or only once per timer call
        """
        self.active_cells = []
        for i, center in enumerate(coord.centers):
            x, y = center

            cell_min = lego.width_px * self.column
            cell_max = cell_min + lego.width_px
            
            # check if there is a marker center that aligns with column the timeline is currently at
            if x >= cell_min and x <= cell_max:
                cell = coord.get_cell_of_marker_center(center, reversed_cols=True)

                try:
                    id = coord.ids[i] # IndexError: index 2 is out of bounds for axis 0 with size 2
                except IndexError: 
                    return 
                
                #print("marker @", f"row:{cell.row}, col:{cell.col}")
                self.active_cells.append((id, cell))
                newSoundEvent.clear()
                newSoundEvent.set()
        
        notes = []
        for id, cell in self.active_cells:
            notes.append(self.position_to_note(cell,id[0]))
        player.active_cells = []
        synth.play_simultaneous_notes(notes)
                
        self.advance_timeline() # comment if check every frame
    
    def position_to_note(self,cell, id):
        y_index = cell.col
        # print(f"position: {y_index}")
        note = REFERENCE_NOTE + y_index
        instrument = ID_TO_INSTRUMENT[id]
        length = NOTE_DURATION_IN_SEC
        volume = NOTE_VOLUME # 80
        return Note(length, note, instrument, volume)


    def advance_timeline(self):
        """Gets called by a repeating threaded timer to advance the timeline (see: Looper-Class)"""
        self.column += 1
        self.x += lego.width_px 
        # print("player @ col", self.column)
    
    def start_timer(self):
        self.timer = Looper(NOTE_DURATION_IN_SEC, self.play_cells) # comment if check every frame
        # self.timer = Looper(NOTE_DURATION_IN_SEC, self.advance_timeline) # uncomment if check every frame
        self.timer.start()
        self.is_paused = False

    def stop_timer(self):
        if self.timer:
            self.timer.cancel()

    def on_pause(self):
        if self.timer == None:
            text = "No grid initiated yet. Press Enter and put a marker below the camera."
            print(text)
        else: 
            if self.is_paused:
                print("play")
                self.start_timer()
                self.is_paused = False
            else:
                print("pause")
                self.stop_timer()
                self.is_paused = True


class Looper(threading.Timer):
    """A threaded looping timer, based on: https://stackoverflow.com/a/48741004"""
    def run(self):
        while not self.finished.wait(self.interval):
            self.function(*self.args, **self.kwargs)

class Cell:
    def __init__(self, row, col):
        self.row = row  
        self.col = col

# ----- INIT ----- #

lego = Lego()
coord = Coordinator()
player = Player()
synth = SoundGenerator(SAMPLING_RATE)
newSoundEvent = threading.Event()

# ----- LOOP ----- #

cap = cv2.VideoCapture(cam_id, cv2.CAP_DSHOW)
cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)

def synth_thread():

    while True:
        if end_synth_thread_flag:
            break
        newSoundEvent.wait()

end_synth_thread_flag = False
synth_thread = threading.Thread(target=synth_thread)
synth_thread.start()
while True:
    # Capture a frame from the webcam
    ret, frame = cap.read()

    if not ret:
        print("No frame")
        continue
    if flip_image:
        frame = cv2.flip(frame, -1)

    # Convert the frame to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Detect ArUco markers in the frame
    corners, ids, rejected = detector_notes.detectMarkers(gray)

    # Check if markers for the borders are detected
    if ids is not None:
        # aruco.drawDetectedMarkers(frame, corners, ids)
        lego.set_lego_size(corners, frame) 
        coord.get_marker_center(corners, frame)
        coord.ids = ids
        coord.draw_collision(frame)

    coord.draw_grid(frame)
    player.draw_timeline(frame)

    # Display the frame
    cv2.imshow('frame', frame)

    # Wait for a key press and check if it's the 'q' key
    key = cv2.waitKey(1)
    if key == 27 or key == 113: # esc or q
        player.stop_timer()
        break
    elif key == 32: # space
        player.on_pause()
    elif key == 13: # enter
        coord.has_started = True


# Release the video capture object and close all windows
cap.release()
end_synth_thread_flag = True
cv2.destroyAllWindows()
