import unittest
from fs import Worker

class TestWorkerIteratePathMethod(unittest.TestCase):

    def test_If_root_not_in_subfolder_Returns_empty_list(self):
        res = list(Worker.iterate_path("/a/b/c", "/e/b"))

        self.assertListEqual(res, [])

    def test_If_not_abs_path_Raise_ValueError(self):
        with self.assertRaises(ValueError):
            for p in Worker.iterate_path("a/b", "a/c"):
                print("Never printed", p)

        with self.assertRaises(ValueError):
            next(Worker.iterate_path(top="good/not", root="/good"))

        with self.assertRaises(ValueError):
            next(Worker.iterate_path(top="/good/", root="good/not"))

    def test_Returns_empty_when_root_and_subfolder_swapped(self):
        res = list(Worker.iterate_path("/base/dir", "/base/dir/subfolder"))

        self.assertListEqual(res, [])

    def test_when_subfolder_equals_root_returns_root(self):
        res = list(Worker.iterate_path(top="/", root="/"))
        self.assertListEqual(res, ["/"])

        res = list(Worker.iterate_path(top="/"))
        self.assertListEqual(res, ["/"])

        res = list(Worker.iterate_path(top="/b", root="/b"))
        self.assertListEqual(res, ["/b"])

    def test_reverse_order_when_subfolder_equals_root_returns_root(self):
        res = list(Worker.iterate_path(top="/", root="/", from_root_to_top=True))
        self.assertListEqual(res, ["/"])

        res = list(Worker.iterate_path(top="/", from_root_to_top=True))
        self.assertListEqual(res, ["/"])

        res = list(Worker.iterate_path(top="/a", root="/a", from_root_to_top=True))
        self.assertListEqual(res, ["/a"])

    def test_default_behavior_is_backward_enumeration_folders_without_slashes(self):
        res = list(Worker.iterate_path("/red/hot/chili/peppers"))
        self.assertListEqual(res, ['/red/hot/chili/peppers', '/red/hot/chili', '/red/hot', '/red', '/'])

    def test_reverse_false_forward_enumeration_folders_without_slashes(self):
        res = list(Worker.iterate_path("/red/hot/chili/peppers", from_root_to_top=False))
        self.assertListEqual(res, ['/', '/red', '/red/hot', '/red/hot/chili', '/red/hot/chili/peppers'])

    def test_trailing_slashes_to_distinguish_folders_and_files(self):
        res = list(Worker.iterate_path("/red/hot/chili/peppers", trailing_slash=True))
        self.assertListEqual(res, ['/red/hot/chili/peppers', '/red/hot/chili/', '/red/hot/', '/red/', '/'])

    def test_trailing_slashes_to_distinguish_folders_and_files_from_root_to_top(self):
        res = list(Worker.iterate_path("/red/hot/chili/peppers", from_root_to_top=False, trailing_slash=True))
        self.assertListEqual(res, ['/', '/red/', '/red/hot/', '/red/hot/chili/', '/red/hot/chili/peppers'])


if __name__ == "__main__":
    unittest.main()