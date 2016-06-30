import logging
import os
import uuid
from datetime import datetime, timedelta
from pprint import pprint

import tornado.ioloop
from tornado.options import options
from playhouse.sqlite_ext import SqliteExtDatabase, ClosureTable
from peewee import (Model, CharField, ForeignKeyField, IntegerField,
                    BooleanField, DateTimeField, DoesNotExist, OperationalError)

import fs

log = logging.getLogger("tornado.general")

"""
connect to db
load closure module
create tables
"""
db = SqliteExtDatabase(options.db_file)
db.load_extension(options.sqlite_closure_table_so)


class File(Model):
    path = CharField()
    bytes = IntegerField()
    is_dir = BooleanField()
    modified = DateTimeField()
    size = CharField()  # redundant
    parent = ForeignKeyField('self', null=True, related_name='children')

    class Meta:
        database = db


FileClosure = ClosureTable(File)

File.create_table(True)
FileClosure.create_table(True)


def traverse(statinfo, func):
    func(statinfo)
    if statinfo.get("children"):
        traverse(statinfo['children'], func)


# # Without `get_or_create`, we might write:
# try:
#     person = Person.get(
#         (Person.first_name == 'John') &
#         (Person.last_name == 'Lennon'))
# except Person.DoesNotExist:
#     person = Person.create(
#         first_name='John',
#         last_name='Lennon',
#         birthday=datetime.date(1940, 10, 9))
#
# person, created = Person.get_or_create(
#     first_name='John',
#     last_name='Lennon',
#     defaults={'birthday': datetime.date(1940, 10, 9)})

def node_update(statinfo):
    node_path = statinfo['path']
    parent = None
    try:
        parent = File.get(File.path == os.path.dirname(node_path))
    except DoesNotExist:
        log.warning("Didn't find parent of %s. This maybe a sign of a problem with data persistence model", node_path)

    # node_info = {
    #     "path" : statinfo['path'],
    #     "bytes" : statinfo['bytes'],
    #     "is_dir" : statinfo['is_dir'],
    #     "modified" : datetime.strptime(statinfo['modified'], fs.FSWorker.MODIFIED_DATETIME_FORMAT),
    #     "size" : statinfo['size'],
    #     "parent" : parent
    # }
    node_info = statinfo.copy()
    # if "children" in node_info:
    #     del node_info["children"]
    del node_info["path"]
    node_info['modified'] = datetime.strptime(node_info['modified'], fs.Worker.MODIFIED_DATETIME_FORMAT)
    node_info['parent'] = parent
    node, created = File.get_or_create(
        path=node_path,
        defaults=node_info
    )

    if created:
        log.info("New node '%s' with parent '%s' was created", node_path, parent.path if parent else "NULL")
    else:
        node.modified = node_info['modified']
        node.parent = node_info['parent'] # if parent else node
        node.save()
        log.info("Node '%s' with parent '%s' was updated", node_path, parent.path if parent else "NULL")



def _generic(statinfo):
    """
    - delete file from db
    - update parent folder's `modified` field
    :param statinfo(collections.OrderedDict):
    {
        "bytes": 39,
        "is_dir": false,
        "modified": "Wed, 29 Jun 2016 10:37:12",
        "path": "/johntravolta4",
        "size": "39.0B"
    }
    :return:
    """

    with db.transaction():
        traverse(statinfo, node_update)


def file_or_folder_deleted(update):
    node = update
    prev = None
    while "children" in node and node["children"]:
        prev = node
        node = node["children"]
    if prev:
        prev["children"] = []
    if node['is_dir']:
        folder_deleted(update, node)

    else:
        file_deleted(update, node)



def file_uploaded(update):
    """
    - upload file stat info to db
    - update parent folder's `modified` field
    {
        "bytes": 39,
        "is_dir": false,
        "modified": "Wed, 29 Jun 2016 10:37:12",
        "path": "/johntravolta4",
        "size": "39.0B"
    }
    :return:
    """
    try:
        db.connect()
        debug = str(uuid.uuid4())
        log.info("File %s has been created. Updating DB  with quert_id %s", update['path'], debug)
        _generic(update)
        log.info("Successfully updated database with quert_id %s", debug)
    except OperationalError:
        log.exception("Failed on DB operation. Adding callback with timeout")
        tornado.ioloop.IOLoop.instance().add_timeout(timedelta(seconds=5), folder_created, update)


def file_deleted(update_struct, deleted_node):
    """
    - delete file from db
    - update parent folder's `modified` field
    :param rminfo(collections.OrderedDict):
    {
        "is_dir": False,
        "path": self._part_path,
        "modified": None # Attention, here modified is datetime obj
    }
    :return:
    """
    try:
        db.connect()
        debug = str(uuid.uuid4())
        log.info("File %s has been deleted. Updating DB  with quert_id %s", deleted_node['path'], debug)
        with db.transaction():
            traverse(update_struct, node_update)
            del_node(deleted_node)
        log.info("Successfully updated database with quert_id %s", debug)
    except OperationalError:
        log.exception("Failed on DB operation. Adding callback with timeout")
        tornado.ioloop.IOLoop.instance().add_timeout(timedelta(seconds=5), folder_created, update_struct, deleted_node)


def folder_created(update):
    """
    - upload folder stat info to db
    - update parent folder's `modified` field
    :return:
        """
    try:
        db.connect()
        debug = str(uuid.uuid4())
        log.info("Folder %s has been created. Updating DB  with quert_id %s", update['path'], debug)
        _generic(update)
        log.info("Successfully updated database with quert_id %s", debug)
    except OperationalError:
        log.exception("Failed on DB operation. Adding callback with timeout")
        tornado.ioloop.IOLoop.instance().add_timeout(timedelta(seconds=5), folder_created, update)


def folder_deleted(update_struct, deleted_node):
    """
    - delete folder,
    - all subfolders and files
    - update parent folder's `modified` field
    :return:
    """
    try:
        db.connect()
        debug = str(uuid.uuid4())
        log.info("Folder %s has been deleted. Updating DB  with quert_id %s", deleted_node['path'], debug)
        with db.transaction():
            traverse(update_struct, node_update)
            del_node_tree(deleted_node)
        log.info("Successfully updated database with quert_id %s", debug)
    except OperationalError:
        log.exception("Failed on DB operation. Adding callback with timeout")
        tornado.ioloop.IOLoop.instance().add_timeout(timedelta(seconds=5), folder_created, update_struct, deleted_node)

def del_node(node):
    try:
        query = File.delete().where(File.path == node['path'])
        deleted = query.execute()
        if not deleted:
            raise DoesNotExist
        log.info("deleted {} descendants".format(deleted))
    except DoesNotExist:
        log.error("Didn't find file node %s. This maybe a sign of a problem with data persistence model", node['path'])

def del_node_tree(node):

    try:
        parent = File.get(File.path == node['path'])
        subquery = (FileClosure
                    .select(FileClosure.id)
                    .where(FileClosure.root == parent))
        query = File.delete().where(File.id << subquery)
        log.info("deleted {} descendants".format(query.execute()))
        # for descendant in File.delete().where(File.id << subquery):
        #     print(descendant.path)

    except DoesNotExist:
        log.error("Didn't find folder node %s. This maybe a sign of a problem with data persistence model", node['path'])


