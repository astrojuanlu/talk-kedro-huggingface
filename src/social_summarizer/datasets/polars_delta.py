"""``CSVDataset`` loads/saves data from/to a CSV file using an underlying
filesystem (e.g.: local, S3, GCS). It uses polars to handle the CSV file.
"""
import logging
from copy import deepcopy
from pathlib import PurePosixPath
from typing import Any, Dict

import fsspec
import polars as pl
from deltalake.exceptions import TableNotFoundError
from kedro.io.core import (
    PROTOCOL_DELIMITER,
    AbstractVersionedDataset,
    DatasetError,
    Version,
    get_filepath_str,
    get_protocol_and_path,
)

logger = logging.getLogger(__name__)


class DeltaDataset(AbstractVersionedDataset[pl.DataFrame, pl.DataFrame]):
    """``DeltaDataset`` loads/saves data from/to a Delta Table using an underlying
    filesystem (e.g.: local, S3, GCS). It returns a Polars dataframe.
    """

    DEFAULT_LOAD_ARGS: Dict[str, Any] = {}
    DEFAULT_SAVE_ARGS: Dict[str, Any] = {}

    def __init__(  # noqa: PLR0913
        self,
        filepath: str,
        load_args: Dict[str, Any] = None,
        save_args: Dict[str, Any] = None,
        version: Version = None,
        credentials: Dict[str, Any] = None,
        fs_args: Dict[str, Any] = None,
        metadata: Dict[str, Any] = None,
    ) -> None:
        _fs_args = deepcopy(fs_args) or {}
        _credentials = deepcopy(credentials) or {}

        protocol, path = get_protocol_and_path(filepath, version)
        if protocol == "file":
            _fs_args.setdefault("auto_mkdir", True)

        self._protocol = protocol
        self._storage_options = {**_credentials, **_fs_args}
        self._fs = fsspec.filesystem(self._protocol, **self._storage_options)

        self.metadata = metadata

        super().__init__(
            filepath=PurePosixPath(path),
            version=version,
            exists_function=self._fs.exists,
            glob_function=self._fs.glob,
        )

        # Handle default load and save arguments
        self._load_args = deepcopy(self.DEFAULT_LOAD_ARGS)
        if load_args is not None:
            self._load_args.update(load_args)
        self._save_args = deepcopy(self.DEFAULT_SAVE_ARGS)
        if save_args is not None:
            self._save_args.update(save_args)

        if "storage_options" in self._save_args or "storage_options" in self._load_args:
            logger.warning(
                "Dropping 'storage_options' for %s, "
                "please specify them under 'fs_args' or 'credentials'.",
                self._filepath,
            )
            self._save_args.pop("storage_options", None)
            self._load_args.pop("storage_options", None)

    def _describe(self) -> Dict[str, Any]:
        return {
            "filepath": self._filepath,
            "protocol": self._protocol,
            "load_args": self._load_args,
            "save_args": self._save_args,
            "version": self._version,
        }

    def _load(self) -> pl.DataFrame:
        load_path = str(self._get_load_path())

        load_path = f"{self._protocol}{PROTOCOL_DELIMITER}{load_path}"
        # HACK: If the table is empty, return an empty DataFrame
        try:
            return pl.read_delta(
                load_path, storage_options=self._storage_options, **self._load_args
            )
        except TableNotFoundError:
            return pl.DataFrame()

    def _save(self, data: pl.DataFrame) -> None:
        save_path = get_filepath_str(self._get_save_path(), self._protocol)

        save_path = f"{self._protocol}{PROTOCOL_DELIMITER}{save_path}"
        data.write_delta(
            save_path, storage_options=self._storage_options, **self._save_args
        )

    def _exists(self) -> bool:
        try:
            load_path = get_filepath_str(self._get_load_path(), self._protocol)
        except DatasetError:
            return False

        return self._fs.exists(load_path)
