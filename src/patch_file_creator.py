import argparse
import os
import json
import shutil
import subprocess
import time
import re


supported_tools = ["diff", "bsdiff", "xdelta", "rsync"]


def create_patch_directory_structure(destination_directory, patch_directory):
    for root, dirs, _ in os.walk(destination_directory):
        root = root.replace(destination_directory, "")
        os.makedirs(patch_directory + "/" + root)


def move_new_files_into_patch_directory(source_path, destination_path, file_list):
    for file in file_list:
        shutil.copy(source_path + file[1] + file[0], destination_path + file[1] + file[0])


def create_diff_files(file_list, origin_path, modified_path, patch_path):
    for file in file_list:
        print("Creating diff for {}".format(file[0]))
        original_file = origin_path + "/" + file[1] + "/" + file[0]
        modified_file = modified_path + "/" + file[1] + "/" + file[0]
        patch_file = patch_path + "/" + file[1] + "/" + file[0]
        subprocess.call(["bsdiff", original_file, modified_file, patch_file])


def is_path_valid(path_to_check):
    if os.path.exists(path_to_check):
        print("Path: {} exists".format(path_to_check))
        return True
    else:
        print("The path {} does not exist! Processing stops!".format(path_to_check))
        return False


def fill_list_with_searched_values(file_list_without_paths, file_list_with_paths):
    result_list = []
    for file_wop in file_list_without_paths:
        for file_wp in file_list_with_paths:
            if file_wop == file_wp[0]:
                result_list.append((file_wop, file_wp[1]))
                break
    return result_list


def detect_all_new_and_modified_files(source_list, destination_list):
    new_files = []
    modified_files = []

    source_files = [ file_and_path[0] for file_and_path in source_list]
    destination_files = [file_and_path[0] for file_and_path in destination_list]

    for dest_file in destination_files:
        if dest_file not in source_files:
            new_files.append(dest_file)
        else:
            modified_files.append(dest_file)

    new_files_with_paths = fill_list_with_searched_values(file_list_without_paths=new_files,
                                                          file_list_with_paths=destination_list)

    modified_files_with_paths = fill_list_with_searched_values(file_list_without_paths=modified_files,
                                                               file_list_with_paths=destination_list)
    
    return modified_files_with_paths, new_files_with_paths


def iterate_through_directory(directory_path):
    file_list = []
    for root, dirs, files in os.walk(directory_path):
        # Strip away the directory_path which is not needed for reconstructing the directory structure
        root = root.replace(directory_path, "")
        for file in files:
            file_path = root + "/"
            file_list.append((file, file_path))
    return file_list


def check_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--source_path", 
                        help="This path contains the original version of the directory/file/archive")
    parser.add_argument("-d", "--destination_path", 
                        help="This path contains the modified version of the directory/file/archive")
    parser.add_argument("-p", "--patch_file_path", 
                        help="The created diff file will be saved within this path")
    parser.add_argument("-t", "--tool", 
                        help="Choose one of the supported differential update tools listed below")
    args = parser.parse_args()

    if not is_path_valid(args.source_path):
        exit(1)
    if not is_path_valid(args.destination_path):
        exit(1)
    if args.tool not in supported_tools:
        print("Chosen tool is not supported by this program! Processing stops!")
        exit(2)
    else:
        print("All needed paths exist. Processing continues!")
        print("{} was chosen as the differential update tool for processing!".format(args.tool))

    return args.source_path, args.destination_path, args.patch_file_path, args.tool


if __name__ == "__main__":
    # Step 1: Check if all paths and arguments are valid
    source_path, destination_path, patch_path, chosen_tool = check_arguments()

    # Step 2: Iterate through source and destination directories and search for all files
    #         Note: Files with their corresponding paths will be saved
    print("Starting to iterate through the source path!")
    source_file_list = iterate_through_directory(directory_path=source_path)
    print("Result: ")
    print(source_file_list)
    print("=======================================================================")

    print("Starting to iterate through the destination path!")
    destination_file_list = iterate_through_directory(directory_path=destination_path)
    print("Result: ")
    print(destination_file_list)
    print("=======================================================================")

    # Step 3: Create structure of the patch-directory
    create_patch_directory_structure(destination_directory=destination_path, patch_directory=patch_path)

    # Step 4: Go through destination list and create a patch file for each file in this list
    #         which was modified
    #         Note: This time it is necessary to measure the time which is needed 
    #               to create the diff for all files
    '''
    modified list contains of the following aspects: 
        1. location of the old version
        2. location of the new version
    '''
    modified_files, new_files = detect_all_new_and_modified_files(source_list=source_file_list, destination_list=destination_file_list)

    start_time = time.time()
    create_diff_files(file_list=modified_files, origin_path=source_path, modified_path=destination_path, patch_path=patch_path)
    end_time = time.time()
    # Calculates time which was needed to create all diff-files
    needed_time = end_time - start_time

    # Step 5: Move all new files into their corresponding 
    #           location within the patch-directory
    move_new_files_into_patch_directory(source_path=destination_path, destination_path=patch_path, file_list=new_files)

    # Step 6: Create JSON file and save all measurable stats within it
    stats = {
        "time_needed_to_create_patch_file": needed_time,
        "time_needed_to_apply_patch_file": "",
        "size_of_the_source": "",
        "size_of_the_destination": "",
        "original_size_vs_patch_file_size": ""
    }
    #TODO: Save created JSON-file
    #TODO: Rename source to origin 
    #TODO: Rename destination to modified
    #TODO: Consider renaming patch to destination

    print("Finished processing!")
    #shutil.rmtree(patch_path)