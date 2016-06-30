import configparser
import os

from tornado.options import define, options

define("config", default=os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "config.ini"),
       help='path to config file')

def parse_config_file():
    config = configparser.ConfigParser()
    config.read(options.config)
    define("port",
           default=int(config.get('Main', 'port', fallback=8888)),
           type=int,
           help='port on with to run http server')
    define('storage-path',
           default=config.get('Main', 'storage_path', fallback='/tmp/hosting_app'),
           help='path where to store all the folders and files')
    define('file-size-limit',
           default=int(config.get('Main', 'file_size_limit', fallback=4096)),
           type=int,
           help='Upper limit for files Xchange in MB. '
                'Can be bigger then amount of RAM on your machine '
                'because files are not buffered entirely before processing but instead processed by chunks up to 16 KB')
    define('db_file',
           default=config.get('Database', 'db_file'),
           help='Full path to sqlite3 db file')
    define('sqlite_closure_table_so',
           default=config.get('Database', 'sqlite_closure_table_so'),
           help=''
                'Path to compiled shared library '
                'for sqlite transitive closure table. '
                'To obtain this file perform the following actions:\n'
                '$ git clone https://gist.github.com/coleifer/7f3593c5c2a645913b92 closure\n'
                '$ cd closure/\n'
                '$ gcc -g -fPIC -shared closure.c -o closure.so')
    for logging_option in options.as_dict().keys():
        if logging_option.startswith('log') and logging_option in config['Logging']:
            options.__setattr__(logging_option, config['Logging'][logging_option])


parse_config_file()
