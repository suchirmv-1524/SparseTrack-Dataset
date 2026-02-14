# SparseTrack Dataset

SparseTrack Dataset is a sparse inertial motion capture dataset designed for real-time human motion reconstruction from sparse IMUs.

The dataset contains:

- raw reconstructed IMU streams collected using Movella sensors,
- processed VT-NMD formatted inertial representations,
- preprocessing and reconstruction utilities for dataset reproducibility.

---

# Dataset Structure

```text
SparseTrack-Dataset/
├── raw/
├── processed/
├── scripts/
├── reconstruct_raw.py
└── README.md
```

---

# Raw IMU Streams

The `raw/` directory contains reconstructed Movella-compatible IMU streams organized iteration-wise.

Each iteration contains 9 sensor streams:

```text
raw/Iteration X/
├── left_forearm.csv
├── left_shank.csv
├── left_thigh.csv
├── left_upper_arm.csv
├── right_forearm.csv
├── right_shank.csv
├── right_thigh.csv
├── right_upper_arm.csv
└── torso.csv
```

Each raw CSV contains:

- quaternion orientation,
- free acceleration,
- angular velocity,
- timestamp metadata.

Example schema:

```text
SampleTimeFine
Quat_W
Quat_X
Quat_Y
Quat_Z
FreeAcc_X
FreeAcc_Y
FreeAcc_Z
Gyr_X
Gyr_Y
Gyr_Z
Status
```

---

# Processed VT-NMD Representation

The `processed/` directory contains calibrated VT-NMD formatted inertial representations used by SparseTrack.

Each iteration contains:

```text
processed/Iteration X/
├── left_arm.csv
├── left_leg.csv
├── right_arm.csv
├── right_leg.csv
└── torso.csv
```

The processed representations contain:

- calibrated segment orientations,
- angular velocities,
- free accelerations,
- frame-wise inertial features.

---

# Calibration & Frame Transformation

Prior to every recording session, a static T-pose calibration was performed to align the sensor coordinate frames with anatomical body frames.

The preprocessing pipeline applies:

1. Coordinate frame permutation  
2. T-pose boresight calibration  
3. Quaternion normalization  

Upper-body segments use:

```text
q_global = [w, y, -x, z]
```

Lower-body segments use:

```text
q_global = [w, y, -x, -z]
```

The calibrated orientation is computed as:

```text
q_calibrated(t) = q_offset ⊗ q_global(t)
```

where the offset quaternion is obtained from the initial T-pose frame.

---

# Scripts

## MVNX → VT-NMD Extraction

```text
scripts/extract_vtnmd_streams_from_mvnx.py
```

Extracts calibrated VT-NMD representations directly from MVNX motion capture recordings.

---

## Raw → Processed Conversion

```text
scripts/raw_to_processed.py
```

Converts raw Movella-compatible IMU streams into canonical VT-NMD processed representations.

---

## Processed → Raw Reconstruction

```text
reconstruct_raw.py
```

Reconstructs Movella-compatible raw IMU streams from processed VT-NMD representations.

---

# Notes

- Minor floating-point deviations may exist between reconstructed and original processed streams due to quaternion normalization and calibration recomputation.
- Quaternion sign ambiguity may produce mathematically equivalent orientations with opposite signs.
- All CSV files are stored using fixed floating-point precision.

---

# License

This project is licensed under the license provided in the root `LICENSE` file.
