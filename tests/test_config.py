import unittest
import config
import re


class TestConfig(unittest.TestCase):
    def unpack(self, c):
        return c.__dict__['_Config__config']

    def load(self, name=None, fallback_name=None, add_defaults=False, validate=False):
        path = None
        if name is not None:
            path = "tests/configs/{}.json".format(name)
        fallback_path = None
        if fallback_name is not None:
            fallback_path = "tests/configs/{}.json".format(fallback_name)
        c = config.Config.from_file(path=path, fallback_path=fallback_path)
        if (add_defaults):
            c.add_defaults()
        if (validate):
            c.validate()
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
                "stats": {
                    "default": {
                        "thresholds": [10, 100],
                        "levels": ["a", "b", "c"]
                    },
                    "a": {
                        "thresholds": [10, 100],
                        "levels": ["A", "B", "C"]
                    },
                    "b": {
                        "thresholds": [10, 100],
                        "levels": ["a", "b", "c"]
                    }
                }
            }
        )

    def test_config_validation(self):
        with self.assertRaises(config.ValidationError) as cm:
            self.load(name='config3',
                      fallback_name='fallback_config2',
                      add_defaults=True,
                      validate=True)
        msg = cm.exception.__str__()
        self.assertTrue(
            self.is_subsequence("At least one table should be defined for 'stats.a'", msg)
        )
        self.assertTrue(
            self.is_subsequence("Wrong quantity of thresholds defined for specified levels for 'stats.b'", msg)
        )
        self.assertTrue(
            self.is_subsequence("Wrong quantity of thresholds defined for specified levels for 'stats.c'", msg)
        )
        self.assertTrue(
            self.is_subsequence("At least one table should be defined for 'stats.d'", msg)
        )

if __name__ == '__main__':
    unittest.main()
