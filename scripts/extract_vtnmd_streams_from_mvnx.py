# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

"""
This script:
- stream parses MVNX files
- extracts calibrated inertial representations from concerned body segments (right arm, right leg, left arm, left leg, torso)
- generates canonical VT-NMD processed CSVs as used in original VT-NMD dataset
"""

import os
import traceback
import xml.etree.ElementTree as ET

import numpy as np
import pandas as pd

MVNX_FOLDER = r"/path/to/mvnx_dataset"
OUTPUT_FOLDER = r"/path/to/output_processed"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

TAGS_TO_EXTRACT = [
    "orientation",
    "angularVelocity",
    "acceleration"
]

# ============================================================
# SEGMENT GROUPS
# ============================================================

SEGMENT_GROUPS = {
    "right_arm": [
        "RightUpperArm",
        "RightForeArm",
        "RightHand"
    ],

    "left_arm": [
        "LeftUpperArm",
        "LeftForeArm",
        "LeftHand"
    ],

    "right_leg": [
        "RightUpperLeg",
        "RightLowerLeg",
    ],

    "left_leg": [
        "LeftUpperLeg",
        "LeftLowerLeg",
    ],

    "torso": [
        "T8"
    ]
}

#XML helpers
def detect_namespace(root_tag):
    if root_tag.startswith("{"):
        uri = root_tag.split("}")[0].strip("{")
        return {"xsens": uri}

    return {}


def safe_float_list(text):
    parts = text.strip().split()
    out = []
    for p in parts:
        try:
            out.append(float(p))
        except Exception:
            out.append(float("nan"))
    return out



#MVNX stream parser
def stream_parse_mvnx(file_path, target_segments):
    print(f"\nProcessing: {os.path.basename(file_path)}")
    try:
        context = ET.iterparse(
            file_path,
            events=("start", "end")
        )
        _, root = next(context)
    except Exception as e:
        print(f"Failed opening file: {e}")
        return []

    ns = detect_namespace(root.tag)

    segments = [
        seg.attrib.get("label")
        for seg in root.findall(".//xsens:segment", ns)
    ]

    print(f"Segments found: {len(segments)}")
    frame_tag = f"{{{ns['xsens']}}}frame"

    rows = []
    frame_count = 0

    try:
        for event, elem in context:
            if event == "end" and elem.tag == frame_tag:
                frame_index = elem.attrib.get("index")
                try:
                    frame_index = int(frame_index)
                except Exception:
                    frame_index = frame_count

                row = {
                    "frame_index": frame_index
                }
                frame_count += 1

                #Tag extraction step
                for tag in TAGS_TO_EXTRACT:

                    xml_elem = elem.find(
                        f"xsens:{tag}",
                        ns
                    )
                    step = 4 if tag == "orientation" else 3

                    #Missing XML block handling step
                    if (
                        xml_elem is None
                        or not xml_elem.text
                        or not xml_elem.text.strip()
                    ):

                        for seg in target_segments:
                            if tag == "orientation":
                                axes = ["w", "x", "y", "z"]
                            else:
                                axes = ["x", "y", "z"]

                            for axis in axes:
                                row[f"{seg}_{tag}_{axis}"] = float("nan")
                        continue

                    #Safe float parsing
                    values = safe_float_list(
                        xml_elem.text
                    )

                    expected = len(segments) * step

                    #Pad shorter frames
                    if len(values) < expected:
                        pad = expected - len(values)
                        values += [float("nan")] * pad
                        print(
                            f"Frame {frame_index}: "
                            f"padded {pad} NaNs "
                            f"for tag '{tag}'"
                        )

                    #Extracting target segments
                    for i, seg in enumerate(segments):

                        if seg not in target_segments:
                            continue

                        start = i * step
                        end = start + step

                        seg_vals = values[start:end]

                        if len(seg_vals) < step:

                            seg_vals += [
                                float("nan")
                            ] * (step - len(seg_vals))

                        if tag == "orientation":
                            axes = ["w", "x", "y", "z"]
                        else:
                            axes = ["x", "y", "z"]

                        for axis_i, axis in enumerate(axes):

                            row[
                                f"{seg}_{tag}_{axis}"
                            ] = seg_vals[axis_i]

                rows.append(row)

                #Log streaming progress
                if frame_count % 4000 == 0:

                    print(
                        f"   --> {frame_count} "
                        f"frames parsed..."
                    )
                elem.clear()

    except Exception as e:

        #Log XML corruption if any
        print(
            f"XML corruption in "
            f"{os.path.basename(file_path)}"
        )
        traceback.print_exc()
        return []

    print(f"Done: {frame_count} frames parsed.")
    return rows

#Processing
def process_dataset():
    mvnx_files = [
        f for f in os.listdir(MVNX_FOLDER)
        if (
            f.endswith(".mvnx")
            and f not in SKIP_FILES
        )
    ]

    if not mvnx_files:
        print("No MVNX files found.")
        return

    #Per file processing
    for fname in mvnx_files:
        fpath = os.path.join(
            MVNX_FOLDER,
            fname
        )

        print("\n================================================")
        print(f"FILE: {fname}")
        print("================================================")

        # Per segment group processing
        for group_name, segments in SEGMENT_GROUPS.items():
            print(f"\n--> Extracting: {group_name}")

            try:
                rows = stream_parse_mvnx(
                    fpath,
                    segments
                )
                if not rows:
                    print(
                        f"No valid rows for "
                        f"{group_name}"
                    )
                    continue

                df = pd.DataFrame(rows)

                out_name = (
                    fname.replace(
                        ".mvnx",
                        f"_{group_name}.csv"
                    )
                )

                out_path = os.path.join(
                    OUTPUT_FOLDER,
                    out_name
                )

                df.to_csv(
                    out_path,
                    index=False,
                    float_format="%.6f"
                )

                print(
                    f"Saved: {out_path} "
                    f"({len(df)} frames)"
                )
            except Exception as e:

                print(
                    f"Failed processing "
                    f"{group_name}: {e}"
                )
                traceback.print_exc()

if __name__ == "__main__":
    process_dataset()