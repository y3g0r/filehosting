import os
import tempfile
import urllib.parse
from collections import OrderedDict
import datetime as d
from pprint import pprint

from tornado.options import options

import utils
from pathlib import PurePath

class Path:
    def __init__(self, uri="", abspath=""):
        if not any((uri, abspath)): raise ValueError("either uri or abspath should be provided to constructor")
        self._base_dir = options.storage_path.rstrip(os.path.sep)
        self._uri_based = urllib.parse.unquote(uri)
        self._public_path = None
        self._abspath = abspath.rstrip(os.path.sep)
        self._db_path = None
        self._create_dir_for_file = False

    @property
    def abspath(self):
        if not self._abspath:
            self._abspath = os.path.normpath(os.path.join(self._base_dir, self._uri_based.strip(os.path.sep)))
        return self._abspath

    @property
    def public_path(self):
        if not self._public_path:
            self._public_path = self._abspath[len(self._base_dir):] or self._uri_based
        return self._public_path

    @property
    def base_dir(self):
        return self._base_dir

    @property
    def create_dir_path(self):
        folder_path = os.path.dirname(self.abspath) if self._create_dir_for_file else self.abspath
        return folder_path if self.base_dir in folder_path else self.base_dir

    def validate(self):
        assert os.path.isabs(self.abspath) and os.path.commonpath((self.abspath, self._base_dir)) == self._base_dir

    def work_with_file(self):
        return self._uri_based[-1] != "/"


class Worker:
    MODIFIED_DATETIME_FORMAT = "%a, %d %b %Y %H:%M:%S"
    TEMP_FILE_DIR = '/tmp'

    def __init__(self, uri, openfile=False):
        self.path = Path(uri)
        self._fo = None
        self._updated_path_root = None
        self._updates = None

    @property
    def updates(self):
        if self._updates is None:
            self._updates = self.get_updated_info()
        return self._updates

    @property
    def updated_path_root(self):
        if not self._updated_path_root:
            return None
        else:
            return self._updated_path_root

    @updated_path_root.setter
    def updated_path_root(self, value):
        if self.path.base_dir not in value:
            self._updated_path_root = self.path.base_dir
        else:
            self._updated_path_root = value

    def work_with_file(self):
        """Answers to the question are we working with file (True if file, False if Dir)"""
        return self.path.work_with_file()

    def open_file(self):
        if not self._fo:
            if os.path.isfile(self.path.abspath):
                raise FileExistsError
            self._fo = tempfile.NamedTemporaryFile(
                'wb', dir=Worker.TEMP_FILE_DIR, delete=False)


    def save_file_chunk(self, chunk):
        if not self._fo:
            self.open_file()
        self._fo.write(chunk)

    def close_file(self, interrupted=False):

        if self._fo is not None:
            tempname = self._fo.name
            self._fo.close()
            if not interrupted:
                try:
                    self.path._create_dir_for_file = True
                    try:
                        self.create_folder()
                    except FileExistsError: pass
                    finally:
                        os.rename(tempname, self.path.abspath)
                except FileNotFoundError: pass

    def create_folder(self):
        """Create folder, return path where was update"""
        if os.path.isdir(self.path.create_dir_path):
            raise FileExistsError
        self.updated_path_root = self.mkdir_p()

    def remove_file_or_folder(self):
        self._updates = self.get_updated_info()
        try:
            self.rm_dirs()
        except NotADirectoryError:
            self.rm_file()
        finally:
            if self.path.abspath not in self.path.base_dir:
                self._updates['modified'] = d.datetime.fromtimestamp(os.path.getmtime(self.updated_path_root)).strftime(
                    self.MODIFIED_DATETIME_FORMAT)

    def rm_dirs(self):
        import shutil
        shutil.rmtree(self.path.abspath)

    def rm_file(self):
        os.remove(self.path.abspath)

    def mkdir_p(self):
        prev = self.path.base_dir
        for cur in Worker.iterate_path(self.path.create_dir_path, root=self.path.base_dir):
            if os.path.isdir(cur):
                prev = cur
            else:
                os.makedirs(self.path.create_dir_path)
                break
        return prev


    def lock_components(self):
        """Return paths based on request uri, that has to be checked before performing writing ops"""
        for path in Worker.iterate_path(self.path.public_path):
            if path != "/":
                yield path

        yield (self.path.public_path + "/") if self.path.work_with_file() else (self.path.public_path.rstrip("/"))

    @staticmethod
    def iterate_path(top, root=None, trailing_slash=False, from_root_to_top=True):
        if not root:
            root = "/"
        if not all(map(os.path.isabs, (top, root))):
            raise ValueError("subfolder and root must start with '/'")
        if top.startswith(root):
            members = [top] + list(map(str, PurePath(top).parents))
            if not from_root_to_top:
                members = reversed(members)

            for member in members:
                if root not in member: break
                yield member + "/" if member not in (root, top) and trailing_slash else member



    def get_tree(self, full_tree=False):
        import stat

        def from_root_to_leafs(file_path):
            current = OrderedDict()
            stat_info = os.stat(file_path)
            current['path'] = file_path[len(self.path.base_dir):] or "/"
            current['bytes'] = stat_info.st_size
            current['size'] = utils.sizeof_fmt(stat_info.st_size)
            current['modified'] = d.datetime.fromtimestamp(stat_info.st_mtime).strftime(self.MODIFIED_DATETIME_FORMAT)
            if stat.S_ISDIR(stat_info.st_mode):
                current['is_dir'] = True
                current['children'] = [from_root_to_leafs(os.path.join(file_path, x)) for x in os.listdir(file_path)]
            else:
                current['is_dir'] = False
            return current

        return from_root_to_leafs(self.path.abspath)

    def get_updated_info(self):
        import stat
        if not self.updated_path_root:
            self.updated_path_root = os.path.dirname(self.path.abspath)
        lower = self.updated_path_root
        upper = self.path.abspath

        # TODO: can be optimized to query disk only once
        def from_leaf_to_root():
            children = []
            current = None
            for file_path in Worker.iterate_path(upper, lower):
                current = OrderedDict()
                stat_info = os.stat(file_path)
                current['path'] = file_path[len(self.path.base_dir):] or "/"
                current['bytes'] = stat_info.st_size
                current['size'] = utils.sizeof_fmt(stat_info.st_size)
                current['modified'] = d.datetime.fromtimestamp(stat_info.st_mtime).strftime(
                    self.MODIFIED_DATETIME_FORMAT)
                if stat.S_ISDIR(stat_info.st_mode):
                    current['is_dir'] = True
                    current['children'] = children
                else:
                    current['is_dir'] = False
                children = current
            return current

        return from_leaf_to_root()
