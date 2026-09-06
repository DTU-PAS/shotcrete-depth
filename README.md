<h1 align="center">ShotcreteDepth: A Bi-modal Dataset for Robust Robotic Depth Perception in Shotcrete Construction Environments</h1>

<p align="center">
  <a href="https://arxiv.org/pdf/2606.23152"><img alt="Paper (arXiv)" src="https://img.shields.io/badge/Read-Paper_(arXiv)-yellow"></a>
  <a href="https://huggingface.co/datasets/dtu-pcas/shotcrete-depth"><img alt="HuggingFace" src="https://img.shields.io/badge/Download-HuggingFace-blue"></a>
</p>

This is the official repository for "ShotcreteDepth: A Bi-modal Dataset for Robust Robotic Depth Perception in Shotcrete Construction Environments", presented at [Towards Autonomous Robotic Systems](https://taros-conference.org) 2026 and authored by 
[Jakub Gregorek](https://scholar.google.com/citations?user=Afmk1FYAAAAJ), 
[Lars Arnold Dethlefsen](https://github.com/MrArnoldi),
[Patrick Schmidt](https://scholar.google.com/citations?user=phH_B4sAAAAJ),
Mads Essenbæk,
Jonas Flink Bentzen,
and [Lazaros Nalpantidis](https://lanalpa.github.io).

## Dataset

We are releasing the "ShotcreteDepeth" dataset capturing a shotcreting and construction environment.
The dataset is aimed at development and evaluation of stereo matching, depth completion and depth estimation methods.

### Download

The dataset is available at [data.dtu.dk](https://data.dtu.dk/articles/dataset/ShotcreteDepth_A_Bi-modal_Dataset_for_Robust_Robotic_Depth_Perception_in_Shotcrete_Construction_Environments/32230827/1).
We are providing the following files:

- [RAW dataset & annotations (shotcrete-depth-raw.zip, 40 GB)](https://data.dtu.dk/ndownloader/files/64410741) - can be edited by the provided annotation tool
- [Evaluation Set (shotcrete-depth.zip, 789 MB)](https://data.dtu.dk/ndownloader/files/64410525) - only the evaluation set composed of 220 samples

Alternatively, the evaluation set can be retrieved from HuggingFace 🤗.

```python
from datasets import load_dataset, Split
ds = load_dataset("dtu-pcas/shotcrete-depth", split=Split.TEST).with_format("numpy")
```
Since the dataset hosted on HuggingFace does not include the calibration files, we are providing the camera's focal length (1075.6800537109375) and the stereo baseline (0.15944470465183258) here.

The dataset is licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/deed.en) license.

### Overview

| Parameter                | Description/Value               |
|--------------------------|---------------------------------|
| Stereo Camera            | Roboception rc visard 160 color |
| - Field of View          | Horizontal: 61°, Vertical: 48°  |
| – Image Resolution       | 1280 × 960                      |
| – Disparity Resolution   | 640 × 480                       |
| LiDAR                    | Velodyne PUCK                   |
| – Field of View          | Vertical: 30°                   |
| – Depth Resolution       | 1280 × 960                      |
| - Total Dataset Size     | 11252                           |
| - Annotated Dataset Size | 220                             |

### Data Structure

The RAW dataset has the following structure:

```
.
├── dataset/
│   ├── ROSBAG1/
│   │   ├── SAMPLE1.h5
│   │   ├── SAMPLE2.h5
│   │   ├── ...
│   │   └── calibration.json
│   ├── ROSBAG2/
│   │   ├── SAMPLE1.h5
│   │   ├── ...
│   │   └── calibration.json
│   └── ...
└── annotations/
    ├── ROSBAG1/
    │   ├── SAMPLE1.h5
    │   ├── SAMPLE1.json
    │   └── ...
    ├── ROSBAG2/
    │   ├── SAMPLE1.h5
    │   ├── SAMPLE1.json
    │   └── ...
    └── ...
```

H5 files in the dataset directory contain the following H5 datasets:

- rgb-left (960x1280x3)
- rgb-right (960x1280x3)
- stereo-disparity (480x640)
- stereo-confidence (480x640)
- velodyne (960x1280)

The calibration.json file contains the following matrices:

- velodyne_extrinsic
- stereo_extrinsic
- roboception_left_intrinsic

For some of the samples, annotations are provided in the annotations directory, each H5 contains only one H5 dataset:

- velodyne-annotations

The annotations are stored as 1D array of integers corresponding to the following labels:

- 0 - REMOVE_BY_ALGORITHM
- 1 - KEEP_BY_ALGORITHM
- 2 - REMOVE_BY_USER
- 3 - KEEP_BY_USER 

JSON files store flags assigned to the dataset samples, namely whether it is part of the evaluation dataset.

## Annotation Tool

We are releasing an annotation tool, which can be use to edit the annotations in the RAW dataset.
After installing dependencies from `environment.yml` and `requirements.txt` the tool can be run
as follows:

`python3 -m sdt.annotate --dataset ROSBAG_DIR --annotations ROSBAG_ANNOTATAION_DIR --flag FLAG`

where:
- ROSBAG_DIR is a subdirectory of dataset directory (read only)
- ROSBAG_ANNOTATAION_DIR is a subdirectory of the annotations directory (modified in-place)
- `--flag` is optional, if provided, only samples flagged with `FLAG` will be loaded, by pasing "eval" you can load only the images which were selected for evaluation in our paper

The annotation tool provides two views, 3D point cloud on the left and on the right its projection 
to the left camera RGB image. The tool operates in two modes: ROTATE - mouse is to be used to rotate
and zoom the 3D point cloud, SELECT - mouse is used to select points in the 3D cloud. Depending on
the operation, the points are either KEPT or REMOVED.

Controls:
- R - switches modes ROTATE and SELECT
- D - switches operation KEEP and REMOVE
- left arrow - next dataset sample
- right arrow - previous dataset sample
- M - select or deselect the sample for evaluation 
- S - saves annotations and flags

### Point Cloud Filter

In the next step, we filter out occlusions adopting the filter from:

[bartn8/vppdc: Revisiting Depth Completion from a Stereo Matching Perspective for Cross-domain Generalization (3DV 2024)](https://github.com/bartn8/vppdc/blob/main/filter.py)

You will need to copy https://github.com/bartn8/vppdc/blob/main/filter.py to `sdt/occlusion_filter/filter.py`.

The script can be run as follows:

`python3 -m sdt.occlusion_filter --dataset DATASET_DIR --annotations ANNOTATION_DIR --output FILTERED_ANNOTATIONS_DIR --nx 10 --ny 50 --th 0.5 --flag eval`

where:
- DATASET_DIR - the RAW dataset directory containing all ROS bags
- ANNOTATION_DIR - containins annotations fo all ROS bags
- FILTERED_ANNOTATIONS_DIR - is the destination where the filtered annotations will be saved
- `--nx`, `--ny`, `--th` are parameters of the filter
- `--flag` will process only samples flagged by the given flag

### Export Evaluation Dataset

Creates the evaluation dataset in the format provided above for download:

`python3 -m sdt.export --dataset DATASET_PATH --annotations ANNOTATIONS_PATH --output EXPORTED_DATASET_PATH`

Only samples flagged with "eval" are included in the exported dataset. The exported dataset follows the
file structure of the RAW dataset, while merging the files in the dataset and annotation directories.
The resulting H5 files contain the following data:

- rgb-left
- rgb-right
- stereo-disparity
- stereo-confidence
- velodyne
- velodyne-annotations

# Citation

```bibtex
@misc{shotcretedepth,
      title={ShotcreteDepth: A Bi-modal Dataset for Robust Robotic Depth Perception in Shotcrete Construction Environments}, 
      author={Jakub Gregorek and Lars Arnold Dethlefsen and Patrick Schmidt and Mads Essenbæk and Jonas Flink Bentzen and Lazaros Nalpantidis},
      year={2026},
      eprint={2606.23152},
      archivePrefix={arXiv},
      primaryClass={cs.RO},
      url={https://arxiv.org/abs/2606.23152}, 
}
```

# Licensing

The source code in this repository is licensed under [General Public License Version 2](LICENSE.txt).

# Acknowledgments

This work was funded by the EU Horizon Europe project “RoBétArmé” (Grant Agreement 101058731).