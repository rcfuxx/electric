import json
import logging

from electric.app import application
from electric.icharger.models import Preset, PresetIndex
from electric.tests.live.live_testcase import LiveIChargerTestCase

logger = logging.getLogger("electric.app.test.{0}".format(__name__))


class BasePresetTestCase(LiveIChargerTestCase):
    def setUp(self):
        super(LiveIChargerTestCase, self).setUp()
        self.client = application.test_client()

    def _turn_response_into_preset_object(self, response):
        return self._turn_response_into_object(response, Preset, False)

    def _turn_response_into_preset_index_object(self, response):
        return self._turn_response_into_object(response, PresetIndex, False)

    def _turn_response_into_preset_list(self, response):
        json_dict = json.loads(response.data)
        if type(json_dict) is not list:
            message = "{0} isn't a list!".format(json_dict)
            raise Exception(message)

        list_of_presets = []
        for item in json_dict:
            list_of_presets.append(Preset(item))
        return list_of_presets

    def _create_new_test_preset(self):
        test_preset_dict = self.load_json_file("presets/preset-0.json")
        self.assertIsNotNone(test_preset_dict)
        test_preset = Preset(test_preset_dict)
        test_preset.name = "Test Preset"
        return test_preset

    def _find_preset_with_name(self, name):
        preset_index = self._turn_response_into_preset_index_object(self.client.get("/presetorder"))
        for index in preset_index.range_of_presets():
            preset_endpoint = "/preset/{0}".format(index)
            response = self.client.get(preset_endpoint)
            preset = self._turn_response_into_preset_object(response)
            if preset:
                if preset.name == name:
                    return preset
        return None

    def _find_or_create_last_test_preset(self):
        preset_index, all_presets, test_preset = self._find_last_test_preset()
        if test_preset:
            return preset_index, all_presets, test_preset

        logger.info("No test preset exists. Will create at {0}".format(preset_index.first_empty_slot))

        test_preset = self._create_new_test_preset()

        native = test_preset.to_native()
        preset_endpoint = "/preset/{0}".format(preset_index.first_empty_slot)
        response = self.client.put(preset_endpoint, data=json.dumps(native), content_type='application/json')
        self.assertEqual(response.status_code, 200)

        # Read the preset list back in, and check that we have one more item
        new_preset_index = self._turn_response_into_preset_index_object(self.client.get("/presetorder"))
        self.assertEqual(new_preset_index.number_of_presets, preset_index.number_of_presets + 1)
        self.assertEqual(new_preset_index.first_empty_slot, preset_index.first_empty_slot + 1)

        # The other presets should be identical to before.
        new_presets = self._turn_response_into_preset_list(self.client.get("/preset"))
        for index, old_preset in enumerate(all_presets):
            new_preset = new_presets[index]
            self.assertEqual(new_preset, old_preset)

        # Force a relookup, so we get the latest index and all presets
        return self._find_last_test_preset()

    def remove_test_preset(self):
        preset_index, all_presets, test_preset = self._find_last_test_preset()

        if test_preset:
            print "Index: {0}".format(preset_index.to_native())
            print "Test preset has display index {1}: {0}".format(test_preset.to_native(), test_preset.index)

            response = self.client.delete("/preset/{0}".format(test_preset.index))
            self.assertEqual(response.status_code, 200)

            # Check it is gone
            new_preset_index, new_presets, new_test_preset = self._find_last_test_preset()
            self.assertEqual(new_preset_index.number_of_presets, preset_index.number_of_presets - 1)

            # Because we are deleting the last one, the first empty slot should also decrease
            self.assertEqual(new_preset_index.first_empty_slot, preset_index.first_empty_slot - 1)

            # And we should not be able to get the old preset, by index, anymore
            response = self.client.get("/preset/{0}".format(test_preset.index))
            self.assertEqual(response.status_code, 404)

    def _find_last_test_preset(self):
        response = self.client.get("/preset")
        all_presets = self._turn_response_into_preset_list(response)
        self.assertIsNotNone(all_presets)

        preset_index = self._turn_response_into_preset_index_object(self.client.get("/presetorder"))
        self.assertIsNotNone(preset_index)

        test_preset = None
        for index in preset_index.range_of_presets():
            preset = all_presets[index]
            if preset.name == "Test Preset":
                test_preset = preset
        return preset_index, all_presets, test_preset
