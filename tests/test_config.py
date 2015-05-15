import unittest
import config
import re


class TestConfig(unittest.TestCase):
    def unpack(self, c):
        return c.__dict__['_Config__config']

    def load(self, name=None, fallback_name=None, add_defaults=False):
        path = None
        if name is not None:
            path = "tests/configs/{}.json".format(name)

        fallback_path = None
        if fallback_name is not None:
            fallback_path = "tests/configs/{}.json".format(fallback_name)

        c = config.Config.from_file(path=path, fallback_path=fallback_path)
        if (add_defaults):
            c.add_defaults()

        return c

    def is_subsequence(self, s, of):
        return re.search('.*'.join(s), of)

    def test_fallback_loading(self):
        with self.assertRaisesRegex(TypeError, "^invalid file: None$"):
            self.load()

        c = self.load(fallback_name='fallback_config1')
        self.assertEqual(
            self.unpack(c),
            {
                "a": 1,
                "b": [True, False],
                "c": {
                    "d": 2.0
                }
            }
        )

    def test_config_merging(self):
        c = self.load(name='config1',
                      fallback_name='fallback_config1')
        self.assertEqual(
            self.unpack(c),
            {
                "a": 2,
                "b": [True, False],
                "c": {
                    "d": 2.0,
                    "e": False
                }
            }
        )

    def test_default_adding(self):
        c = self.load(name='config2',
                      fallback_name='fallback_config2',
                      add_defaults=True)
        self.assertEqual(
            self.unpack(c),
            {
                "achievements": {
                    "a": {
                        "count": {
                            "tables": [],
                            "thresholds": [10, 100],
                            "badges": ["A", "B", "C"],
                        },
                        "handlers": {"x": "y"}
                    },
                    "b": {
                        "count": {
                            "tables": [],
                            "thresholds": [10, 100],
                            "badges": ["a", "b", "c"],
                        },
                        "handlers": {"x": "y"}
                    }
                }
            }
        )


if __name__ == '__main__':
    unittest.main()
