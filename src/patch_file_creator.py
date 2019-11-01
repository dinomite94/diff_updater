import argparse
import json
import os
import re
import shutil
import subprocess
import time
import zipfile


supported_tools = ["diff", "bsdiff", "xdelta", "rsync"]


def save_new_modified_and_deleted_file_lists(new_files, modified_files, deleted_files, patch_path):
    new_files_path = patch_path + "/" + "new_files.txt"
    modified_files_path = patch_path + "/" + "modified_files.txt"
    deleted_files_path = patch_path + "/" + "deleted_files.txt"
    with open(new_files_path, "w") as file_handler:
        for file in new_files:
            row = file[0] + " | " + file[1] + "\n"
            file_handler.write(row)

    with open(modified_files_path, "w") as file_handler:
        for file in modified_files:
            row = file[0] + " | " + file[1] + "\n"
            file_handler.write(row)

    with open(deleted_files_path, "w") as file_handler:
        for file in deleted_files:
            row = file[0] + " | " + file[1] + "\n"
            file_handler.write(row)


def calculate_directory_size(dir_path):
    size = 0
    for root, dir, files in os.walk(dir_path):
        for file in files:
            size += os.path.getsize(root + "/" + file)

    return size


def retrieve_needed_information(original_version_path, modified_version_path, patch_path):
    original_version_size = 0
    modified_version_size = 0
    patch_version_size = 0
    compressed_version_size = 0
    
    # Step 1: Get original_version_size
    original_version_size = calculate_directory_size(original_version_path)

    # Step 2: Get modified_version_size
    modified_version_size = calculate_directory_size(modified_version_path)

    # Step 3: Get patch_version_size
    patch_version_size = calculate_directory_size(patch_path)

    # Step 4: Compare modified version size with patch version size
    modified_version_vs_patch_version = "{} / {} = {}".format(modified_version_size, patch_version_size, (modified_version_size/patch_version_size))

    return original_version_size, modified_version_size, patch_version_size, compressed_version_size, modified_version_vs_patch_version


def create_patch_directory_structure(modified_directory, patch_directory):
    for root, dirs, _ in os.walk(modified_directory):
        root = root.replace(modified_directory, "")
        if not os.path.exists(patch_directory + "/" + root):
            path = patch_directory + "/" + root + "/"
            print("New directory created: {}".format(path))
            os.makedirs(path)


def copy_new_files_into_patch_directory(from_path, to_path, file_list):
    for file in file_list:
        source_path = from_path + "/" + file[1] + "/" + file[0]
        destination_path = to_path + "/" + file[1] + "/" + file[0]
        shutil.copy(src=source_path, dst=destination_path)


def create_diff_files(file_list, original_version_path, modified_version_path, patch_path, diff_tool):
    files_with_failed_patches = []

    for file in file_list:
        print("Creating diff for {}".format(file[0]))
        original_version_file = original_version_path + "/" + file[1] + "/" + file[0]
        modified_version_file = modified_version_path + "/" + file[1] + "/" + file[0]
        patch_file = patch_path + "/" + file[1] + "/" + file[0]

        if diff_tool == "bsdiff":
            result = subprocess.call(["bsdiff", original_version_file, modified_version_file, patch_file])
            if result > 0:
                print("Patch for {} failed. Adding this file to the list!".format(file[0]))
                files_with_failed_patches.append(file)
        elif diff_tool == "xdelta":
            pass
        elif diff_tool == "diff":
            pass
        elif diff_tool == "rsync":
            pass
        else:
            pass

    return files_with_failed_patches


def is_path_valid(path_to_check):
    if os.path.exists(path_to_check):
        print("Path: {} exists".format(path_to_check))
        return True
    else:
        print("The path {} does not exist! Processing stops!".format(path_to_check))
        return False


def detect_all_new_modified_and_deleted_files(original_version_file_list, modified_version_file_list):
    new_files = []
    modified_files = []
    deleted_files = []

    for modified_file in modified_version_file_list:
        modified_file_name = modified_file[0]
        modified_file_path = modified_file[1]

        found_equal_file = False

        for original_file in original_version_file_list:
            original_file_name = original_file[0]
            original_file_path = original_file[1]

            if original_file_name == modified_file_name:
                if original_file_path == modified_file_path:
                    modified_files.append(modified_file)
                    found_equal_file = True
                    break

        if not found_equal_file:
            new_files.append(modified_file)

    for original_file in original_version_file_list:
        original_file_name = original_file[0]
        original_file_path = original_file[1]

        found = False

        for modified_file in modified_version_file_list:
            modified_file_name = modified_file[0]
            modified_file_path = modified_file[1]

            if modified_file_name == original_file_name:
                if modified_file_path == original_file_path:
                    found = True
                    break
        if not found:
            deleted_files.append(original_file)

    return modified_files, new_files, deleted_files


