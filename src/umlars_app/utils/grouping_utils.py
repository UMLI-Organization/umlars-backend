import dataclasses
import logging
import re
from collections import defaultdict
from typing import Dict, List, Deque, Set
from collections import deque

from django.core.files.uploadedfile import UploadedFile

from umlars_app.exceptions import UnsupportedFileError
from umlars_backend.settings import LOGGING
from umlars_app.utils.logging import get_new_sublogger


logger = get_new_sublogger(__name__)


@dataclasses.dataclass
class ModelFilesGroup:
    model_name: str | None = dataclasses.field(default=None)
    files: List[UploadedFile] = dataclasses.field(default_factory=list)



def create_filenames_to_extensions_mapping(files: List[UploadedFile]) -> Dict[str, Dict[str, List[UploadedFile]]]:
    """
    Create a mapping from filenames to extensions.

    Args:
        files (List[UploadedFile]): List of uploaded files.

    Returns:
        Dict[str, Dict[str, List[UploadedFile]]]: Mapping from filenames to extensions.
    """
    filenames_mapping = defaultdict(lambda: defaultdict(list))
    for file in files:
        base_name, extension = file.name.rsplit('.', 1)
        filenames_mapping[base_name][extension].append(file)

    return filenames_mapping


def group_files(
    files: List[UploadedFile], 
    extensions_groups: Deque[Set[str]], 
    regex_patterns: Deque[str]
) -> Deque[ModelFilesGroup]:
    """
    Group files based on the provided grouping rules.

    Args:
        files (List[UploadedFile]): List of uploaded files.
        extensions_groups (Deque[Set[str]]): Groups of extensions.
        regex_patterns (Deque[str]): List of regex patterns.

    Returns:
        Deque[ModelFilesGroup]: Grouped files.
    """
    grouped_files: Deque[ModelFilesGroup] = deque()

    if not extensions_groups and not regex_patterns:
        # If no grouping rules provided, treat each file as a separate group
        grouped_files = deque(map(lambda file: ModelFilesGroup(files=[file]), files))
        return grouped_files
    
    filenames_to_extensions_mapping = create_filenames_to_extensions_mapping(files)

    logger.debug(f"Files to extensions mapping: {filenames_to_extensions_mapping}")
    # Group by extension
    while extensions_groups:
        extensions_group = extensions_groups.popleft()
        for base_name, extensions_mapping_for_base_name in list(filenames_to_extensions_mapping.items()):
            group = ModelFilesGroup()
            for extension in extensions_group:
                files_for_extension = extensions_mapping_for_base_name.pop(extension, [])
                group.files.extend(files_for_extension)


            logger.debug(f"Grouped files for base name: {group.files}")
            if group.files:
                grouped_files.append(group)
                if not extensions_mapping_for_base_name:  # If no extensions left for this base name, remove the entry
                    del filenames_to_extensions_mapping[base_name]
    logger.debug(f"Grouped files after extension grouping: {grouped_files}")

    # Group by regex patterns
    while regex_patterns:
        pattern = regex_patterns.popleft()
        regex = re.compile(pattern)
        regex_groups = defaultdict(list)
        for base_name, extensions_mapping_for_base_name in filenames_to_extensions_mapping.items():
            for extension, files_for_extension in extensions_mapping_for_base_name.items():
                for file in files_for_extension:
                    match = regex.match(file.name)
                    if match:
                        regex_key = match.group(0)
                        regex_groups[regex_key].append(file)
                # Remove processed extensions
                del extensions_mapping_for_base_name[extension]
            if not extensions_mapping_for_base_name:  # If no extensions left for this base name, remove the entry
                del filenames_to_extensions_mapping[base_name]

        for regex_key, files_for_extension in regex_groups.items():
            grouped_files.append(ModelFilesGroup(model_name=regex_key, files=files_for_extension))

    logger.debug(f"Grouped files after regex grouping: {grouped_files}")

    logger.debug(f"Remaining files after grouping: {filenames_to_extensions_mapping}")
    # Any remaining files are treated as separate groups containing one file each
    for base_name, extensions_mapping_for_base_name in filenames_to_extensions_mapping.items():
        for extension, files_for_extension in extensions_mapping_for_base_name.items():
            for file in files_for_extension:
                grouped_files.append(ModelFilesGroup(model_name=determine_model_name_from_file(file), files=[file]))

    return grouped_files



def determine_model_name(group: ModelFilesGroup) -> str:
    """
    Determine the name for the UML model based on the grouped files.

    Args:
        group (ModelFilesGroup): Group of files.

    Returns:
        str: The determined model name.
    """
    return determine_model_name_from_file(group.files[0]) if group.model_name is None else group.model_name or "Unnamed Model"


def determine_model_name_from_file(file: UploadedFile) -> str:
    """
    Determine the name for the UML model based on the grouped files.

    Args:
        group (ModelFilesGroup): Group of files.

    Returns:
        str: The determined model name.
    """
    return file.name.rsplit('.', 1)[0] or "Unnamed Model"
