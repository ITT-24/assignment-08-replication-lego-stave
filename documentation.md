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
  - **Audio d-touch** aims to make tangible interaction with music accessible by detecting markers using only a camera. They created a stave sheet, a drum machine and sequencer to demonstrate their technique of mapping the markers to notes.
  - **Color Singer** uses LEGOs to create simple songs. They map color to notes and then detect the differing brightness levels of the blocks using a light sensor. This allows users to build music.
  - see [sources](#sources)

## Process

#### 1. Research and discussion
- we looked at different papers with several constraints:
  - is it doable in two weeks (or rather ~1 after research and planning/discussion)
  - is the interaction fun (to use or to develop)
  - how good is the explanation of how it works given in the paper
  - what materials or hardware/software are used and how accessible are they in a short amount of time 
- discussion within the team
  - explanation of the found papers
  - brainstorming on how it could be implemented and what materials are used
  - narrowing it down using similar constraints as above
  - taking into account personal interest
  
#### 2. Decision
Reasons for the decision where:
- the original paper (audio-d touch) had an interesting concept, that is still very extendable (and gives room for creativity)
- makes use of tangibles which don't require written explanation and are fun to use
- the interaction would give real time feedback, which makes it fun to play with and to develop as you can test your way around
- the accessibility of the method used by audio-d touch was also a big part of the decision:
  - it seemed doable in two weeks
  - it uses simple materials, that don't require any more prerequisite knowledge (other than what was learned in the course), meaning that there would be no dependency on having to understand or run the hardware before development could start
  - this technique provides a tangible interface that is easy to understand and to use
  - it does not require (re-)learning a skill (e.g. app development)
  - uses materials, that we already had at home (no dependency on hardware + reusing existing things)

# Implementation
### Design decisions
- use of markers as in [^1], but with the added flexibility of using LEGOs as [^2] suggested.
  - markers would make the prototype more flexible in terms of extending the range of detectable notes and more robust against lighting situations
- use of LEGO duplo blocks as they are easier to detect (bigger size) and handle (not as tight a connection)
  - the blocks are used sideways, to the smooth sides can be used to stick markers on
  - they can also be used to build stacks of notes so you can create and move groups of notes or extend the length of a note
- 1 color = 1 marker id = 1 midi instrument
- no marker = pause
- markers are detected using a "grid", similar to a midi
  - x-axis = time
  - y-axis = pitch
  - if the middle of a marker is inside a cell it maps that cell and it's position in the grid to a note
  - ![](/img/design-idea.png)

### Problems
- the marker detection is dependent on the markers being big enough
  - decision on using duplo blocks instead of normal ones
  - camera needs to be close enough, which does limit the length of the track
- the detection is dependent on the markers having a white border (which does reduce the size of the marker a little bit)
  - we did a short test without the border, which showed that the marker where not detected reliably
  - interestingly enough if the color of the lego bricks is light enough (i.e. yellow or brighter) it can (mostly) substitute the white border
  - ![](/img/duplo_border(less).png)


### How it works
#### Detection
- creates a grid across the frame as a reference point of where the markers are placed
  - the grids dimensions are based on the LEGO pieces and their known size
  - when the first marker gets detected the application calculates the LEGOs relative size in pixels and sets the grids cells to that size
  - it uses the known dimensions of the marker (i.e. 16mmx16mm) and its detected pixel size to create a multiplier to convert mm to pixels
- after the grid is created the main loop of the application starts
  - a threaded timer loops over the columns of the grid
  - uses the center of the markers to check which cell they are inside of
  - play a generated note

![](/img/lego-dimensions.png)

#### Music
  - y-axis = pitch
  - x-axis = timing
  - markerID = midi instrument
- First try with **pyAudio**:
  - attempting to create a new mini synthesizer to get a bigger variety in sounds and instruments
  - opened an audio stream when the script is started
  - used a thread, that listens to an event to play the sounds
  - event gets triggered, when a marker gets detected and generates the sound appropriate to its position
  - had issues with playing sound at the right time and the right length
  - sound had a delay that would cause the next sound to delay as well, leading to "output underflow"
- Change to using **mido** with rtmidi-backend
  - map the pitch to a musical note
  - after sending a message to play the note, it starts a threaded timer to later send the message to end the note

# Usage
- blocks are made by sticking AruCo-Markers onto LEGO duplo bricks
  - 16mm markers with 1mm white border on each side + IDs 0, 1, 2, 3 
  - alternatively: works with just the markers as well
- set up a camera above a desk (alternatively you could use your laptops webcam and hold the blocks up to the camera)
- start the script: `py coordinator.py`
  - the camera is set to `0`, to use a different camera do: `py coordinator.py 1` 
  - to switch the vertical direction of the grid do: `py coordinator.py 0 -f` (you need to specify your camera)
- press <kbd>enter</kbd> to start the music loop
- arrange the LEGO blocks as you like (you can use the video-feed if you need help)
- press <kbd>space</kbd> to pause/play
- press <kbd>esc</kbd> or <kbd>q</kbd> to quit the application
 
# Video
- [ ] TODO: video

---
### Sources
[^1]: Costanza, E., Shelley, S. B. & Robinson, J. (2003). INTRODUCING AUDIO D-TOUCH: A TANGIBLE USER INTERFACE FOR MUSIC COMPOSITION AND PERFORMANCE. Conference On Digital Audio Effects. http://intuac.com/userport/john/pubs/dtouchdafx.pdf 

[^2]: Qiuyu Lu, Zhang Yin, Jingtian Fu, Naixuan Du, and Yingqing Xu. 2024. Color Singer: Composing Music via the Construction of LEGO Blocks with Various Colors. In Extended Abstracts of the 2024 CHI Conference on Human Factors in Computing Systems (CHI EA '24). Association for Computing Machinery, New York, NY, USA, Article 639, 1–2. https://doi.org/10.1145/3613905.3649120 
