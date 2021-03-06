import logging

from bzt.modules.soapui import SoapUIScriptConverter
from tests import BZTestCase, __dir__
from tests.mocks import RecordingHandler


class TestSoapUIConverter(BZTestCase):
    def test_minimal(self):
        obj = SoapUIScriptConverter(logging.getLogger(''))
        config = obj.convert_script(__dir__() + "/../soapui/project.xml")

        self.assertIn("execution", config)
        self.assertEqual(3, len(config["execution"]))
        execution = config["execution"][0]
        self.assertEqual("TestSuite 1-index", execution.get("scenario"))
        self.assertEqual(60, execution.get("hold-for"))
        self.assertEqual(10, execution.get("concurrency"))

        self.assertIn("scenarios", config)
        self.assertIn("TestSuite 1-index", config["scenarios"])

        scenario = config["scenarios"]["TestSuite 1-index"]
        self.assertIn("requests", scenario)
        self.assertEqual(3, len(scenario["requests"]))

        self.assertIn("variables", scenario)
        self.assertEqual("foo", scenario["variables"].get("something"))
        self.assertEqual("2", scenario["variables"].get("something_else"))
        self.assertEqual("json", scenario["variables"].get("route_part"))

        first_req = scenario["requests"][0]
        self.assertEqual("http://blazedemo.com/reserve.php", first_req["url"])
        self.assertEqual("test index", first_req["label"])
        self.assertIn("headers", first_req)
        self.assertEqual(first_req["headers"].get("X-Custom-Header"), "Value")
        self.assertIn("assert", first_req)
        self.assertEqual(2, len(first_req["assert"]))
        self.assertEqual("BlazeDemo", first_req["assert"][0]["contains"][0])
        self.assertEqual(False, first_req["assert"][0]["not"])
        self.assertEqual("BlazeDemou", first_req["assert"][1]["contains"][0])
        self.assertEqual(True, first_req["assert"][1]["not"])

        second_req = scenario["requests"][1]
        self.assertEqual("http://example.com/body", second_req["url"])
        self.assertEqual("posty", second_req["label"])
        self.assertEqual("POST", second_req["method"])
        self.assertIn("headers", second_req)
        self.assertEqual(second_req["headers"].get("X-Header"), "X-Value")
        self.assertEqual(second_req["headers"].get("X-Header-2"), "X-Value-2")
        self.assertIn("body", second_req)
        self.assertIn("answer", second_req["body"])
        self.assertEqual('42', second_req["body"]["answer"])
        self.assertIn("extract-xpath", second_req)
        self.assertIn("something_else", second_req["extract-xpath"])
        self.assertEqual("//head", second_req["extract-xpath"]["something_else"]["xpath"])

        third_req = scenario["requests"][2]
        self.assertEqual("http://localhost:9999/api/${route_part}", third_req["url"])
        self.assertEqual("/api/json", third_req["label"])
        self.assertIn("extract-jsonpath", third_req)
        self.assertIn("something", third_req["extract-jsonpath"])
        self.assertEqual("$.baz", third_req["extract-jsonpath"]["something"]["jsonpath"])

    def test_find_test_case(self):
        obj = SoapUIScriptConverter(logging.getLogger(''))
        config = obj.convert_script(__dir__() + "/../soapui/project.xml")

        scenarios = config["scenarios"]
        self.assertEqual(len(scenarios), 3)

        target_scenario = scenarios["TestSuite 1-index"]
        found_name, found_scenario = obj.find_soapui_test_case("index", scenarios)
        self.assertEqual(target_scenario, found_scenario)

    def test_find_test_case_empty(self):
        log_recorder = RecordingHandler()
        obj = SoapUIScriptConverter(logging.getLogger(''))
        obj.log.addHandler(log_recorder)

        config = obj.convert_script(__dir__() + "/../soapui/project.xml")

        scenarios = config["scenarios"]
        self.assertEqual(len(scenarios), 3)

        target_scenario = scenarios["TestSuite 1-index"]
        found_name, found_scenario = obj.find_soapui_test_case(None, scenarios)
        self.assertEqual(target_scenario, found_scenario)

        self.assertIn("No `test-case` specified for SoapUI project, will use 'index'",
                      log_recorder.warn_buff.getvalue())

    def test_skip_if_no_requests(self):
        log_recorder = RecordingHandler()
        obj = SoapUIScriptConverter(logging.getLogger(''))
        obj.log.addHandler(log_recorder)

        obj.convert_script(__dir__() + "/../soapui/amazon-sample.xml")
        self.assertIn("No requests extracted for scenario TestSuite 1-TestCase 1, skipping it",
                      log_recorder.warn_buff.getvalue())

    def test_rest_service_name_as_base_address(self):
        obj = SoapUIScriptConverter(logging.getLogger(''))
        config = obj.convert_script(__dir__() + "/../soapui/youtube-sample.xml")
        scenarios = config["scenarios"]
        scenario = scenarios["TestSuite-TestCase"]
        self.assertEqual(len(scenario["requests"]), 5)
        for request in scenario["requests"]:
            self.assertTrue(request["url"].startswith("http://gdata.youtube.com/"))