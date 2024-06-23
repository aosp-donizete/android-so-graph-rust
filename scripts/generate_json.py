#!/usr/bin/python

import subprocess
import json

from typing import Callable, Tuple

def adb_shell(cmd: str) -> list[str]:
    process = subprocess.run(
        f"adb shell {cmd}",
        capture_output=True,
        shell=True
    )
    output = process.stdout.decode().split('\n')
    output.pop()
    return output

def cut_name_after_ls(name: str) -> str:
    return name.split(" ").pop()

def is_file_after_ls(name: str) -> bool:
    return name[0] == "-"

def is_folder_after_ls(name: str) -> bool:
    return name[0] == "d"

def is_link_after_ls(name: str) -> bool:
    return name[0] == "l"

def is_library_after_ls(name: str) -> bool:
    return is_file_after_ls(name) and name.split(".").pop() == "so"

def adb_shell_linker_list(file: str, arch: str) -> list[str]:
    def extract_full_lib_name(line: str) -> str:
        splits = line.split(" ")
        return splits[len(splits) - 2]

    dependencies = adb_shell(f"linker{arch} --list {file}")
    dependencies = map(extract_full_lib_name, dependencies)
    return list(dependencies)

library_index = list[str]()
library_dependency = dict[int, list[str]]()
library_link_to = dict[str, str]()

def global_library_get_index(library: str) -> int:
    if library not in library_index:
        library_index.append(library)
    return library_index.index(library)

def global_library_dependency_append(library: str, dependency: str):
    library_index = global_library_get_index(library)
    dependency_index = global_library_get_index(dependency)

    if library_index not in library_dependency:
        library_dependency[library_index] = list()

    library_dependency[library_index].append(dependency_index)

def handle_ls_result_for_libraries(folder: str, arch: str, ls_result: list[str]):
    libraries = map(lambda library : library.split(" ").pop(), ls_result)
    libraries = map(lambda library : f"{folder}/{library}", libraries)
    libraries = list(libraries)

    for library in libraries:
        dependencies = adb_shell_linker_list(library, arch)
        for dependency in dependencies:
            global_library_dependency_append(library, dependency)

def handle_ls_result_for_links(folder: str, arch: str, ls_result: list[str]):
    for line in ls_result:
        splits = line.split(" ")
        splits = filter(lambda split : split.split(".").pop() == "so", splits)
        splits = list(splits)
        link = f"{folder}/{splits[0]}"
        links_to = splits[1]
        if links_to[0] != "/": #relative link
            links_to = f"{folder}/{links_to}"
        library_link_to[link] = links_to

def handle_ls_result_for_folders(folder: str, arch: str, ls_result: list[str]):
    subfolders = map(lambda subfolder : subfolder.split(" ").pop(), ls_result)
    subfolders = map(lambda subfolder : f"{folder}/{subfolder}", subfolders)
    subfolders = list(subfolders)

    for subfolder in subfolders:
        trigger_ls_functions_for_folder_arch(subfolder, arch)

functions = list[Tuple[Callable[[str, str, list[str]], None], Callable[[str], bool]]](
    [
        (handle_ls_result_for_folders, is_folder_after_ls),
        (handle_ls_result_for_libraries, is_library_after_ls),
        (handle_ls_result_for_links, is_link_after_ls)
    ]
)

def trigger_ls_functions_for_folder_arch(folder: str, arch: str):
    ls_result = adb_shell(f"ls -l {folder}")
    for function, predicate in functions:
        function(folder, arch, list(filter(predicate, ls_result)))

partitions = [
    "/system",
    "/system_ext",
    "/vendor",
    "/product"
]

archs = [
    "",
    "64"
]

for partition in partitions:
    for arch in archs:
        trigger_ls_functions_for_folder_arch(f"{partition}/lib{arch}", arch)

subapexes = adb_shell(f"ls -l /apex")
subapexes = filter(is_folder_after_ls, subapexes)
subapexes = map(lambda line : line.split(" ").pop(), subapexes)
for subapex in subapexes:
    for arch in archs:
        trigger_ls_functions_for_folder_arch(f"/apex/{subapex}/lib{arch}", arch)

for library in library_index:
    if library in library_link_to:
        link_to = library_link_to[library]
        print(link_to)

json_object = {
    "libraries": library_index,
    "relations": library_dependency,
    "links": library_link_to
}

with open("sample/generated.json", "w") as fp:
    json.dump(json_object, fp)