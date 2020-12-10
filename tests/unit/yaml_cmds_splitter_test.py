#!/usr/bin/env python3
import unittest

import yaml

from rest.utils.yaml_cmds_splitter import YamlCommandsSplitter


class RenderTestCase(unittest.TestCase):

    def test_full_yml(self):
        yaml_config_string = """
        env:
          MINE: yours
        before_install:
          - echo before_install
        install:
          - echo install
        after_install:
          - echo after_install
        before_script:
          - echo before_script
        script:
          - echo script
        after_script:
          - echo after_script
        """
        splitter = YamlCommandsSplitter(yaml.safe_load(yaml_config_string))
        self.assertEqual(len(splitter.get_cmds_in_order()), 6)

    def test_full_yml_skipped_key(self):
        yaml_config_string = """
        env:
          MINE: yours
        this_key_is_skipped:
          - echo skipped
        before_install:
          - echo before_install
        install:
          - echo install
        after_install:
          - echo after_install
        before_script:
          - echo before_script
        script:
          - echo script
        after_script:
          - echo after_script
        """
        splitter = YamlCommandsSplitter(yaml.safe_load(yaml_config_string))
        self.assertEqual(len(splitter.get_cmds_in_order()), 6)

    def test_missing_before_yml(self):
        yaml_config_string = """
        env:
          MINE: yours
        before_script:
        script:
          - echo script
        after_script:
          - echo after_script
        """
        splitter = YamlCommandsSplitter(yaml.safe_load(yaml_config_string))
        self.assertEqual(len(splitter.get_cmds_in_order()), 2)

    def test_missing_after_yml(self):
        yaml_config_string = """
        env:
          MINE: yours
        before_script:
          - echo before_script
        script:
          - echo script
        after_script:
        """
        splitter = YamlCommandsSplitter(yaml.safe_load(yaml_config_string))
        self.assertEqual(len(splitter.get_cmds_in_order()), 2)

    def test_missing_script_yml(self):
        yaml_config_string = """
        env:
          MINE: yours
        before_script:
          - echo before_script
        script:
        after_script:
          - echo after_script
        """
        try:
            YamlCommandsSplitter(yaml.safe_load(yaml_config_string)).get_cmds_in_order()
        except Exception as e:
            self.assertEqual("Mandatory section 'script' was not found or it was empty.", e.__str__())


if __name__ == '__main__':
    unittest.main()
