import argparse
import datetime
from os import makedirs, getlogin
from os.path import join
from tqdm import tqdm
from sdt.constants import CALIBRATION_FILE
from sdt.utils import (
    write_calibration, 
    write_h5, 
    write_json
)
from sdt.annotate.manager import (
    EVAL_FLAG, 
    FACE_FLAG, 
    contains_flag
)
from sdt.data.dataset import Dataset

def export_eval_dataset(dataset_path: str, annotations_path: str, output_path: str):
    dataset = Dataset(dataset_path, annotations_path)

    info = {
        "created": datetime.datetime.now().isoformat(),
        "user": getlogin()
    }
    makedirs(output_path, exist_ok=True)
    write_json(info, join(output_path, "metadata.json"))

    for bag_name, bag in tqdm(dataset):
        new_bag_path = join(output_path, bag_name)
        makedirs(new_bag_path, exist_ok=True)
        write_calibration(bag.load_calibration(), join(new_bag_path, CALIBRATION_FILE))

        for sample_id in range(len(bag)):
            sample_name = bag.sample_names[sample_id]
            metadata = bag.load_metadata(sample_id)
            
            if contains_flag(metadata, EVAL_FLAG) and not contains_flag(metadata, FACE_FLAG):
                new_sample_path = join(new_bag_path, f"{sample_name}.h5")
                sample_data = bag.load_sample(sample_id) | bag.load_annotations(sample_id)
                write_h5(sample_data, new_sample_path)


parser = argparse.ArgumentParser(description="Extract dataset for evaluation")
parser.add_argument("-d", "--dataset", type=str, required=True, 
                    help="dataset directory containing ROS bag directories")
parser.add_argument("-a", "--annotations", type=str, required=True, 
                    help="directory contianing all annotations for the given dataset (in subdirectories for each ROS bag)")
parser.add_argument("-o", "--output", type=str, required=True, 
                    help="Directory where the extracted data will be saved.")
args = parser.parse_args()


export_eval_dataset(args.dataset, args.annotations, args.output)