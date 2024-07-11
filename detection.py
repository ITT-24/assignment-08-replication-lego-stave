import cv2
import numpy as np
import cv2.aruco as aruco

cam_id = 0

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

    # Check if marker is detected
    if border_ids is not None:
        # Draw lines along the sides of the marker
        aruco.drawDetectedMarkers(frame, border_corners)
        
        border_markers = border_corners[np.where(border_ids in [0,1,2,3])]
        print(border_markers)

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

