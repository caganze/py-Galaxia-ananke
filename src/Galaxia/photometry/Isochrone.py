#!/usr/bin/env python
"""
Docstring
"""
import pathlib
from glob import glob

from ..constants import *
from . import Photometry
from .IsochroneFile import IsochroneFile

__all__ = ['Isochrone']


class Isochrone:
    _Age = 'Age'
    _M_ini = 'M_ini'
    _M_act = 'M_act'
    _Lum = 'Lum'
    _T_eff = 'T_eff'
    _Grav = 'Grav'
    _required_keys = [_Age, _M_ini, _M_act, _Lum, _T_eff, _Grav]
    def __init__(self, *args) -> None:
        if not args:
            raise TypeError("Isochrone requires at least one argument")
        elif len(args) == 1:
            self._path = pathlib.Path(args[0])
        elif len(args) == 2:
            self._path = Photometry.ISOCHRONES_PATH / CUSTOM_PHOTOCAT / args[0]
            # self.path.rmdir()  # TODO
            self._write_isochrone_files(args[1])
        else:
            raise TypeError(f"Too many arguments ({len(args)} given)")
        self._isochrone_files = None
    
    def __repr__(self) -> str:
        cls = self.__class__.__name__
        description = ', '.join([(f"{prop}={getattr(self, prop)}") for prop in ['category', 'name']])
        return f'{cls}({description})'
    
    def _write_isochrone_files(self, isochrone_data: dict):
        self.path.mkdir(parents=True, exist_ok=True)
        iso_column_order = self._write_file_descriptor(isochrone_data)
        for feh, iso in isochrone_data.items():
            path = self._path / ISO_FILE_FORMAT.format(format(feh, '.6f'))
            _temp = IsochroneFile(path, iso[iso_column_order], isochrone=self)

    def _write_file_descriptor(self, isochrone_data):
        metallicities, headers = zip(*[(feh, list(iso.keys())) for feh, iso in isochrone_data.items()])
        metallicities = set(metallicities)
        if metallicities != ISO_REQUI_METAL:
            missing = ISO_REQUI_METAL.difference(metallicities)
            missing = f"misses {missing}" if missing else ""
            extra = metallicities.difference(ISO_REQUI_METAL)
            extra = f"misincludes {extra}" if extra else ""
            raise ValueError(f"Given isochrone data covers wrong set of metallicities: {missing}{' & ' if missing and extra else ''}{extra}")
        check = []
        for header in headers:
            if header not in check: check.append(header)
        if len(check) > 1:
            raise ValueError("Given isochrone dataframes have unequal headers")
        header = check[0]
        remain = set(self._required_keys).difference(header)
        if remain:
            raise ValueError(f"Given isochrone dataframes have incomplete headers: missing {remain}")
        magnames = sorted(list(set(header).difference(self._required_keys)))
        if not magnames:
            raise ValueError(f"Given isochrone dataframes have no magnitude columns")
        iso_column_order = self._required_keys + magnames
        with self.file_descriptor_path.open('w') as f: f.write(
            # f"Python_{self.name} {27} {8} {12} {' '.join(['Z087','Y106','J129','H158','F184','W149','F475W','F555W','F606W','F814W','F110W','F160W'])}\n\n")
            f"Python_{self.name} {len(iso_column_order)} {len(self._required_keys)} {len(magnames)} {' '.join(magnames)}\n\n")
        return iso_column_order

    def _prepare_isochrone_files(self):
        self._isochrone_files = list(map(lambda path: IsochroneFile(path, isochrone=self),
                                         glob(str(self._path / ISO_FILE_FORMAT.format('*')))))

    @property
    def path(self):
        return self._path
    
    @property
    def category(self):
        return self.path.parent.name
    
    @property
    def name(self):
        return self.path.name

    @property
    def file_descriptor_path(self):
        return self._path / ISO_FILE_DESCRI

    @property
    def has_file_descriptor(self):
        return self.file_descriptor_path.exists()

    @property
    def isochrone_files(self):
        if self._isochrone_files is None:
            self._prepare_isochrone_files()
        return self._isochrone_files
    
    @property
    def mag_names(self):
        if self.has_file_descriptor:
            with open(self.file_descriptor_path,'r') as f: return f.readline().strip('\n').split()[4:]
        else:
            raise NotImplementedError("Photometric system doesn't have an IsoFileDescriptor.txt file")

    @property
    def to_export_keys(self):
        return [f"{self.name.lower()}_{mag_name.lower()}" for mag_name in self.mag_names]
