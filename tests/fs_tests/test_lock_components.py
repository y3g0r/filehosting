import unittest

from tornado.options import define

from fs import Worker

define("storage-path", "/why/do/you/need/me", callback=lambda: None)

class TestWorkerLockComponents(unittest.TestCase):

    def setUp(self):
        pass

    def test_components_returned_for_file_url(self):
        dummy = Worker("/nested/file")
        self.assertSetEqual(set(dummy.lock_components()), {"/nested", "/nested/file", "/nested/file/"})

    def test_components_returned_for_dir_url(self):
        dummy = Worker("/nested/dir/")
        self.assertSetEqual(set(dummy.lock_components()), {"/nested", "/nested/dir", "/nested/dir/"})


if __name__ == "__main__":
    unittest.main()