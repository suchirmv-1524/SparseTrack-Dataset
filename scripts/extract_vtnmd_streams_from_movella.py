# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

"""
This script converts raw Movella Xsens DOT IMU streams into structured VT-NMD processed representations.
We perform:
- raw IMU stream parsing
- coordinate transformations
- T-pose calibration
as described in the calibration and frame transformation methodology described in the SparseTrack paper.
"""

from pathlib import Path

import numpy as np
import pandas as pd

RAW_ROOT = Path("/path/to/raw")
PROCESSED_ROOT = Path("/path/to/processed")
PROCESSED_ROOT.mkdir(exist_ok=True)

PROCESSING_MAP = {
    "right_arm": [
        ("right_upper_arm.csv", "RightUpperArm", "upper"),
        ("right_forearm.csv", "RightForeArm", "upper"),
    ],

    "left_arm": [
        ("left_upper_arm.csv", "LeftUpperArm", "upper"),
        ("left_forearm.csv", "LeftForeArm", "upper"),
    ],

    "right_leg": [
        ("right_thigh.csv", "RightUpperLeg", "lower"),
        ("right_shank.csv", "RightLowerLeg", "lower"),
    ],

    "left_leg": [
        ("left_thigh.csv", "LeftUpperLeg", "lower"),
        ("left_shank.csv", "LeftLowerLeg", "lower"),
    ],

    "torso": [
        ("torso.csv", "T8", "upper")
    ]
}

#Quaternion helpers
def normalize_quaternion(q):
    norm = np.linalg.norm(
        q,
        axis=1,
        keepdims=True
    )
    norm[norm < 1e-8] = 1.0
    return q / norm


def quaternion_inverse(q):
    q_inv = q.copy()
    q_inv[:, 1:] *= -1
    return q_inv


def quaternion_multiply(q1, q2):
    w1, x1, y1, z1 = q1.T
    w2, x2, y2, z2 = q2.T
    w = (
        w1 * w2
        - x1 * x2
        - y1 * y2
        - z1 * z2
    )
    x = (
        w1 * x2
        + x1 * w2
        + y1 * z2
        - z1 * y2
    )
    y = (
        w1 * y2
        - x1 * z2
        + y1 * w2
        + z1 * x2
    )
    z = (
        w1 * z2
        + x1 * y2
        - y1 * x2
        + z1 * w2
    )
    out = np.vstack([w, x, y, z]).T
    return normalize_quaternion(out)

#Frame transformations
def raw_to_global(q_raw, lower_body=False):
    w = q_raw[:, 0]
    x = q_raw[:, 1]
    y = q_raw[:, 2]
    z = q_raw[:, 3]

    if lower_body:
        q_global = np.stack([
            w,
            y,
            -x,
            -z
        ], axis=1)
    else:
        q_global = np.stack([
            w,
            y,
            -x,
            z
        ], axis=1)
    return normalize_quaternion(q_global)


def calibrate_quaternion(q_global):
    # first frame => perform calibration
    q0 = q_global[0:1]
    q_offset = quaternion_inverse(q0)
    q_offset = np.repeat(
        q_offset,
        len(q_global),
        axis=0
    )

    q_calibrated = quaternion_multiply(
        q_offset,
        q_global
    )
    return normalize_quaternion(q_calibrated)

#Raw sensor data loading
def load_raw_sensor(csv_path):
    df = pd.read_csv(csv_path)
    quat = df[[
        "Quat_W",
        "Quat_X",
        "Quat_Y",
        "Quat_Z"
    ]].values

    acc = df[[
        "FreeAcc_X",
        "FreeAcc_Y",
        "FreeAcc_Z"
    ]].values

    gyr = df[[
        "Gyr_X",
        "Gyr_Y",
        "Gyr_Z"
    ]].values

    return {
        "quat": quat,
        "acc": acc,
        "gyr": gyr
    }

#Process the sensor readings
def process_sensor(sensor, lower_body=False):

    q_global = raw_to_global(
        sensor["quat"],
        lower_body=lower_body
    )

    q_calibrated = calibrate_quaternion(
        q_global
    )

    return {
        "quat": q_calibrated,
        "acc": sensor["acc"],
        "gyr": sensor["gyr"]
    }


