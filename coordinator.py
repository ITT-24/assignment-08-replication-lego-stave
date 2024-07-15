import threading
import cv2
import numpy as np
import cv2.aruco as aruco
import sys
import math
from sound_generation import Note, Instrument, SoundGenerator

NOTE_DURATION_IN_SEC = 0.5
REFERENCE_NOTE = 69 # aka C4
SAMPLING_RATE = 44100
GRID_COLOR = (200, 200, 200)
TIMELINE_COLOR = (0, 0, 0)
ID_TO_INSTRUMENT = {
    0: Instrument.PIANO,
    1: Instrument.SAX,
    2: Instrument.HAMMOND,
    3: Instrument.BASS
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

# INIT VIDEO FEED
cam_id = 0
if len(sys.argv) > 1:
    cam_id = int(sys.argv[1])

aruco_dict_border = aruco.getPredefinedDictionary(aruco.DICT_6X6_100)
aruco_dict_notes = aruco.getPredefinedDictionary(aruco.DICT_4X4_100)

aruco_params = aruco.DetectorParameters()
detector_border = aruco.ArucoDetector(aruco_dict_border,aruco_params)
detector_notes = aruco.ArucoDetector(aruco_dict_notes, aruco_params)

# TODO: use angle of surface to create perspectively transformed grid
# ??: instead of padding cells, crop the frame?

# ----- Helper classes ----- #

class Lego:
    """A representation of a lego duplo piece standing on it's side. So smooth sides up."""
    def __init__(self):
        self.width_mm = 18 # actually 18 (but adds some leniency)
        self.height_mm = 31 # actually 31 (but adds some leniency)
        self.marker_mm = 16
        self.marker_size = 0
        self.padding = 20 

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

        # get initial size
        width_px = int(self.width_mm * mm_in_px)
        height_px = int(self.height_mm * mm_in_px)
        
        # add dynamic padding to make the cells fit the frame better (works (with, but has some rounding errors))
        # so: |[lego+padding][l+p][l+p][l+p]| not |[l+p][l+p][l+p][|
        padding_w = 0
        if frame_w % width_px != 0: # set a padding to fill the width of the frame
            cells_w = int(frame_w / width_px )
            diff_w = frame_w - (width_px * cells_w)
            padding_w = int(diff_w / width_px)
            print("w", cells_w * int( width_px + padding_w), "==", frame_w )

        padding_h = 0
        if frame_h % height_px != 0:
            cells_h = int(frame_h / height_px)
            print("cells", cells_h)
            diff_h = frame_h - (height_px * cells_h)
            print("diff", diff_h)
            padding_h = int(diff_h / cells_h)
            print("padding", padding_h)
            print("h", cells_h * ( height_px + padding_h), "==", frame_h )

        # rounding for cv2 functions
        self.width_px = int( width_px + padding_w )
        self.height_px = int( height_px + padding_h )

        # uncomment to do static padding
        # self.width_px = int( (self.width_mm * mm_in_px) + self.padding)
        # self.height_px = int ( (self.height_mm * mm_in_px) + self.padding)

        # # resize to fit grid?
        # #  frame = cv2.resize(frame, ( (self.width_px) * steps,  (self.height_px) * steps_h ))

        print(f"lego == {self.width_px} x {self.height_px}")


class Coordinator:
    """A class that capsules the position detection of the markers"""
    
    def __init__(self):
        self.rows = 0
        self.cols = 0
        self.centers = []
        self.ids = []
        self.has_started = False

    # ?? do perspective projection?
    def draw_grid(self, frame):
        """see: https://stackoverflow.com/a/37705365"""
        
        if lego.marker_size == 0:
            return # only draw after marker was successfully detected
        if not self.has_started:
            return 

        # divide the into cells using the lego size
        h, w, _ = frame.shape
        rows, cols = (h//lego.height_px, w//lego.width_px)

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
        
        # print("c's", len(self.centers))
        # TODO: ? only re-save the centers, if the markers have moved significantly (for performance)


    def draw_collision(self, frame):
        """Show the cell the marker is currently colliding with"""
        if self.rows == 0:
            return
        for center in self.centers:
            # get which cell the center is in
            cell = self.get_cell_of_marker_center(center)

    def get_cell_of_marker_center(self, center):
        """Detect which cell the marker is in, see: https://stackoverflow.com/a/37705365"""
        x, y = center
        row = int( x / lego.width_px )
        col = int( y / lego.height_px) 
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
            print("out of frame", self.x, w)
            self.x = 0 # reset
            self.column = 0

        cv2.line(frame, (self.x, 0), (self.x, h), color=self.color, thickness=2)

        # uncomment if check every frame
        # self.play_cells() # check often    

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
                cell = coord.get_cell_of_marker_center(center)
                id = coord.ids[i]
                print("marker @", f"row:{cell.row}, col:{cell.col}")
                self.active_cells.append((id, cell))
                newSoundEvent.clear()
                newSoundEvent.set()
        
        notes = []
        for id, cell in self.active_cells:
            notes.append(self.position_to_note(cell,id[0]))
        player.active_cells = []
        synth.play_simultaneous_notes(notes)
        
        # TODO: Advanced stuff, like merging notes, etc
        
        self.advance_timeline() # comment if check every frame
    
    def position_to_note(self,cell, id):
        y_index = cell.col
        print(f"position: {y_index}")
        note = REFERENCE_NOTE + y_index
        instrument = ID_TO_INSTRUMENT[id]
        length = NOTE_DURATION_IN_SEC
        volume = 80
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
        # print(key)


# Release the video capture object and close all windows
cap.release()
end_synth_thread_flag = True
cv2.destroyAllWindows()


"""
# min bounding rect

        # idx_min = np.argmin(np.sum(corners, axis=1))
        # min_pos = corners[idx_min]

        # x = int(min_pos[0])
        # y = int(min_pos[1])

        # rect = cv2.minAreaRect(corners)
        # (x2, y2), (width, height), angle = rect
        # width = int(width)
        # height = int(height)

        # print("min", width, height)

        # cv2.rectangle(frame,(x,y),(x+width,y+height),(0,255,255),2)
"""