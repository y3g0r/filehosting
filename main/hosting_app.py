import configparser
import logging
import os
import signal
import time

import tornado.gen
import tornado.ioloop
import tornado.options
import tornado.process
import tornado.web
from tornado.httpserver import HTTPServer
from tornado.options import define, options

import config
from handlers import FileHandler, DirHandler

_SHUTDOWN_TIMEOUT = 30


def make_safe_shutdownable(srv):
    io_loop = srv.io_loop or tornado.ioloop.IOLoop.instance()

    def stop_handler(signum, stack_frm, *args, **keywords):

        logging.getLogger("tornado.general").warning(
            "{signame} signal received. Closing HTTP server. "
            "Waiting up to {timeout} secs for all active tasks to be finished.".format(
                signame={
                    signal.SIGQUIT: "SIGQUIT",
                    signal.SIGTERM: "SIGTERM",
                    signal.SIGINT: "SIGINT"
                }[signum], timeout=_SHUTDOWN_TIMEOUT
            ))

        def shutdown():
            def stop_loop():
                now = time.time()
                if now < deadline and (io_loop._callbacks or io_loop._timeouts or len(io_loop._handlers) > 1):
                    io_loop.add_timeout(now + 1, stop_loop)
                else:
                    io_loop.stop()

            srv.stop()  # this may still disconnection backlogs at a low probability
            deadline = time.time() + _SHUTDOWN_TIMEOUT
            stop_loop()

        io_loop.add_callback(shutdown)

    signal.signal(signal.SIGQUIT, stop_handler)  # SIGQUIT is send by our supervisord to stop this server.
    signal.signal(signal.SIGTERM, stop_handler)  # SIGTERM is send by Ctrl+C or supervisord's default.
    signal.signal(signal.SIGINT, stop_handler)


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            ('.*/', DirHandler),
            ('/(.+)', FileHandler, {"path": options.storage_path}),
        ]
        settings = {
            "static_path": options.storage_path
        }
        super(Application, self).__init__(handlers, **settings)
        self.log = logging.getLogger("torando.general")
        self.locks = dict()


def main():
    tornado.options.parse_command_line()
    server = HTTPServer(Application(), max_buffer_size=1024 * 1024 * options.file_size_limit)
    make_safe_shutdownable(server)
    server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()
