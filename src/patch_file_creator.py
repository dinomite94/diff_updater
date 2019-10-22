import argparse
import os
import json
import shutil
import subprocess
import time
import re


supported_tools = ["diff", "bsdiff", "xdelta", "rsync"]


def create_patch_directory_structure(modified_directory, patch_directory):
    for root, dirs, _ in os.walk(modified_directory):
        root = root.replace(modified_directory, "")
        if not os.path.exists(patch_directory + "/" + root):
            path = patch_directory + "/" + root
            print("New directory created".format(path))
            os.makedirs(path)


def copy_new_files_into_patch_directory(from_path, to_path, file_list):
    for file in file_list:
        shutil.copy(from_path + file[1] + file[0], to_path + file[1] + file[0])


def create_diff_files(file_list, original_version_path, modified_version_path, patch_path):
    #TODO: Implement diff creation for all other differential update tools
    for file in file_list:
        print("Creating diff for {}".format(file[0]))
        original_version_file = original_version_path + "/" + file[1] + "/" + file[0]
        modified_version_file = modified_version_path + "/" + file[1] + "/" + file[0]
        patch_file = patch_path + "/" + file[1] + "/" + file[0]
        subprocess.call(["bsdiff", original_version_file, modified_version_file, patch_file])


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


def detect_all_new_and_modified_files(original_version_file_list, modified_version_file_list):
    new_files = []
    modified_files = []

    original_version_files = [ file_and_path[0] for file_and_path in original_version_file_list]
    modified_version_files = [file_and_path[0] for file_and_path in modified_version_file_list]

    for modified_version_file in modified_version_files:
        if modified_version_file not in original_version_files:
            new_files.append(modified_version_file)
        else:
            modified_files.append(modified_version_file)

    new_files_with_paths = fill_list_with_searched_values(file_list_without_paths=new_files,
                                                          file_list_with_paths=modified_version_file_list)

    modified_files_with_paths = fill_list_with_searched_values(file_list_without_paths=modified_files,
                                                               file_list_with_paths=modified_version_file_list)
    
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
    #TODO: Add -f flag for single file diffing. Currently, the program will only execute correctly for directories!
    #TODO: Make the program work for archives 
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--original_version_path", 
                        help="This path contains the original version of the directory/file/archive")
    parser.add_argument("-m", "--modified_version_path", 
                        help="This path contains the modified version of the directory/file/archive")
    parser.add_argument("-p", "--patch_path", 
                        help="The created diff file will be saved within this path")
    parser.add_argument("-t", "--tool", 
                        help="Choose one of the supported differential update tools listed below")
    args = parser.parse_args()

    if not is_path_valid(args.original_version_path):
        exit(1)
    if not is_path_valid(args.modified_version_path):
        exit(1)
    if args.tool not in supported_tools:
        print("Chosen tool is not supported by this program! Processing stops!")
        exit(2)
    else:
        print("{} was chosen as the differential update tool for processing!".format(args.tool))

    return args.original_version_path, args.modified_version_path, args.patch_path, args.tool


if __name__ == "__main__":
    # Step 1: Check if all paths and arguments are valid
    print("Checking if the paths of the original and modified versions are valid and exist!")
    original_version_path, modified_version_path, patch_path, chosen_tool = check_arguments()
    print("All needed paths are valid and exist. Processing continues")

    # Step 2: Iterate through the original and modified directories and search for all differences
    #         Note: Files with their corresponding paths will be saved
    print("Starting to iterate through the original version!")
    original_version_file_list = iterate_through_directory(directory_path=original_version_path)
    print("Result: ")
    print(original_version_file_list)
    print("=======================================================================")

    print("Starting to iterate through the modified version!")
    modified_version_file_list = iterate_through_directory(directory_path=modified_version_path)
    print("Result: ")
    print(modified_version_file_list)
    print("=======================================================================")

    # Step 3: Create structure of the patch-directory
    print("Starting to create patch directory structure!")
    create_patch_directory_structure(modified_directory=modified_version_path, patch_directory=patch_path)
    print("Finished creating patch directory structure!")

    # Step 4: Go through destination list and create a patch file for each file in this list
    #         which was modified
    #         Note: This time it is necessary to measure the time which is needed 
    #               to create the diff for all files
    print("Starting to detect all new and modified files!")
    modified_files, new_files = detect_all_new_and_modified_files(original_version_file_list=original_version_file_list, 
                                                                  modified_version_file_list=modified_version_file_list)
    print("List of all files which were added within the modified version: ")
    print(new_files)
    print("List of all files which were modified within the modified version: ")
    print(modified_files)

    print("Creating diff-files for all modified files!")
    start_time = time.time()
    create_diff_files(file_list=modified_files, original_version_path=original_version_path, 
                      modified_version_path=modified_version_path, patch_path=patch_path)
    end_time = time.time()
    print("All diff-files were created and stored within the patch directory!")
    # Calculates time which was needed to create all diff-files
    needed_time = end_time - start_time
    print("Time needed to create all diff-files: {}".format(needed_time))

    # Step 5: Move all new files into their corresponding 
    #           location within the patch-directory
    print("Copying all new files from the modified version into the patch directory!")
    copy_new_files_into_patch_directory(from_path=modified_version_path, to_path=patch_path, file_list=new_files)
    print("Finished copying process!")

    # Step 6: Create JSON file and save all measurable stats within it
    print("Saving JSON-file with all relevant information as: stats.json")
    stats = {
        "time_needed_to_create_patch_file": needed_time,
        "time_needed_to_apply_patch_file": "",
        "size_of_the_original_version": "",
        "size_of_the_modified_version": "",
        "original_size_vs_patch_size": ""
    }
    #TODO: Save created JSON-file
    print("JSON-file successfully saved!")
    print("Finished processing!")