def write_segment(df_out, prefix, sensor):

    #Write orientations values
    df_out[f"{prefix}_orientation_w"] = sensor["quat"][:, 0]
    df_out[f"{prefix}_orientation_x"] = sensor["quat"][:, 1]
    df_out[f"{prefix}_orientation_y"] = sensor["quat"][:, 2]
    df_out[f"{prefix}_orientation_z"] = sensor["quat"][:, 3]

    #Write gyroscope values
    df_out[f"{prefix}_angularVelocity_x"] = sensor["gyr"][:, 0]
    df_out[f"{prefix}_angularVelocity_y"] = sensor["gyr"][:, 1]
    df_out[f"{prefix}_angularVelocity_z"] = sensor["gyr"][:, 2]

    #Write accelerometer values
    df_out[f"{prefix}_acceleration_x"] = sensor["acc"][:, 0]
    df_out[f"{prefix}_acceleration_y"] = sensor["acc"][:, 1]
    df_out[f"{prefix}_acceleration_z"] = sensor["acc"][:, 2]

def add_hand_placeholders(df_out, side):
    n = len(df_out)
    zeros = np.zeros(n)
    prefix = f"{side}Hand"

    #orientation
    df_out[f"{prefix}_orientation_w"] = 1.0
    df_out[f"{prefix}_orientation_x"] = 0.0
    df_out[f"{prefix}_orientation_y"] = 0.0
    df_out[f"{prefix}_orientation_z"] = 0.0

    #angular velocity
    df_out[f"{prefix}_angularVelocity_x"] = zeros
    df_out[f"{prefix}_angularVelocity_y"] = zeros
    df_out[f"{prefix}_angularVelocity_z"] = zeros

    #acceleration
    df_out[f"{prefix}_acceleration_x"] = zeros
    df_out[f"{prefix}_acceleration_y"] = zeros
    df_out[f"{prefix}_acceleration_z"] = zeros

ARM_COLUMNS = [
    "frame_index",

    "Upper1_orientation_w",
    "Upper1_orientation_x",
    "Upper1_orientation_y",
    "Upper1_orientation_z",

    "Lower1_orientation_w",
    "Lower1_orientation_x",
    "Lower1_orientation_y",
    "Lower1_orientation_z",

    "Hand1_orientation_w",
    "Hand1_orientation_x",
    "Hand1_orientation_y",
    "Hand1_orientation_z",

    "Upper1_angularVelocity_x",
    "Upper1_angularVelocity_y",
    "Upper1_angularVelocity_z",

    "Lower1_angularVelocity_x",
    "Lower1_angularVelocity_y",
    "Lower1_angularVelocity_z",

    "Hand1_angularVelocity_x",
    "Hand1_angularVelocity_y",
    "Hand1_angularVelocity_z",

    "Upper1_acceleration_x",
    "Upper1_acceleration_y",
    "Upper1_acceleration_z",

    "Lower1_acceleration_x",
    "Lower1_acceleration_y",
    "Lower1_acceleration_z",

    "Hand1_acceleration_x",
    "Hand1_acceleration_y",
    "Hand1_acceleration_z",
]

#Build processed file
def build_processed_file(iteration_dir, group_name):
    sensor_configs = PROCESSING_MAP[group_name]
    df_out = pd.DataFrame()
    processed_sensors = []

    for raw_file, prefix, body_type in sensor_configs:
        raw_path = iteration_dir / raw_file
        sensor = load_raw_sensor(raw_path)
        processed_sensor = process_sensor(
            sensor,
            lower_body=(body_type == "lower")
        )
        processed_sensors.append(
            (prefix, processed_sensor)
        )

    #Write segments
    for prefix, sensor in processed_sensors:

        write_segment(
            df_out,
            prefix,
            sensor
        )

    if "arm" in group_name:
        if "right" in group_name:
            add_hand_placeholders(df_out, "Right")
        else:
            add_hand_placeholders(df_out, "Left")

    df_out.insert(
        0,
        "frame_index",
        np.arange(len(df_out))
    )

    return df_out

#Process files per iteration
def process_iteration(iteration_dir):
    relative_name = iteration_dir.name
    output_dir = PROCESSED_ROOT / relative_name
    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )
    print("\n================================================")
    print(f"[ITERATION] {relative_name}")
    print("================================================")

    for group_name in PROCESSING_MAP.keys():
        print(f"[INFO] Building {group_name}.csv")

        df_out = build_processed_file(
            iteration_dir,
            group_name
        )

        output_path = (
            output_dir / f"{group_name}.csv"
        )

        df_out.to_csv(
            output_path,
            index=False,
            float_format="%.6f"
        )

        print(f"--> Saved: {output_path}")

def main():
    iteration_dirs = sorted([

        d for d in RAW_ROOT.iterdir()
        if d.is_dir()
    ])

    if not iteration_dirs:
        print("[WARNING] No iteration folders found.")
        return

    for iteration_dir in iteration_dirs:

        process_iteration(iteration_dir)
    print("\n================================================")
    print("[DONE] Raw --> processed conversion complete.")
    print("================================================")

if __name__ == "__main__":
    main()