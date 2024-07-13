# Documentation
<!-- 
Search for scientific papers that describe the concept and/or implementation of
new interaction techniques. Demonstration and short paper tracks of conferences
such as UIST, EICS, MobileHCI, and CHI might be a good starting point. You can
also use projects that were discussed in our journal club. First, collect papers you
find interesting. Then, exclude everything that is not possible to be implemented
within two weeks, for example because of hardware requirements, or because you
would have to gather a lot of training data first. However, feel free to build upon
existing code and/or training data. Then, decide which prototype you want to
implement and/or extend.
Document decision process, implementation, and usage of your prototype 
-->
- Extension of [^1] with inspiration from [^2]
  - Audio d-touch aims to make tangible interaction with music accessible by detecting markers using only a camera. They created a stave sheet, a drum machine and sequencer to demonstrate their techniques 
  - Color Singer uses LEGOs to create simple songs. They map color to notes and then detect the differing brightness levels of the blocks using light sensor. This allows users to build music.
  - see [sources](#sources)

## Process

#### 1. Research and discussion
- look at different paper with several constraints (independent)
  - is it doable in two weeks (or rather one after research and planning/discussion)
  - is the interaction fun (to use or to develop)
  - how good is the explanation of how it works given in the paper
  - what materials or hardware/software are used and how accessible are they in a short amount of time 
- discussion within the team
  - explanation of the found papers
  - brainstorming on how it could be implemented and what materials it uses
  - narrowing it down with using similar constraints as above
  - 
#### 2. Decision
Reasons for the decision where:
- the original paper (audio-d touch) had an interesting concept, that is still very extendable (and gives room for creativity)
- makes use of tangibles which give the user easy feedback, don't require written explanation and are fun to use. In short are very user friendly
- the interaction would give real time feedback, which makes it fun to play with and to develop as you can test your way around
- the accessibility of the method used by audio-d touch was also a big part of the decision:
  - it seemed doable in two weeks
  - very hardware oriented and technical prototypes are interesting, but seem very far away from both a user and developer perspective. This techniques provides a interface that is easy to understand and to use
- it seemed doable in two weeks
- it does not require (re-)learning a skill (e.g. app development)
- use of materials, that we already had at home (no dependency on hardware + reusing existing products)

# Implementation
### Design decisions
- use of markers as in [^1], but with the added flexibility of using LEGOs as [^2] suggested.
  - markers would make the prototype more flexible in terms of extending the range of detectable notes and more robust against lighting situations.
- use of LEGO duplo blocks as they are easier to handle (not as tight a connection) and detect (bigger size)
  - the blocks are used sideways, to the smooth sides can be use to stick markers on them
  - they can also be used to build stacks of notes. This can be used to create and move a groups of notes or extend the length of 1 note
- 1 color = 1 marker id = 1 "instrument"
- no marker = pause
- markers are detected using a "grid", similar to a midi
  - x-axis = time
  - y-axis = pitch
  - if the middle of a marker is inside a cell it maps that cell and it's position to a note
  - ![](/img/design-idea.png)
- degrees of freedom are time, pitch, instrument

### Problems
- the marker detection is dependent on the markers being big enough
  - decision on using duplo blocks instead of normal ones
  - camera needs to be close enough, which does limit the length of the track
  - TODO: comparison picture
- the detection is dependent on the markers having a white border (which does reduce the size of the marker a little bit)
  - we did a short test without the border, which showed that the marker where not detected reliably
  - interestingly enough if the color of the lego bricks was light enough (i.e. yellow or brighter) the color of the blocks was enough of a border to detect the markers (most of the time).
  - ![](/img/duplo_border(less).png)

### How it works
#### Detection
- [ ] TODO: see [positionserkennung](#positionserkennung) 
- creates a grid across the frame as a reference point of where the markers are placed
  - the grids dimensions are based on the LEGO pieces and their known dimensions
  - press <kbd>enter</kbd> when you are ready to start
  - when the first marker gets detected the application calculates the LEGOs relative size in pixels and sets the grids cells to that size
  - it uses the known dimensions of the marker (i.e. 16mmx16mm) and its detected pixel size to create a multiplier to convert mm to pixels
  - then converts the known dimensions of the lego pieces using that multiplier.
- after the grid is created the main loop of the application starts
  - a threaded timer loops over the column of the grid
  - uses the center of the markers to check which cell they are inside of
  - press <kbd>space</kbd> to (un-)pause the loop
![](/img/lego-dimensions.png)

#### Music
- [ ] TODO

# Usage
- [ ] TODO: explanation
- [ ] TODO: video


---

### Notes
#### Setup
- Kamera ca. halber Meter über Tisch

#### Positionserkennung
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

---
### Sources
[^1]: Costanza, E., Shelley, S. B. & Robinson, J. (2003). INTRODUCING AUDIO D-TOUCH: A TANGIBLE USER INTERFACE FOR MUSIC COMPOSITION AND PERFORMANCE. Conference On Digital Audio Effects. http://intuac.com/userport/john/pubs/dtouchdafx.pdf 

[^2]: Qiuyu Lu, Zhang Yin, Jingtian Fu, Naixuan Du, and Yingqing Xu. 2024. Color Singer: Composing Music via the Construction of LEGO Blocks with Various Colors. In Extended Abstracts of the 2024 CHI Conference on Human Factors in Computing Systems (CHI EA '24). Association for Computing Machinery, New York, NY, USA, Article 639, 1–2. https://doi.org/10.1145/3613905.3649120 