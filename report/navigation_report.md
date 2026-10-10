The formatted writeup, in the same layout as the Lab 1 PDF, is
`CSE398_Lab3a_Report.pdf` in this folder.

# How TurtleBot3 Semantic Navigation Works

This report explains the navigation pipeline. My code and demo are in
[LeoXu227/turtlebot3-gazebo-navigation-hw](https://github.com/LeoXu227/turtlebot3-gazebo-navigation-hw).
The course starter I forked is
[YiyuchenHu/turtlebot3-gazebo-navigation-hw](https://github.com/YiyuchenHu/turtlebot3-gazebo-navigation-hw).
The robot explores a Gazebo room, builds a map, remembers the objects it sees,
and later drives to one of those objects when a text command arrives.

The only student code in the graded assignment is `load()` and `infer()` in
`src/tb3_detector/tb3_detector/detector_core.py`. Everything else described
below is provided by the course and was already working.

## What a command can say

The system does not use a language model. A short rule parser in
`src/tb3_query/tb3_query/query_core.py` accepts a fixed set of phrases:

| What you type | What it means |
|---|---|
| `go to person` | nearest saved person |
| `go to person 2` | the landmark whose id is `person_2` |
| `go to trash can` | nearest saved trash can |
| `go to chair` | nearest saved chair |

Phrases such as "the person wearing a green shirt" or "the red chair" are
rejected. Color and clothing are not part of the grammar. The parser lowercases
the text, drops filler words (`go`, `to`, `the`, `please`, and so on), and
looks for one of the three target names. `trash can`, `trashcan`, and `bin`
all map to `trash_can`. A number after the name selects that landmark id.
`person_2`, `person 2`, and `person2` are the same request.

The names come from `src/tb3_bringup/config/semantic_targets.yaml`. Each entry
has a human name (`semantic_name`) and the label the detector must emit
(`detector_label`). With the shipped fine-tuned weights those two strings
match: `person`, `trash_can`, and `chair`.

## The design: map first, query later

A command is a lookup, not a search. The robot has to have already seen the
object and saved it as a landmark. If you send `go to person` before any
person marker exists, the coordinator answers `no active person in memory`
and goes back to exploring.

```text
camera image
    -> YOLO detector (boxes)
    -> localizer (box center + LiDAR range -> map x, y)
    -> short-term memory, then semantic map memory
    -> landmark such as person_0

later:

"go to person" on /user_command
    -> parser
    -> pick the nearest person landmark (or person_N)
    -> approach pose about 0.5 m in front of it
    -> Nav2 drives there
    -> TARGET_REACHED, then exploration resumes
```

## From the camera to a point on the map

Gazebo simulates the room and the TurtleBot3 Waffle Pi. The robot's camera
publishes `/camera/image_raw`. `DetectorCore.infer()` runs the fine-tuned
YOLO model `tb3det_yolo26n.pt` on each frame and returns boxes in the original
image pixels:

- `label`: `person`, `trash_can`, or `chair`
- `conf`: confidence from 0 to 1
- `bbox_xyxy`: top-left and bottom-right corners
- `track_id`: unused in the course configuration

The shipped confidence threshold is 0.40. Boxes below that, and labels outside
the three-class whitelist, are dropped.

The localizer does not use the whole box. It takes the horizontal center of
the box, maps that pixel across the camera's 62.2 degree field of view to get
a bearing, then reads a small window of LiDAR ranges around that bearing and
takes the median. Bearing plus range becomes an `(x, y)` point in the robot
frame, which is then transformed into the map built by SLAM Toolbox.

That is why a bad box sends the robot the wrong way: a shifted box is a wrong
bearing. It is also why some objects cannot be landmarks even if the camera
sees them. The LiDAR scan is a thin plane near the floor. A thin pole or a
tabletop above that plane does not return a trustworthy range. The course
kept person, trash can, and chair because each one is both recognizable in
the camera and solid in that scan plane.

## How a sighting becomes a landmark

One detection is not enough. Semantic map memory collects repeated
observations of the same place and only then promotes a landmark:

- a person needs 8 observations
- a chair or a trash can needs 12
- the observations must arrive within about 45 seconds

Until then the object is only a candidate. RViz shows a promoted landmark as
a green sphere with a name such as `person_0 (n=11)`. The number is how many
times that landmark has been seen, not a confidence score.

Landmark ids are memory slots, not permanent identities. The first person
that is promoted is `person_0`, the next distinct one is `person_1`, and so
on. They are not "the person in the green shirt."

While this is happening, frontier exploration keeps the robot driving toward
unmapped edges of the room, and SLAM Toolbox grows the occupancy map. Nav2
is what actually moves the wheels, both for exploration and for a later
`go to` command.

## What happens after you type a command

The command is published once:

```bash
ros2 topic pub --once /user_command std_msgs/String "data: 'go to person'"
```

`semantic_query_node` parses it and selects a landmark.

- With no number, it picks the matching object closest to the robot.
- With a number, it looks up that exact id, for example `person_2`. If that
  id is not in memory, the query fails and lists the ids that do exist.

The coordinator then switches from `EXPLORING` to `SEMANTIC_NAV`. The nav
adapter computes a pose about 0.5 m short of the object, facing it, so the
robot stops in front of the target instead of driving into it. Nav2 receives
that pose. On success the coordinator logs `TARGET_REACHED` and resumes
exploration a few seconds later.

`TARGET_REACHED` only means Nav2 reported that it reached its own goal. The
assignment's real check is stricter: the robot should finish within 1.2 m of
the true object in Gazebo. The 1.2 m budget covers the 0.5 m standoff, the
fact that LiDAR hits the near surface of the object rather than its center,
and Nav2's own goal tolerance.

## What this laptop did

The detector implementation loaded `tb3det_yolo26n.pt` and published person
boxes with confidence around 0.95–0.99. RViz showed the green box in the
Detector Debug Image and the green landmark spheres on the map.

In the person world (`warehouse_models_person`):

- On an earlier run, `go to person` selected the nearest landmark, `person_0`,
  and logged `TARGET_REACHED`. `go to person 2` reached `person_2` at map
  goal `(1.62, 1.70)` and logged `TARGET_REACHED`.
- `go to person 1` was accepted three times and each time Nav2 timed out
  after 60 seconds at the same approach pose `(-0.30, -0.01)`. The robot
  circled the person's feet and never finished. The lab TA described this as
  an intermittent Nav2 problem that also happens with the reference
  solution, not as a bug in the detector.

Trash cans and chairs use the same pipeline, with a stricter memory rule: 12
sightings inside about 45 seconds, instead of 8 for a person. On this laptop
the camera only delivers a few frames per second, so those candidates expired
before they became landmarks. The demo stays in the person world.

The demo video is a screen capture of the RViz desktop from a later run of
this same person world. Five person landmarks were already on the map. `go to person`
selected the nearest one, `person_1`, which was only 0.06 m away, so the nav
adapter skipped that goal and the robot did not move. The two commands that
did drive are the ones in the video:

- `go to person 0` sent Nav2 to `(-1.65, 1.65)`. The goal succeeded and the
  coordinator logged `TARGET_REACHED`.
- `go to person 2` sent Nav2 to `(1.60, -1.57)`. That goal also succeeded
  and logged `TARGET_REACHED`.

The clip keeps those two drives and cuts the exploration in between.
