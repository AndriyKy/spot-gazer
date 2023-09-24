import glob
import json
from functools import lru_cache
from os.path import join as join_path
from typing import Any
from zipfile import ZipFile

import numpy as np

FILE_NAME = "parking_spaces_location.json"


class CoordinatesConverter:
    def __init__(self, directory: str = "COCO_archives") -> None:
        self.directory = directory

    def read_json(
        self, archive_name: str = "", file_in_archive: str = "result.json", converted_json_file: str = ""
    ) -> dict[str, Any]:
        """If the `converted_json_file` parameter is specified, a converter file will be read"""
        if converted_json_file:
            with open(join_path(self.directory, converted_json_file)) as file:
                return json.loads(file.read())
        else:
            with ZipFile(join_path(self.directory, archive_name)) as archive, archive.open(file_in_archive) as file:
                return json.loads(file.read())

    @staticmethod
    def convert(marking_results: dict[str, Any]) -> list[dict[str, Any]]:
        parking_space_list = []
        for image in marking_results["images"]:
            parking_space_info = dict()
            parking_space_info["file_name"] = image["file_name"].split("-")[1]
            parking_space_info["coordinates"] = []

            for annotation in marking_results["annotations"]:
                if annotation["image_id"] == image["id"]:
                    ndarr = np.array(annotation["segmentation"][0], np.int32)
                    ndarr = ndarr.reshape(-1, 1, 2).tolist()
                    parking_space_info["coordinates"].append(ndarr)
            parking_space_list.append(parking_space_info)

        return parking_space_list

    def export(
        self,
        data_to_export: list[dict[str, Any]],
        to_file: str | None = FILE_NAME,
    ) -> dict[str, Any] | None:
        """If the `to_file` parameter is omitted, the result will be returned"""
        _data_to_export = {"parkings": data_to_export}
        if to_file:
            with open(join_path(self.directory, to_file), "w") as file:
                file.write(json.dumps(_data_to_export, indent=2))
        return _data_to_export

    @lru_cache
    def start_converting(
        self,
        archive_name: str | None = None,
        file_in_archive: str = "result.json",
        to_file: str | None = FILE_NAME,
    ) -> dict[str, Any] | None:
        """
        If `archive_name` is None, the method converts data from all archives and writes them to JSON files with
        the same name as the archive has.

        If the `to_file` parameter is omitted, the result will be returned.
        """

        if archive_name:
            json_dict = self.read_json(archive_name, file_in_archive)
            converted_dict = self.convert(json_dict)
            return self.export(converted_dict, to_file)
        else:
            for path in glob.glob(join_path(self.directory, "*.zip"), recursive=True):
                _archive_name = path[len(self.directory) + 1 :]
                json_dict = self.read_json(_archive_name, file_in_archive)
                converted_dict = self.convert(json_dict)
                self.export(converted_dict, f"{_archive_name.split('.')[0]}.json")
        return None