def iterate_through_directory(directory_path):
    file_list = []
    for root, dirs, files in os.walk(directory_path):
        # Strip away the directory_path which is not needed for reconstructing the directory structure
        root = root.replace(directory_path, "")
        for file in files:
            file_path = root + "/"
            file_list.append((file, file_path))
    return file_list


def create_single_patch_file(original_version_path, modified_version_path, patch_path, tool):
    #TODO: Implement patch file creation for all other tools too
    subprocess.call(["bsdiff", original_version_path, modified_version_path, patch_path])


def check_arguments():
    parser = argparse.ArgumentParser()

    # Required Arguments
    parser.add_argument("-o", "--original_version_path", required=True, 
                        help="This path contains the original version of the directory/file/archive")
    parser.add_argument("-m", "--modified_version_path", required=True, 
                        help="This path contains the modified version of the directory/file/archive")
    parser.add_argument("-p", "--patch_path", required=True, 
                        help="The created diff file/directory/archive will be saved within this path")

    # Optional Arguments
    parser.add_argument("-t", "--tool", 
                        help="Choose one of the supported differential update tools listed below",
                        default="bsdiff")
    parser.add_argument("-j", "--json_path",
                        help="Choose path where the JSON-file will be saved. Default location will be the desktop",
                        default=os.environ["HOME"] + "/Desktop/stats.json")
    parser.add_argument("-f", "--file",
                        help="Set this flag if a patch file shall be created for a single file",
                        action='store_true',
                        default=False)
    parser.add_argument("-c", "--compress",
                        help="Set this flag if the created patch file/directory shall be compressed",
                        action='store_true',
                        default=False)

    args = parser.parse_args()

    if args.file:
        print("Flag for single file patching was set!")
        if os.path.isfile(args.original_version_path):
            print("Given path for original version leads to a file and it exists! Processing continues!")
            if os.path.isfile(args.modified_version_path):
                print("Given path for modified version leads to a file and it exists! Processing continues!")
            else:
                print("A problem occurred while checking the paths of the files!")
                print("Either the given path does not lead to a file, the file does not exist or the filename is mispelled!")
                print("Problem occurred while checking the following path: {}".format(args.modified_version_path))
                exit(1)
        else:
            print("A problem occurred while checking the paths of the files!")
            print("Either the given path does not lead to a file, the file does not exist or the filename is mispelled!")
            print("Problem occurred while checking the following path: {}".format(args.original_version_path))
            exit(1)
    else:
        print("Flag for single file patching was NOT set. Therefore a whole directory is patched!")
        # If this case is executed, it is not requested to update a single file!
        if not is_path_valid(args.original_version_path):
            exit(1)
        if not is_path_valid(args.modified_version_path):
            exit(1)

    if args.compress:
        print("Flag for compressing was set! Created patch file/directory will be compressed!")
    else:
        print("Flag for compressing was NOT set! Created patch file/directory won't be compressed!")

    if args.tool not in supported_tools:
        print("Chosen tool is not supported by this program! Processing stops!")
        exit(2)
    else:
        print("{} was chosen as the differential update tool for processing!".format(args.tool))

    return args


