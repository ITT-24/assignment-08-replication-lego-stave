import cv2
import numpy as np
import cv2.aruco as aruco
import sys

# INIT VIDEO FEED
cam_id = 0
if len(sys.argv) > 1:
    cam_id = int(sys.argv[1])

aruco_dict_border = aruco.getPredefinedDictionary(aruco.DICT_6X6_100)
aruco_dict_notes = aruco.getPredefinedDictionary(aruco.DICT_4X4_100)

aruco_params = aruco.DetectorParameters()
detector_border = aruco.ArucoDetector(aruco_dict_border,aruco_params)
detector_notes = aruco.ArucoDetector(aruco_dict_notes, aruco_params)


class Lego:
    """A representation of a lego duplo piece standing on it's side. So smooth sides up."""
    def __init__(self):
        self.width_mm = 18
        self.height_mm = 31
        self.marker_mm = 16
        self.marker_size = 0
        self.padding = 20 # leniency for align

    def get_size_from_marker(self, corners, frame):
        """Use the known dimensions of the aruco marker to get the size of the lego pieces in pixels
           corners = corners of the first detected marker => all same size + distance.
           0 - 1
           |   |
           3 - 2   
        """
        rect = cv2.boundingRect(corners)
        x,y,marker_w,marker_h = rect
        cv2.rectangle(frame,(x,y),(x+marker_w,y+marker_h),(0,255,0),2)
        print("max", marker_w, marker_h)
        self.marker_size_px = (marker_w + marker_h) / 2 # get average

    def set_lego_size(self, corners):
        """Measure the rough size of the lego pieces in pixels in the frame. Uses the first detected lego"""
        # partially from: https://pysource.com/2021/05/28/measure-size-of-an-object-with-opencv-aruco-marker-and-python/
        if self.marker_size != 0:
            return # only set once (not for debug)

        int_corners = np.intp(corners)
        cv2.polylines(frame, int_corners, True, (0, 255, 0), 2) # for debug

        aruco_perimeter = cv2.arcLength(corners[0], True)
        self.marker_size = aruco_perimeter // 4

        mm_in_px = self.marker_size / self.width_mm


        # TODO: choose padding, so that frame_w/h is multiple of w/h 

        self.width_px = int(self.width_mm * mm_in_px) + self.padding
        self.height_px = int(self.height_mm * mm_in_px) + self.padding

        # print(f"lego == {self.width_px} x {self.height_px}")


class Coordinator:
    """A class that capsules the position detection of the markers"""
    
    def __init__(self):
        self.rows = 0
        self.cols = 0
        self.centers = []
        pass

    # ?? do perspective projection?
    def draw_grid(self, frame):
        """see: https://stackoverflow.com/a/37705365"""
        if lego.marker_size == 0:
            return # only draw after marker was successfully detected

        # divide the into cells using the lego size
        h, w, _ = frame.shape
        rows, cols = (h//lego.height_px, w//lego.width_px)
        # rows, cols = (w//lego.width_px, h//lego.height_px)

        color = (200, 200, 200)
        grid_x_idx = 0
        grid_y_idx = 0

        cell_width = lego.width_px
        cell_height = lego.height_px

        for x in range (0, w, cell_width):
            x = int(x)
            cv2.line(frame, (x, 0), (x, h), color=color, thickness=1)
            cv2.putText(frame, str(grid_x_idx), (x, h), cv2.FONT_HERSHEY_PLAIN, 1, color)
            grid_x_idx += 1

        for y in range (0, h, cell_height):
            y = int(y)
            cv2.line(frame, (0, y), (w, y), color=color, thickness=1)
            cv2.putText(frame, str(grid_y_idx), (0, y+12), cv2.FONT_HERSHEY_PLAIN, 1, color)
            grid_y_idx += 1


        self.rows = rows
        self.cols = cols

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

        # TODO: only re-save the centers, if the markers have moved significantly (for performance)


    def collision(self, frame):
        """Detect which cell the marker is in, see: https://stackoverflow.com/a/37705365"""

        if self.rows == 0:
            return

        for center in self.centers:
            # get which cell the center is in
            x, y = center
            row = int( x / lego.width_px )
            col = int( y / lego.height_px) 

            print(f"row: {row} + col: {col}")

            x = row * lego.width_px
            y = col * lego.height_px
            cv2.rectangle(frame, (x, y), (x+lego.width_px, y+lego.height_px), (255, 255, 255), 2)

            # cell = row * self.rows + col + 1
            # print("cell", cell)

        # check center of marker to "center of cell"
# https://stackoverflow.com/questions/37704114/drawing-numbering-and-identifying-grid-cells-in-opencv
    
# ----- INIT ----- #
lego = Lego()
coord = Coordinator()

cap = cv2.VideoCapture(cam_id, cv2.CAP_DSHOW)
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

        lego.set_lego_size(corners) 
        coord.get_marker_center(corners, frame)
        coord.collision(frame)
        # print(corners[0][0], "\n")
        # lego.get_size_from_marker(corners[0][0], frame)
        # lego.get_pixel_per_cm(corners, contours[0])
        # TODO: detect their relative/normalized position (x, y)


    coord.draw_grid(frame)

    # Display the frame
    cv2.imshow('frame', frame)

    # Wait for a key press and check if it's the 'q' key
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the video capture object and close all windows
cap.release()
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