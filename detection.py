import cv2
import numpy as np
import cv2.aruco as aruco

cam_id = 1

aruco_dict_border = aruco.getPredefinedDictionary(aruco.DICT_6X6_100)
aruco_dict_notes = aruco.getPredefinedDictionary(aruco.DICT_4X4_100)

aruco_params = aruco.DetectorParameters()
detector_border = aruco.ArucoDetector(aruco_dict_border,aruco_params)
detector_notes = aruco.ArucoDetector(aruco_dict_notes, aruco_params)


def sort_points():
    global points
    origin = np.mean(points,0)
    polar = np.apply_along_axis(lambda a : to_polar(a, origin), 1, points)
    polar = polar[polar[:, 1].argsort()] # https://stackoverflow.com/a/2828121
    points = np.apply_along_axis(lambda a : to_cartesian(a, origin), 1, polar)

def to_polar(point:np.array, origin:np.array=np.array((0,0))) -> np.array:
    p_relative = point-origin
    theta = np.arctan2(p_relative[1], p_relative[0])
    r = np.sqrt(p_relative[0]**2 + p_relative[1]**2)
    return np.array((r, theta))

def to_cartesian(point:np.array, origin:np.array):
    r = point[0]
    theta = point[1]
    x = r * np.cos(theta)
    y = r * np.sin(theta)
    p_relative = np.array((x,y))
    return p_relative + origin


class Playfield():
    """
    Takes a paper with 4 AruCo markers and transforms the surface to 
    fit the video frame
    """

    def __init__(self):
        self.has_transformed = False
        self.marker_ids = [0, 1, 2, 3]
        self.prev_transform = []

    def transform_game_field(self, ids:list[list[int]], corners, frame):
        """
        Uses the outer corners of the markers on the board
        to transform the board to fit the webcam.
        Keeps the the orientation until all expected markers have been detected.
        Returns the transformed image.
        """
        
        marker_ids = self.marker_ids # expected markers
        ids = ids.flatten()
        ids.sort() 

        if len(ids) == 4 and (marker_ids == ids).all():
            c = corners
            # get the top-left corner of each marker for comparison
            m_0 = c[ids[0]][0][0] # x/y coordinates of top-left corner
            m_1 = c[ids[1]][0][0]
            m_2 = c[ids[2]][0][0]
            m_3 = c[ids[3]][0][0]

            self.prev_transform = np.float32(np.array([m_0, m_1, m_3, m_2]))

        # keep the transformation if not all markers have been reliably found
        if len(self.prev_transform) > 0:
            old_points = self.prev_transform
            height, width, c = frame.shape
            new_points = np.float32(np.array([ [0, 0], [width, 0], [width, height], [0, height] ]))

            matrix = cv2.getPerspectiveTransform(old_points, new_points )
            frame = cv2.warpPerspective(frame, matrix, (width, height))

        return frame

# Init
playfield = Playfield()

cap = cv2.VideoCapture(cam_id)
while True:
    # Capture a frame from the webcam
    ret, frame = cap.read()

    # Convert the frame to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Detect ArUco markers in the frame
    #corners, ids, rejectedImgPoints = aruco.detectMarkers(gray, aruco_dict, parameters=aruco_params)
    border_corners, border_ids, border_rejectedImgPoints = detector_border.detectMarkers(gray)

    corners, ids, rejected = detector_notes.detectMarkers(gray)

    # Check if markers for the borders are detected
    if border_ids is not None:
        # Draw lines along the sides of the marker
        aruco.drawDetectedMarkers(frame, border_corners, border_ids)

        frame = playfield.transform_game_field(border_ids, border_corners, frame)

        # border_markers = border_corners[np.where(border_ids in [0,1,2,3])]
        # print(border_ids)

    if ids is not None:
        aruco.drawDetectedMarkers(frame, corners)

    # Display the frame
    cv2.imshow('frame', frame)

    # Wait for a key press and check if it's the 'q' key
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the video capture object and close all windows
cap.release()
cv2.destroyAllWindows()

