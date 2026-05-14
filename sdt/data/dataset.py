from os import listdir
from os.path import isdir, join
from sdt.data.bag import RosBag


class Dataset:
    def __init__(self, dataset_dir: str, annotations_dir: str):
        self._rosbags = []
        self._names = []
        
        for rosbag_name in listdir(dataset_dir):
            rosbag_path = join(dataset_dir, rosbag_name)
            annotations_path = join(annotations_dir, rosbag_name)
            
            if isdir(rosbag_path):
                self._names.append(rosbag_name)
                self._rosbags.append(RosBag(rosbag_path, annotations_path))


    def __getitem__(self, i) -> RosBag:
        return self._rosbags[i]


    def __len__(self):
        return len(self._rosbags)


    def __iter__(self):
        return iter(zip(self._names, self._rosbags))


    def rosbag_name(self, i):
        return self._names[i]
