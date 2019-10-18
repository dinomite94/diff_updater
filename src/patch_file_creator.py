import argparse
import os
import json
import shutil
import time


supported_tools = ["diff", "bsdiff", "bspatch", "xdelta", "rsync"]


def is_path_valid(path_to_check):
    if os.path.exists(path_to_check):
        print("Path: {} exists".format(path_to_check))
        return True
    else:
        print("The path {} does not exist! Processing stops!".format(path_to_check))
        return False


def create_diff_files():
    pass


def iterate_through_directory(directory_path):
    '''
    for root, dirs, files in os.walk(root_dir):
        print(root)
    '''
    time.sleep(5)
    return "do some magic"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--source_path", 
                        help="This path contains the original version of the directory/file/archive")
    parser.add_argument("-d", "--destination_path", 
                        help="This path contains the modified version of the directory/file/archive")
    parser.add_argument("-p", "--patch_file_path", 
                        help="The created diff file will be saved within this path")
    parser.add_argument("-t", "--tool", 
                        help="Choose one of the supported differential update tools listed below")
    parser.add_argument("-v", "--verbose", 
                        help="More details are printed on the console", action="store_true")
    parser.add_argument("-r", "--recursive", 
                        help="Recursively iterates through the given path", default=True)
    args = parser.parse_args()

    start_time = time.time()
    # Step 1: Check if all paths and arguments 
    if not is_path_valid(args.source_path):
        exit(1)
    if not is_path_valid(args.destination_path):
        exit(1)
    if not is_path_valid(args.patch_file_path):
        exit(1)
    if args.tool not in supported_tools:
        print("Chosen tool is not supported by this program! Processing stops!")
        exit(2)
    else:
        print("All needed paths exist. Processing continues!")
        print("{} was chosen as the differential update tool for processing!".format(args.tool))
    if args.recursive:
        print("Recursion is activated.")

    source_path = args.source_path
    destination_path = args.destination_path
    patch_file_path = args.patch_file_path
    chosen_tool = args.tool

    # Step 2: Iterate through source and destination directories and search for all files
    #         Important note: Files with their corresponding paths will be saved
    source_file_list = iterate_through_directory(directory_path=source_path)
    destination_file_list = iterate_through_directory(directory_path=destination_path)

    # Step 3: Go through source list and create a patch file for each file in this list
    #         Important note: This time it is necessary to measure the time which is needed 
    #                         to create the diff for all files
    create_diff_files()

    # Step 4: Create JSON file and save all measurable stats within it
    #TODO: Save created JSON-file
    end_time = time.time()

    needed_time = end_time - start_time
    stats = {
        "time_needed_to_create_patch_file": needed_time,
        "time_needed_to_apply_patch_file": "",
        "size_of_the_source": "",
        "size_of_the_destination": "",
        "original_size_vs_patch_file_size": ""
    }
    print("Needed time: {} seconds".format(needed_time))

    print("Current JSON-file setup:")
    print(stats)