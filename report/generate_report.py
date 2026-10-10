#!/usr/bin/env python3
"""Generate CSE398 Lab 3a report in the same layout as the Lab 1 report."""

from __future__ import annotations

from pathlib import Path

from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Image,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
)

ROOT = Path(__file__).resolve().parent
OUT_PDF = ROOT / "CSE398_Lab3a_Report.pdf"
FIG = ROOT / "figures"
GITHUB = "https://github.com/LeoXu227/turtlebot3-gazebo-navigation-hw"
CODE = (
    GITHUB
    + "/blob/main/src/tb3_detector/tb3_detector/detector_core.py"
)
DEMO = GITHUB + "/blob/main/report/navigation_demo.mp4"


def styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "TitleCustom", parent=base["Title"], fontSize=15, leading=18,
            alignment=TA_CENTER, spaceAfter=6,
        ),
        "h1": ParagraphStyle(
            "H1Custom", parent=base["Heading1"], fontSize=12, leading=15,
            spaceBefore=8, spaceAfter=4,
        ),
        "h2": ParagraphStyle(
            "H2Custom", parent=base["Heading2"], fontSize=10.5, leading=13,
            spaceBefore=6, spaceAfter=3,
        ),
        "body": ParagraphStyle(
            "BodyCustom", parent=base["BodyText"], fontSize=10, leading=13,
            alignment=TA_JUSTIFY, spaceAfter=6,
        ),
        "caption": ParagraphStyle(
            "CaptionCustom", parent=base["Normal"], fontSize=8, leading=10,
            alignment=TA_CENTER, spaceAfter=6, textColor="#333333",
        ),
        "meta": ParagraphStyle(
            "MetaCustom", parent=base["Normal"], fontSize=10, leading=12,
            alignment=TA_CENTER, spaceAfter=3,
        ),
    }


def maybe_image(path: Path, width=5.6 * inch, max_height=2.4 * inch):
    s = styles()
    if not path.is_file():
        return Paragraph(f"[Missing figure: {path.name}]", s["caption"])
    img = Image(str(path))
    aspect = img.imageHeight / float(img.imageWidth)
    img.drawWidth = width
    img.drawHeight = width * aspect
    if img.drawHeight > max_height:
        scale = max_height / img.drawHeight
        img.drawWidth *= scale
        img.drawHeight *= scale
    return img


