import argparse
import numpy
from os import makedirs
from os.path import join
from copy import deepcopy
from tqdm import tqdm
from sdt.constants import (
    VELODYNE, 
    VELODYNE_ANNOTATIONS, 
    REMOVE_BY_USER, 
    REMOVE_BY_ALGORITHM
)
from sdt.utils import write_h5, write_json
from sdt.data.dataset import Dataset
from sdt.annotate.manager import contains_flag
from sdt.annotate.utils import default_annotation
from sdt.occlusion_filter.filter import filter_heuristic_depth


def occlusion_filter(velodyne: numpy.ndarray, annotations: numpy.ndarray, ny: int, nx: int, th: float):
    removed_before = numpy.logical_or(annotations == REMOVE_BY_USER, annotations == REMOVE_BY_ALGORITHM)
    
    modified_velodyne = deepcopy(velodyne)
    modified_velodyne[modified_velodyne < 0] = 0
    modified_velodyne_valid  = modified_velodyne[modified_velodyne > 0]
    modified_velodyne_valid[removed_before] = 0
    modified_velodyne[modified_velodyne > 0] = modified_velodyne_valid

    filtered_velodyne, _ = filter_heuristic_depth(modified_velodyne, ny=ny, nx=nx, th=th)

    removed_after = numpy.not_equal(velodyne[velodyne > 0], filtered_velodyne[velodyne > 0])
    removed_by_conti = numpy.logical_and(removed_after, numpy.logical_not(removed_before))

    updated_annotations = deepcopy(annotations)
    updated_annotations[removed_by_conti] = REMOVE_BY_ALGORITHM

    return updated_annotations


parser = argparse.ArgumentParser(description="Filter LiDAR point clouds.")
parser.add_argument("-d", "--dataset", type=str, required=True, help="Dataset directory.")
parser.add_argument("-a", "--annotations", type=str, required=True, help="Annotations directory.")
parser.add_argument("-o", "--output", type=str, required=True, help="Path to save filtered annotations.")
parser.add_argument("--nx", type=int, required=True)
parser.add_argument("--ny", type=int, required=True)
parser.add_argument("--th", type=float, required=True)
parser.add_argument("-f", "--flag", type=str, required=False, default=None,
                    help="only samples flagged with the specified flag will be filtered")
args = parser.parse_args()

dataset = Dataset(args.dataset, args.annotations)

for rosbag_name, rosbag in tqdm(dataset, desc="filtering rosbags"):
    result_dir = join(args.output, rosbag_name)
    makedirs(result_dir, exist_ok=True)

    for sample_idx in range(len(rosbag)):
        sample_metadata = rosbag.load_metadata(sample_idx)
        if args.flag is not None:
            if not contains_flag(sample_metadata, args.flag):
                continue

        sample_name = rosbag.sample_names[sample_idx]
        sample = rosbag.load_sample(sample_idx)
        
        velodyne = sample[VELODYNE]
        annotations = rosbag.load_annotations(sample_idx)

        if annotations is None:
            annotations = default_annotation(numpy.count_nonzero(velodyne > 0))
        else:
            annotations = annotations[VELODYNE_ANNOTATIONS]

        filtered_annotations = { VELODYNE_ANNOTATIONS: occlusion_filter(velodyne, annotations, args.ny, args.nx, args.th) }
        write_h5(filtered_annotations, join(result_dir, f"{sample_name}.h5"))
        write_json(sample_metadata, join(result_dir, f"{sample_name}.json"))
