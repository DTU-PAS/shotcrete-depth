from os.path import join, exists
from glob import glob
from typing import Dict, Optional
from sdt.constants import CALIBRATION_FILE
from sdt.utils import (
    load_calibration, 
    load_h5, 
    write_h5
)
from sdt.annotate.utils import (
    sample_id_from_path, 
    load_metadata, 
    write_metadata
)


class RosBag:
    def __init__(self, rosbag_path: Optional[str] = None, annotations_dir: Optional[str] = None):
        if rosbag_path is None:
            self.sample_paths = []
            self.sample_names = []
            self.annotation_paths = []
            self.metadata_paths = []
            self.calibration_path = ""
        else: 
            self.sample_paths = sorted(glob(join(rosbag_path, "*.h5")))
            self.sample_names = [sample_id_from_path(p) for p in self.sample_paths]
            self.annotation_paths = [join(annotations_dir, f"{sample_name}.h5") for sample_name in self.sample_names]
            self.metadata_paths = [join(annotations_dir, f"{sample_name}.json") for sample_name in self.sample_names ]
            self.calibration_path = join(rosbag_path, CALIBRATION_FILE)       


    def __len__(self):
        return len(self.sample_names)


    def load_calibration(self) -> Optional[Dict]:
        if exists(self.calibration_path):
            return load_calibration(self.calibration_path)
        
        return None


    def load_sample(self, idx: int) -> Dict:
        return load_h5(self.sample_paths[idx])


    def save_sample(self, sample: Dict, idx: int) -> None:
        write_h5(sample, self.sample_paths[idx])


    def load_annotations(self, idx: int) -> Optional[Dict]:
        annotation_path = self.annotation_paths[idx]
        if exists(annotation_path):
            return load_h5(annotation_path)

        return None


    def save_annotations(self, annotations: Dict, idx: int) -> None:
        write_h5(annotations, self.annotation_paths[idx])


    def load_metadata(self, idx: int) -> Dict:
        flag_path = self.metadata_paths[idx]

        if exists(flag_path):
            return load_metadata(self.metadata_paths[idx])

        return {}


    def write_metadata(self, flags: Dict, idx: int):
        write_metadata(flags, self.metadata_paths[idx])
