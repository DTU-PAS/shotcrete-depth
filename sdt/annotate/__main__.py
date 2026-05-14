import argparse
from sdt.annotate.session import Session

parser = argparse.ArgumentParser(description="Point cloud annotation tool.")
parser.add_argument("-d", "--dataset", type=str, required=True, 
                    help="ROS bag directory contianing H5 files.")
parser.add_argument("-a", "--annotations", type=str, required=True, 
                    help="directory contianing annotations for the ROS bag")
parser.add_argument("--simple", action="store_true", 
                    help="if specified, the tool visualizes only two colors, for kept and removed points")
parser.add_argument("-f", "--flag", type=str, required=False, default=None,
                    help="only samples flagged with the specified flag will be loaded")
args = parser.parse_args()

session = Session(args.dataset, args.annotations, args.simple, args.flag)
session.run()