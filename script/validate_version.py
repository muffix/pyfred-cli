import argparse
import sys
from configparser import ConfigParser

arg_parser = argparse.ArgumentParser(
    prog="validate_version", description="Validate that the package version matches a value"
)
arg_parser.add_argument("-e", "--expected_version", type=str, required=True, help="The expected version")
args = arg_parser.parse_args()

parser = ConfigParser()
parser.read("setup.cfg")

committed_version = parser.get("metadata", "version")
expected_version = args.expected_version[1:] if args.expected_version.startswith("v") else args.expected_version


if committed_version != expected_version:
    print(f"Committed version: {committed_version}, but expected: {expected_version}", file=sys.stderr)
    exit(1)
