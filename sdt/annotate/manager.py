import numpy
from copy import deepcopy
from enum import Enum
from typing import Optional, Dict
from sdt.data.bag import RosBag
from sdt.annotate.utils import default_annotation
from sdt.utils import projection_to_point_cloud
from sdt.constants import (
    CALIB_CAMERA_LEFT_INTRINSIC,
    CALIB_VELODYNE_EXTRINSIC,
    VELODYNE,
    VELODYNE_ANNOTATIONS,
    KEEP_BY_USER, 
    REMOVE_BY_USER
)

from sdt.annotate.constants import (
    EVAL_FLAG, 
    FLAGS,
    FACE_FLAG
)

class Operation(str, Enum):
    KEEP = "keep"
    REMOVE = "remove"


class SessionManager:
    def __init__(self, rosbag_path: str, annotations_dir: str, flag: Optional[str] = None):
        self._rosbag = RosBag(rosbag_path, annotations_dir)
        if len(self._rosbag) == 0:
            raise Exception(f"provided ROS bag path {rosbag_path} is empty")

        if flag is not None:
            self._rosbag = filter_bag_by_flag(self._rosbag, flag)
            if len(self._rosbag) == 0:
                raise Exception(f"the ROS bag does not contain any samples with given flag: {flag}")

        self._selected_idx = 0

        self._calibration = {}
        self._sample = {}
        self._annotation_history = []
        self._flags = set()

        self.lidar_points = None

        self._load_calibration()
        self._load_sample()


    def __len__(self):
        return len(self._rosbag)
    

    def _load_calibration(self):
        self._calibration = self._rosbag.load_calibration()


    def _load_sample(self):
        self._sample = self._rosbag.load_sample(self._selected_idx)
        self.lidar_points = projection_to_point_cloud(self._sample[VELODYNE], self.intrinsics(), self.extrinsics())

        annotations = self._rosbag.load_annotations(self._selected_idx)
        if annotations is None:
            point_count = self.lidar_points.shape[0]
            annotations = default_annotation(point_count)
        else:
            annotations = annotations[VELODYNE_ANNOTATIONS]
        
        self._annotation_history = [annotations]
        
        metadata = self._rosbag.load_metadata(self._selected_idx)
        if FLAGS in metadata.keys():
            self._flags = set(metadata[FLAGS])
        else:
            self._flags = set()

    def sample_element(self, key: str) -> numpy.ndarray:
        return self._sample[key]


    def next_sample(self) -> bool:
        self._selected_idx += 1

        if self._selected_idx == len(self._rosbag):
            self._selected_idx -= 1
            return False
        
        self._load_sample()
        return True


    def previous_sample(self) -> bool:
        self._selected_idx -= 1

        if self._selected_idx < 0:
            self._selected_idx = 0
            return False
        
        self._load_sample()
        return True


    def sample_name(self) -> str:
        return self._rosbag.sample_names[self._selected_idx]


    def sample_index(self) -> str:
        return self._selected_idx


    def intrinsics(self) -> numpy.ndarray:
        return numpy.array(self._calibration[CALIB_CAMERA_LEFT_INTRINSIC])


    def extrinsics(self) -> str:
        return numpy.array(self._calibration[CALIB_VELODYNE_EXTRINSIC])


    def annotations(self) -> numpy.ndarray:
        return deepcopy(self._annotation_history[-1])


    def save(self):
        self._rosbag.save_annotations({VELODYNE_ANNOTATIONS: self._annotation_history[-1]}, self._selected_idx)
        self._rosbag.write_metadata({FLAGS: list(self._flags)}, self._selected_idx)
    

    def is_marked_for_evaluation(self):
        return EVAL_FLAG in self._flags
    
    def is_marked_as_contains_face(self):
        return FACE_FLAG in self._flags


    def toggle_evaluation_mark(self):
        if self.is_marked_for_evaluation():
            self._flags.remove(EVAL_FLAG)
        else:
            self._flags.add(EVAL_FLAG)
    
    def toggle_face_mark(self):
        if self.is_marked_as_contains_face():
            self._flags.remove(FACE_FLAG)
        else:
            self._flags.add(FACE_FLAG)


    def undo(self) -> bool:
        if len(self._annotation_history) == 1:
            return False
        
        self._annotation_history.pop()
        return True
    
    
    def apply_pick(self, idcs: numpy.ndarray, op: Operation):
        annotations = self.annotations()

        if op is Operation.KEEP:
            annotations[idcs] = KEEP_BY_USER

        if op is Operation.REMOVE:
            annotations[idcs] = REMOVE_BY_USER

        self._annotation_history.append(annotations)


def filter_bag_by_flag(bag: RosBag, flag: str):
    filtered_bag = RosBag()
    filtered_bag.calibration_path = bag.calibration_path

    for i in range(len(bag)):
        if contains_flag(bag.load_metadata(i), flag):
            filtered_bag.sample_paths.append(bag.sample_paths[i])
            filtered_bag.sample_names.append(bag.sample_names[i])
            filtered_bag.annotation_paths.append(bag.annotation_paths[i])
            filtered_bag.metadata_paths.append(bag.metadata_paths[i])

    return filtered_bag


def contains_flag(metadata: Dict, flag: str):
    if FLAGS not in metadata.keys():
         return False

    return flag in set(metadata[FLAGS])
