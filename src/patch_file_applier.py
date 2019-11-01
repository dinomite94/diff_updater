import argparse
import json
import os
import re
import time
import shutil
import subprocess

supported_tools = ["bspatch", "diff", "xdelta", "rsync"]


def is_path_valid(path_to_check):
    if os.path.exists(path_to_check):
        print("Path: {} exists".format(path_to_check))
        return True
    else:
        print("The path {} does not exist! Processing stops!".format(path_to_check))
        return False


def check_arguments():
    parser = argparse.ArgumentParser()

    # Required Arguments
    parser.add_argument("-o", "--original_version_path", required=True, 
                        help="This path contains the original version of the directory/file/archive")
    parser.add_argument("-m", "--modified_version_path", required=True, 
                        help="This path contains the modified version of the directory/file/archive")
    parser.add_argument("-p", "--patch_path", required=True, 
                        help="The created diff file will be saved within this path")

    # Optional Arguments
    parser.add_argument("-t", "--tool", 
                        help="Choose one of the supported differential update tools listed below",
                        default="bspatch")

    # Currently not implemented Arguments
    #TODO: Implement behavior for single file patching
    #TODO: Implement behavior for compressing the created patch-file/patch-directory
    #TODO: Implement behavior for choosing a specific JSON-file-directory
    parser.add_argument("-f", "--file_path",
                        help="Filepath and filename in order to create the patch file for a specific file", 
                        default=None)
    parser.add_argument("-c", "--compress",
                        help="Compresses the created patch directory. Default compression is ZIP",
                        default="zip")
    parser.add_argument("-j", "--json_path", 
                        help="Chosen path where the JSON-file will be saved. Default location will be the desktop!",
                        default=os.environ["HOME"] + "/Desktop/stats.json")
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

    return args.original_version_path, args.modified_version_path, args.patch_path, args.tool, args.json_path


def update_original_directory(modified_files, original_version_path, patch_path, tool):
    failed_patches = []

    for file in modified_files:
        modified_file_path = original_version_path + "/" + file
        patch_file_path = patch_path + "/" + file

        return_value = subprocess.call(["bspatch", modified_file_path, modified_file_path, patch_file_path])
        if return_value > 0:
            print("Patch failed for the following file: {}".format(modified_file_path))
            failed_patches.append(modified_file_path)
        else:
            print("Patch applied for the following file: {}".format(modified_file_path))
    print("Number of files which were not patched successfully: {}".format(len(failed_patches)))


def compare_original_and_modified_directories(original_version_path, modified_version_path):
    print("Not implemented yet")
    return True


def read_file(file_path):
    return_list = []

    with open(file_path, "r") as file_handler:
        line = file_handler.readline()
        while line:
            name, path = re.split(r" \| ", line)
            path = path.replace("\n", "")

            return_list.append(path + "/" + name)
            line = file_handler.readline()

    return return_list


def create_all_file_lists(patch_path):
    deleted_file = read_file(patch_path + "/" + "deleted_files.txt")
    new_files = read_file(patch_path + "/" + "new_files.txt")
    modified_files = read_file(patch_path + "/" + "modified_files.txt")

    return new_files, modified_files, deleted_file


def delete_empty_directories_of_original_version(original_version_path):
    something_changed = True
    while something_changed:
        something_changed = False
        for root, dirs, files in os.walk(original_version_path):
            for dir in dirs:
                dir_path = root + "/" + dir
                if not os.listdir(dir_path):
                    print("The following directory was empty and therefore deleted: {}".format(dir_path))
                    something_changed = True
                    os.rmdir(dir_path)



def remove_files_from_original_version(deleted_files, original_version_path):
    for file in deleted_files:
        old_version_file = original_version_path + "/" + file
        os.remove(old_version_file)
        print("Deleted the following file from the original version: {}".format(old_version_file))


def move_files_to_original_version(new_files, original_version_path, patch_path):
    for file in new_files:
        file_path = re.split("/", file)
        file_path = file_path[:-1]

        path = ""
        for f in file_path:
            path += f + "/"

        new_file_from = patch_path + "/" + file
        new_file_to = original_version_path + "/" + file

        if os.path.exists(original_version_path + "/" + path):
            shutil.move(src=new_file_from, dst=new_file_to)
        else:
            os.makedirs(original_version_path + "/" + path)
            shutil.move(src=new_file_from, dst=new_file_to)
        print("Moved the following file from {} to {}".format(new_file_from, new_file_to))


if __name__ == "__main__":
    # Step 1: Check if all needed parameters were set and
    #         if all needed paths exist
    original_version_path, modified_version_path, patch_path, tool, json_path = check_arguments()

    # Step 2: Create list with all new, modified and deleted elements
    new_files, modified_files, deleted_files = create_all_file_lists(patch_path=patch_path)

    # Step 3: Remove all files within the original version which are within the deleted_file list
    remove_files_from_original_version(deleted_files=deleted_files, 
                                       original_version_path=original_version_path)

    # Step 4: Move all files from the new_files list into the original version
    move_files_to_original_version(new_files=new_files, 
                                   original_version_path=original_version_path,
                                   patch_path=patch_path)

    # Step 5: Update the old version of the directory with all files of the modified_files list
    #         Important note: Time needed will be measured!
    start_time = time.time()
    update_original_directory(modified_files=modified_files,
                              original_version_path=original_version_path,
                              patch_path=patch_path,
                              tool=tool)
    end_time = time.time()

    delete_empty_directories_of_original_version(original_version_path)

    needed_time = end_time - start_time
    print("Time needed for applying all patches: {} seconds".format(int(needed_time)))

    # Step 3: Check whether the size of the modified directory
    #         is equal to the old one after patching
    result = compare_original_and_modified_directories(original_version_path=original_version_path,
                                                       modified_version_path=modified_version_path)
    if result:
        print("Patching was successfull! Both directories are equal now!")
    else:
        print("Something went wrong while patching! Directories are not equal sized!")

    print("Starting to update previously saved JSON-file!")
    json_file = None

    with open(json_path, "r") as file_handler:
        json_file = json.load(file_handler)

    json_file["time_needed_to_apply_patch_file"] = "{} seconds".format(int(needed_time))

    with open(json_path, "w") as file_handler:
        json.dump(json_file, file_handler, indent=4, ensure_ascii=True, sort_keys=True)

    print("JSON-file successfully updated!")
