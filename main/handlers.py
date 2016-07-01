import http.client
import logging

import tornado.web
import tornado.ioloop

import fs
import db

class BaseHandler(tornado.web.RequestHandler):
    def prepare(self):
        """Initialize all resources"""
        self.log = logging.getLogger("tornado.general")
        self.fs = fs.Worker(self.request.uri)

        self.db = db

    def delete(self, _=None):
        """Delete is basically the same for both files and folders"""
        try:
            self.fs.remove_file_or_folder()
            self.add_callback(self.db.file_or_folder_deleted, self.fs.updates)
            # self.write(self.fs.updates)
        except FileNotFoundError:
            self.send_error(404)
        except PermissionError:
            self.send_error(403)

    def write(self, chunk):
        """Override this method to have access over response body"""
        self.repsonse = chunk
        super().write(chunk)

    def write_error(self, status_code, msg=None, **kwargs):
        """Write errors as json in body"""
        self.write({
            "errors": [{
                "error_code": status_code,
                "error_msg": msg if msg else http.client.responses[status_code]
            }]
        })
        self.finish()

    def on_finish(self):
        """Add some logging, release resources"""
        self.fs.close_file()

    def add_callback(self, callback, *a, **kw):
        tornado.ioloop.IOLoop.instance().add_callback(callback, *a, **kw)

    def add_timeout(self, deadline, callback, *a, **kw):
        tornado.ioloop.IOLoop.instance().add_timeout(deadline, callback, *a, **kw)


class DirHandler(BaseHandler):
    def put(self):
        """Create new directory with this method"""
        try:
            self.fs.create_folder()
            self.add_callback(self.db.folder_created, self.fs.updates)
            self.write(self.fs.updates)
        except (FileExistsError, NotADirectoryError):
            self.send_error(409)
        except PermissionError:
            self.send_error(403)

    def get(self):
        """Get dir tree and stat info"""
        try:
            # TODO: change to read from BD
            self.write(self.fs.get_tree(full_tree=True))
        except FileNotFoundError:
            self.send_error(404)

@tornado.web.stream_request_body
class FileHandler(BaseHandler, tornado.web.StaticFileHandler):
    def data_received(self, chunk):
        """Receive uploaded files chunk by chunk"""
        try:
            self.fs.save_file_chunk(chunk)
        except FileExistsError:
            self.send_error(409)
        except NotADirectoryError:
            self.send_error(409)
        except IOError:
            self.send_error(500)

    def put(self, _):
        """Called when all chunks are received"""
        # TODO: add update tree
        try:
            self.fs.open_file()
            self.fs.close_file()
            self.add_callback(self.db.file_uploaded, self.fs.updates)
            self.write(self.fs.updates)
        except FileExistsError:
            self.send_error(409)