if __name__ == "__main__":
    # Step 1: Check if all paths and arguments are valid
    print("Checking which parameters were set for this script!")
    args = check_arguments()
    print("Checking of all parameters finished successfully! Processing continues")

    original_version_path = args.original_version_path
    modified_version_path = args.modified_version_path
    patch_path = args.patch_path
    diff_tool = args.tool
    json_path = args.json_path
    single_file_patching = args.file
    compression = args.compress


    original_version_size = 0
    modified_version_size = 0
    patch_version_size = 0 
    modified_vs_patch_size = 0
    needed_time = 0

    if single_file_patching:
        print("Single patch file creation starts!")
        start_time = time.time()
        create_single_patch_file(original_version_path=original_version_path,
                                 modified_version_path=modified_version_path,
                                 patch_path=patch_path,
                                 tool=diff_tool)
        end_time = time.time()
        needed_time = end_time - start_time
        print("Finished single patch file creation")

        print("Retrieving all relevant information of the selected files!")
        original_version_size = os.path.getsize(original_version_path)
        modified_version_size = os.path.getsize(modified_version_path)
        modified_vs_patch_size = "{} / {} = {}".format(modified_version_size, patch_version_size, modified_version_size / patch_version_size)
        patch_version_size = os.path.getsize(patch_path)
        print("Successfully gathered all needed information.")
    else:
        # Step 2: Iterate through the original and modified directories and search for all differences
        #         Note: Files with their corresponding paths will be saved
        print("Starting to iterate through the original version!")
        original_version_file_list = iterate_through_directory(directory_path=original_version_path)
        print("Number of files within the original version: {}".format(len(original_version_file_list)))
        print("=======================================================================")

        print("Starting to iterate through the modified version!")
        modified_version_file_list = iterate_through_directory(directory_path=modified_version_path)
        print("Number of files within the modified version: {}".format(len(modified_version_file_list)))
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
        modified_files, new_files, deleted_files = detect_all_new_modified_and_deleted_files(original_version_file_list=original_version_file_list,
                                                                                            modified_version_file_list=modified_version_file_list)

        print("Number of files which were added within the modified version: {}".format(len(new_files)))
        print("Number of files which were modified within the modified version: {}".format(len(modified_files)))
        print("Number of files which were deleted within the modified version: {}".format(len(deleted_files)))

        print("Creating diff-files for all modified files!")
        start_time = time.time()
        files_with_failed_patches = create_diff_files(file_list=modified_files, 
                                                    original_version_path=original_version_path,
                                                    modified_version_path=modified_version_path,
                                                    patch_path=patch_path,
                                                    diff_tool=diff_tool)
        end_time = time.time()
        print("All diff-files were created and stored within the patch directory!")
        # Calculates time which was needed to create all diff-files
        needed_time = end_time - start_time
        print("Time needed to create all diff-files: {}".format(needed_time))

        print("Number of files where the patching process failed: {}".format(len(files_with_failed_patches)))
        print("Files with a failed patching process need to be copied completely into the patch directory!")
        for file in files_with_failed_patches:
            new_files.append(file)
            if file in modified_files:
                print("Removing {} out of the modified_files list!".format(file))
                modified_files.remove(file)

        # Step 5: Move all new files into their corresponding
        #           location within the patch-directory
        print("Copying all new files from the modified version into the patch directory!")
        copy_new_files_into_patch_directory(from_path=modified_version_path,
                                            to_path=patch_path,
                                            file_list=new_files)
        print("Finished copying process!")

        # Step 6: Retrieve the following details which are necessary for the JSON-file:
        #           - Size of the original version
        #           - Size of the modified version
        #           - Size of the patch version
        #           - Size of the compressed version
        #           - Modified version size vs. patch size

        original_version_size, modified_version_size, \
        patch_version_size, compressed_version_size, \
        modified_vs_patch_size = retrieve_needed_information(original_version_path=original_version_path, 
                                                            modified_version_path=modified_version_path,
                                                            patch_path=patch_path)

        # Step 7: Create files which list all modified, new and deleted files
        print("Creating files which contain information about all new files, all modified files and all deleted files")
        save_new_modified_and_deleted_file_lists(new_files=new_files, 
                                                modified_files=modified_files,
                                                deleted_files=deleted_files,
                                                patch_path=patch_path)
        print("Successfully created all file lists!")

    compressed_version_size = 0
    if compression:
        zip_file = zipfile.ZipFile("/home/dino/Desktop/patch_result.zip", "w", zipfile.ZIP_DEFLATED)

        for root, dirs, files in os.walk(patch_path):
            for file in files:
                zip_file.write(os.path.join(root, file))

        compressed_version_size = os.path.getsize("/home/dino/Desktop/patch_result.zip")

    # Create JSON file and save all measurable stats within it
    print("Saving JSON-file with all relevant information as: stats.json")
    stats = {
        "time_needed_to_create_patch_file": "{} seconds".format(int(needed_time)),
        "time_needed_to_apply_patch_file": "",
        "size_of_the_original_version": "{} bytes".format(original_version_size),
        "size_of_the_modified_version": "{} bytes".format(modified_version_size),
        "size_of_the_patch_version": "{} bytes".format(patch_version_size),
        "size_of_the_compressed_version": "{} bytes".format(compressed_version_size),
        "modified_size_vs_patch_size": "{}".format(modified_vs_patch_size)
    }

    with open(json_path, "w") as file_handler:
        json.dump(stats, file_handler, indent=4, sort_keys=True, ensure_ascii=True)
    print("JSON-file successfully saved!")


    print("Finished processing!")