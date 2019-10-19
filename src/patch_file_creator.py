import argparse
import os
import json
import shutil
import time


supported_tools = ["diff", "bsdiff", "xdelta", "rsync"]


def create_patch_directory_structure():
    pass


def delete_empty_subirectories():
    pass


def move_files_into_patch_directory():
    #TODO: Move all added files into their corresponding patch-directory location
    #TODO: Move all patch files into their corresponding patch-directory location
    pass


def is_path_valid(path_to_check):
    if os.path.exists(path_to_check):
        print("Path: {} exists".format(path_to_check))
        return True
    else:
        print("The path {} does not exist! Processing stops!".format(path_to_check))
        return False


def create_diff_files(source_list, destination_list):
    new_file = []
    modified_file = []
    deleted_files = []

    source_files = [ file_and_path[0] for file_and_path in source_list]
    destination_files = [file_and_path[0] for file_and_path in destination_list]

    for dest_file in destination_files:
        if dest_file not in source_files:
            new_file.append(dest_file)
        else:
            modified_file.append(dest_file)
    
    for source_file in source_files:
        if source_file not in destination_files:
            deleted_files.append(source_file)

    #TODO: For each modified file, a diff file needs to be created
    #TODO: Each new file can directly be moved to the patch-directory location
    #TODO: All deleted files can be ignored
    #TODO: After creating all diff-files and moving them to their corresponding location, all empty directories can be deleted!


def iterate_through_directory(directory_path):
    file_list = []
    for root, dirs, files in os.walk(directory_path):
        for file in files:
            file_path = root + "/" + file
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
    if not is_path_valid(args.patch_file_path):
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
    source_path, destination_path, patch_file_path, chosen_tool = check_arguments()


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
    create_patch_directory_structure()

    # Step 4: Go through destination list and create a patch file for each file in this list
    #         which was modified
    #         Note: This time it is necessary to measure the time which is needed 
    #               to create the diff for all files
    start_time = time.time()
    create_diff_files(source_list=source_file_list, destination_list=destination_file_list)
    end_time = time.time()

    needed_time = end_time - start_time

    # Step 5.1: Move all patch files and newly added files into their corresponding 
    #         location within the patch-directory
    move_files_into_patch_directory()

    # Step 5.2: Check if any of the subdirectories of the patch-directory is empty.
    #           If a directory is empty --> delete it
    delete_empty_subirectories()

    # Step 6: Create JSON file and save all measurable stats within it
    stats = {
        "time_needed_to_create_patch_file": needed_time,
        "time_needed_to_apply_patch_file": "",
        "size_of_the_source": "",
        "size_of_the_destination": "",
        "original_size_vs_patch_file_size": ""
    }
    #TODO: Save created JSON-file
