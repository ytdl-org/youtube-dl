import unittest
from youtube_dl.extractor.mixcloud import server_numbers

class TestMixcloud(unittest.TestCase):
    def test_server_numbers(self):
        self.assertEqual([n for n in server_numbers(2, (1, 5))],
            [2, 3, 1, 4, 5])
        self.assertEqual([n for n in server_numbers(1, (1, 5))],
            [1, 2, 3, 4, 5])
        self.assertEqual([n for n in server_numbers(5, (1, 5))],
            [5, 4, 3, 2, 1])
        self.assertEqual([n for n in server_numbers(-1, (1, 5))],
            [-1, 1, 2, 3, 4, 5])

if __name__ == '__main__':
    unittest.main()