def build():
    FIG.mkdir(parents=True, exist_ok=True)
    s = styles()
    doc = SimpleDocTemplate(
        str(OUT_PDF), pagesize=letter,
        leftMargin=0.7 * inch, rightMargin=0.7 * inch,
        topMargin=0.65 * inch, bottomMargin=0.65 * inch,
    )
    story = []

    story.append(Paragraph("CSE398/498 Generative AI for Healthcare &amp; Robotics", s["meta"]))
    story.append(Paragraph("Lab 3a Report", s["title"]))
    story.append(Paragraph(
        "Gazebo simulation: language command to semantic navigation",
        s["meta"],
    ))
    story.append(Paragraph(
        "Xiyuan Xu &nbsp;|&nbsp; Due Oct 5, 2026 &nbsp;|&nbsp; Instructor: M. Chuah",
        s["meta"],
    ))
    story.append(Paragraph(
        f"My GitHub: <font color='blue'><u>{GITHUB}</u></font>",
        s["meta"],
    ))
    story.append(Spacer(1, 8))

    story.append(Paragraph("What I implemented", s["h1"]))
    story.append(Paragraph(
        "The only program I wrote for this lab is "
        "<font face='Courier'>load()</font> and <font face='Courier'>infer()</font> in "
        f"<font color='blue'><u><link href='{CODE}'>src/tb3_detector/tb3_detector/detector_core.py</link></u></font>. "
        "Everything else in the repository is the course starter. I did not change the parser, "
        "the localizer, the map memory, or Nav2.",
        s["body"],
    ))
    story.append(Paragraph(
        "<b>load()</b> runs once at startup. It raises an error if ultralytics is missing or if "
        "the weights file is missing. Otherwise it loads "
        "<font face='Courier'>tb3det_yolo26n.pt</font> and moves the model onto the configured device.",
        s["body"],
    ))
    story.append(Paragraph(
        "<b>infer()</b> runs that model on one camera image. It keeps a box only when the label "
        "is in the class filter, and it returns a list of label, confidence, and box corners in "
        "the original image pixels. If <font face='Courier'>load()</font> was never called, it "
        "raises an error instead of pretending there were no objects.",
        s["body"],
    ))
    story.append(Paragraph(
        "The demo recording is "
        f"<font color='blue'><u><link href='{DEMO}'>report/navigation_demo.mp4</link></u></font> "
        "in the same repository. It shows <font face='Courier'>go to person 0</font> and then "
        "<font face='Courier'>go to person 2</font>. The figures later in this report are frames "
        "from that file, and the mp4 is also attached to this PDF.",
        s["body"],
    ))

    story.append(Paragraph("1. How a command becomes a goal", s["h1"]))
    story.append(Paragraph(
        "This lab is not a language model. A short rule parser reads one text command, "
        "looks up an object the robot has already saved on its map, and asks Nav2 to drive "
        "to a pose in front of that object. The robot has to see the object first. A command "
        "sent before any matching landmark exists fails with "
        "<font face='Courier'>no active … in memory</font> and exploration continues.",
        s["body"],
    ))
    story.append(Paragraph(
        "The command is published once on <font face='Courier'>/user_command</font>. "
        "<font face='Courier'>parse_command()</font> in "
        "<font face='Courier'>tb3_query/query_core.py</font> lowercases the text, drops filler "
        "words (<i>go</i>, <i>to</i>, <i>the</i>, <i>please</i>), and keeps one target name plus "
        "an optional number. <font face='Courier'>semantic_targets.yaml</font> maps that name to "
        "the detector label. No number means the nearest saved landmark. "
        "<font face='Courier'>person 2</font>, <font face='Courier'>person_2</font>, and "
        "<font face='Courier'>person2</font> are the same request.",
        s["body"],
    ))
    story.append(Paragraph(
        "Phrases the parser accepts: <font face='Courier'>go to person</font>, "
        "<font face='Courier'>go to person N</font>, <font face='Courier'>go to trash can</font> "
        "(also <i>trashcan</i> or <i>bin</i>), and <font face='Courier'>go to chair</font>. "
        "Color and clothing are not in the grammar, so “person wearing a green shirt” and "
        "“red chair” are rejected.",
        s["body"],
    ))
    story.append(Paragraph(
        "The graded student code is <font face='Courier'>load()</font> and "
        "<font face='Courier'>infer()</font> in <font face='Courier'>detector_core.py</font>. "
        "<font face='Courier'>load()</font> opens the fine-tuned weights "
        "<font face='Courier'>tb3det_yolo26n.pt</font>. <font face='Courier'>infer()</font> runs "
        "that YOLO model on one camera image and returns boxes. Everything after the box "
        "(LiDAR, memory, and Nav2) is course code.",
        s["body"],
    ))

    story.append(Paragraph("1.1 From the camera to a point on the map", s["h2"]))
    story.append(Paragraph(
        "Gazebo simulates the room and a TurtleBot3 Waffle Pi. SLAM Toolbox builds the "
        "occupancy map while frontier exploration drives toward unmapped edges. The camera "
        "publishes <font face='Courier'>/camera/image_raw</font>. "
        "<font face='Courier'>infer()</font> returns, for each box, a label "
        "(<font face='Courier'>person</font>, <font face='Courier'>trash_can</font>, or "
        "<font face='Courier'>chair</font>), a confidence, and pixel corners. The shipped "
        "threshold is 0.40. Boxes below that, and any other label, are dropped.",
        s["body"],
    ))
    story.append(Paragraph(
        "The localizer does not use the whole box. It takes the horizontal center, maps that "
        "pixel across the camera’s 62.2° field of view to get a bearing, then takes the median "
        "LiDAR range in a small window around that bearing. Bearing plus range becomes an "
        "(x, y) point, which is transformed into the SLAM map. A shifted box is a wrong bearing, "
        "so a bad detection sends the robot the wrong way.",
        s["body"],
    ))
    story.append(Paragraph(
        "One detection is not a landmark. Memory promotes a place only after repeated sightings "
        "inside about 45 seconds: <b>8</b> for a person, <b>12</b> for a chair or a trash can. "
        "Until then it is only a candidate. RViz draws a promoted landmark as a green sphere, "
        "for example <font face='Courier'>person_0 (n=11)</font>. The number is how many times "
        "that spot has been seen. The id is a memory slot, not a permanent identity: the first "
        "person saved is <font face='Courier'>person_0</font>, the next distinct one is "
        "<font face='Courier'>person_1</font>, and so on.",
        s["body"],
    ))

    story.append(PageBreak())

    story.append(Paragraph("1.2 What happens after the command", s["h2"]))
    story.append(Paragraph(
        "I publish the command with:",
        s["body"],
    ))
    story.append(Paragraph(
        "<font face='Courier'>ros2 topic pub --once /user_command std_msgs/String "
        "\"data: 'go to person'\"</font>",
        s["body"],
    ))
    story.append(Paragraph(
        "The query node picks the landmark. The coordinator leaves "
        "<font face='Courier'>EXPLORING</font> and enters "
        "<font face='Courier'>SEMANTIC_NAV</font>. The nav adapter places a goal about "
        "<b>0.5 m</b> in front of the object, facing it, so the robot stops short instead of "
        "driving into it. Nav2 drives there. On success the log says "
        "<font face='Courier'>TARGET_REACHED</font>, then exploration resumes a few seconds later.",
        s["body"],
    ))
    story.append(Paragraph(
        "<font face='Courier'>TARGET_REACHED</font> only means Nav2 reached its own goal. The "
        "assignment’s check is stricter: the robot should finish within <b>1.2 m</b> of the true "
        "object in Gazebo. That budget covers the 0.5 m standoff, the fact that LiDAR hits the "
        "near surface rather than the center, and Nav2’s own goal tolerance.",
        s["body"],
    ))

    story.append(Paragraph("2. What I ran", s["h1"]))
    story.append(Paragraph(
        "I ran the person world, <font face='Courier'>warehouse_models_person</font>, in Docker "
        "on a Mac (Apple silicon, Rosetta, software graphics). After the robot spawned I closed "
        "the Gazebo window and used RViz. The detector loaded "
        "<font face='Courier'>tb3det_yolo26n.pt</font> and published person boxes around "
        "0.95–0.99 confidence. RViz showed the green detection box and the green landmark spheres.",
        s["body"],
    ))
    story.append(Paragraph(
        "<b>What worked.</b> On one run, <font face='Courier'>go to person</font> selected the "
        "nearest landmark, <font face='Courier'>person_0</font>, and logged "
        "<font face='Courier'>TARGET_REACHED</font>. "
        "<font face='Courier'>go to person 2</font> reached "
        "<font face='Courier'>person_2</font> at map goal (1.62, 1.70) and also logged "
        "<font face='Courier'>TARGET_REACHED</font>.",
        s["body"],
    ))
    story.append(Paragraph(
        "<b>What failed.</b> <font face='Courier'>go to person 1</font> was accepted three times. "
        "Each time Nav2 timed out after 60 seconds at the same approach pose (−0.30, −0.01). "
        "The robot circled the person’s feet and never finished. The lab TA described this as an "
        "intermittent Nav2 problem that also happens with the reference solution, not as a bug "
        "in the detector.",
        s["body"],
    ))
    story.append(Paragraph(
        "Trash cans and chairs use the same pipeline, but they need 12 sightings inside about "
        "45 seconds. On this laptop the camera only delivers a few frames per second, so those "
        "candidates expired before they became landmarks. I did not demo "
        "<font face='Courier'>go to trash can</font> or <font face='Courier'>go to chair</font>. "
        "The demo stays in the person world.",
        s["body"],
    ))

    story.append(PageBreak())

    story.append(Paragraph("2.1 Demo: two person commands", s["h2"]))
    story.append(Paragraph(
        "The demo is a screen capture of the RViz desktop, about 1 minute 50 seconds. "
        "The original file is attached to this PDF as "
        "<font face='Courier'>navigation_demo.mp4</font> "
        "(in Acrobat or Preview, open the attachments panel, the paperclip). "
        "The figures on this page and the next are frames from that same recording, "
        "so the drives are visible even if the attachment does not play. "
        "Five person landmarks were already on the map. "
        "<font face='Courier'>go to person</font> selected the nearest one, "
        "<font face='Courier'>person_1</font>, which was only 0.06 m away, so the nav adapter "
        "skipped that goal and the robot did not move. The two commands that did drive are the "
        "ones in the video. Idle exploration between them is cut out.",
        s["body"],
    ))
    story.append(Paragraph(
        "<font face='Courier'>go to person 0</font> sent Nav2 to (−1.65, 1.65). The goal "
        "succeeded and the coordinator logged <font face='Courier'>TARGET_REACHED</font>. "
        "Figure 1 is the plan toward <font face='Courier'>person_0</font>. Figure 2 is the robot "
        "after it arrived.",
        s["body"],
    ))

    left, right = FIG / "person0_path.png", FIG / "person0_arrived.png"
    if left.is_file() and right.is_file():
        story.append(Table([
            [maybe_image(left, width=3.3 * inch, max_height=2.15 * inch),
             maybe_image(right, width=3.3 * inch, max_height=2.15 * inch)]
        ], colWidths=[3.45 * inch, 3.45 * inch]))
        story.append(Paragraph(
            "Figure 1 (left). <font face='Courier'>go to person 0</font>: green Nav2 plan toward "
            "person_0, with a person box in the detector view. "
            "Figure 2 (right). After <font face='Courier'>TARGET_REACHED</font>, the robot is next "
            "to person_0.",
            s["caption"],
        ))

    story.append(Paragraph(
        "<font face='Courier'>go to person 2</font> sent Nav2 to (1.60, −1.57). That goal also "
        "succeeded and logged <font face='Courier'>TARGET_REACHED</font>. Figure 3 is the robot "
        "beside <font face='Courier'>person_2</font>. The count on that marker rose while the "
        "robot was there (n=30 in the clip), which is extra sightings of the same landmark, not "
        "a new id.",
        s["body"],
    ))
    story.append(maybe_image(FIG / "person2_arrived.png", width=5.4 * inch, max_height=2.7 * inch))
    story.append(Paragraph(
        "Figure 3. <font face='Courier'>go to person 2</font> after the goal succeeded. "
        "The robot is next to person_2. The green line is the end of the Nav2 plan.",
        s["caption"],
    ))

    story.append(PageBreak())
    story.append(Paragraph("2.2 The same demo, frame by frame", s["h2"]))
    story.append(Paragraph(
        "Top row: <font face='Courier'>go to person 0</font>, from the plan appearing "
        "to the robot arriving at person_0. Bottom row: <font face='Courier'>go to person 2</font>, "
        "from the new plan to the robot beside person_2.",
        s["body"],
    ))
    seq = [
        (FIG / "seq_p0_a.png", "0:04 — plan toward person_0"),
        (FIG / "seq_p0_b.png", "0:22 — driving to person_0"),
        (FIG / "seq_p0_c.png", "0:42 — arrived at person_0"),
        (FIG / "seq_p2_a.png", "0:58 — plan toward person_2"),
        (FIG / "seq_p2_b.png", "1:20 — driving to person_2"),
        (FIG / "seq_p2_c.png", "1:45 — arrived at person_2"),
    ]
    if all(p.is_file() for p, _ in seq):
        def cell(path, caption):
            return [
                maybe_image(path, width=2.25 * inch, max_height=1.45 * inch),
                Paragraph(caption, s["caption"]),
            ]
        row1 = [cell(seq[i][0], seq[i][1]) for i in range(3)]
        row2 = [cell(seq[i][0], seq[i][1]) for i in range(3, 6)]
        story.append(Table(
            [[c[0] for c in row1], [c[1] for c in row1],
             [c[0] for c in row2], [c[1] for c in row2]],
            colWidths=[2.35 * inch, 2.35 * inch, 2.35 * inch],
        ))
        story.append(Paragraph(
            "Figure 4. Six frames from the attached demo, in time order.",
            s["caption"],
        ))

    story.append(Paragraph("3. Conclusion", s["h1"]))
    story.append(Paragraph(
        "A text command is a lookup on a map the robot already built. The camera and YOLO say "
        "what is in view, LiDAR turns the box into a map point, and memory keeps that point only "
        "after enough repeated sightings. Nav2 then drives to a standoff pose in front of the "
        "saved landmark. On an earlier run, <font face='Courier'>go to person</font> reached "
        "<font face='Courier'>person_0</font>. The demo video shows "
        "<font face='Courier'>go to person 0</font> and "
        "<font face='Courier'>go to person 2</font>, and both logged "
        "<font face='Courier'>TARGET_REACHED</font>. "
        "<font face='Courier'>go to person 1</font> timed out at the person’s feet, which also "
        "happens with the reference solution. Chair and trash-can landmarks never formed here "
        "because the camera was too slow to collect 12 sightings in 45 seconds.",
        s["body"],
    ))

    story.append(PageBreak())

    story.append(Paragraph("Appendix", s["h1"]))
    story.append(Paragraph("AI tools", s["h2"]))
    story.append(Paragraph(
        "I used Cursor to help with the Docker/ROS setup, the detector "
        "<font face='Courier'>load()</font> and <font face='Courier'>infer()</font> implementation, "
        "report wording, and the screen capture. I ran the simulator, sent the commands, and can "
        "explain the pipeline (course AI policy).",
        s["body"],
    ))
    story.append(Paragraph("References", s["h2"]))
    story.append(Paragraph(
        f"1. My repository: {GITHUB}<br/>"
        f"2. Code I wrote: {CODE}<br/>"
        f"3. Demo video: {DEMO}<br/>"
        "4. Course starter I forked: "
        "https://github.com/YiyuchenHu/turtlebot3-gazebo-navigation-hw<br/>"
        "5. Course packages I used as provided: tb3_query, tb3_localizer, "
        "tb3_coordinator, Nav2, SLAM Toolbox. Weights: tb3det_yolo26n.pt",
        s["body"],
    ))
    story.append(Paragraph("How to rerun the person-world demo", s["h2"]))
    story.append(ListFlowable([
        ListItem(Paragraph(
            "Start the course Docker stack and launch the six terminals with "
            "<font face='Courier'>world:=warehouse_models_person</font>. Close the Gazebo window "
            "after spawn.",
            s["body"],
        )),
        ListItem(Paragraph(
            "Wait until RViz shows at least <font face='Courier'>person_0</font> and "
            "<font face='Courier'>person_2</font>.",
            s["body"],
        )),
        ListItem(Paragraph(
            "Publish <font face='Courier'>go to person 0</font>, wait for "
            "<font face='Courier'>TARGET_REACHED</font>, then publish "
            "<font face='Courier'>go to person 2</font>.",
            s["body"],
        )),
    ], bulletType="bullet", leftIndent=14))

    doc.build(story)
    print(f"Wrote {OUT_PDF}")


if __name__ == "__main__":
    build()
