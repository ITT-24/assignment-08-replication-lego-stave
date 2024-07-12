# Documentation



# Setup
- Kamera ca. halber Meter über Tisch

# Positionserkennung
- 12 Lego duplo Steine passen in Kamera-frame (Höhe)
- 26 Lego duplo Steine passen in Kamera-frame (Breite)
- Koordinaten normalisieren
- Mittelpunkt von Legosteinen erkennen
- Kamera in 12(h)x16(w) Grid einteilen 
  - Stein-Mittelpunkt am nächsten an Zell-Mittelpunkt/ in Zelle drin = Pitch + Zeit


`coordinator.py` has the initial implementation:
- cam id is default set to 0, to change it call `py coordinator.py 1` or similar
- creates a grid with cells that mimic the size of the lego pieces
  - uses known size of aruco markers + known size of lego pieces to parse them from millimeters to pixels
  - grid currently without perspective transform and doesn't fill the frame perfectly, but responds to different marker sizes (i.e. distances of the marker to the camera)
  - grid gets creates, when the first marker gets detected. This also starts the main loop of the application.
- The loop:
  - a threaded timer advances the timeline (i.e. what colum of cells get played)
  - every frame the application draws the timeline 
  - the timeline advances per column
  - prints the cell (row, column) with a detected marker
- Checking the cells
  - check every frame (this can get repeats)
  - check when timeline advances (this is more robust, but doesn't respond to changes as well)