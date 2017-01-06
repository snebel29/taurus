import logging

from bzt.engine import ScenarioExecutor
from bzt.modules.blazemeter import CloudProvisioning
from tests import BZTestCase
from tests.mocks import EngineEmul, ModuleMock


class TestCloudProvisioningOld(BZTestCase):
    mock_get = {}
    mock_post = {}

    def test_case1(self):
        self.mock_get = {
            'https://a.blazemeter.com/api/v4/user': {'defaultProject': {'id': None}, "locations": [{'id': 'aws'}]},
            'https://a.blazemeter.com/api/v4/accounts': {"result": [{'id': 1}]},
            'https://a.blazemeter.com/api/v4/workspaces?accountId=1': {"result": [{'id': 1}]},
            'https://a.blazemeter.com/api/v4/multi-tests?workspaceId=1&name=Taurus+Cloud+Test': {"result": []},
            'https://a.blazemeter.com/api/v4/tests?workspaceId=1&name=Taurus+Cloud+Test': {"result": []},
            'https://a.blazemeter.com/api/v4/projects?workspaceId=1': {"result": []},
            'https://a.blazemeter.com/api/v4/masters/1/status': {"result": {"status": "CREATE"}},
            'https://a.blazemeter.com/api/v4/masters/1/sessions': {"result": {"sessions": []}},
        }

        self.mock_post = {
            'https://a.blazemeter.com/api/v4/projects': {"result": {"id": 1}},
            'https://a.blazemeter.com/api/v4/tests': {"result": {"id": 1}},
            'https://a.blazemeter.com/api/v4/tests/1/files': {"result": None},
            'https://a.blazemeter.com/api/v4/tests/1/start': {"result": {"id": 1}},
            'https://a.blazemeter.com/api/v4/masters/1/stop': {"result": None},
        }

        prov = CloudProvisioning()
        prov.browser_open = None
        prov.user.token = "test"
        prov.engine = EngineEmul()
        # prov.engine.config.merge({"modules": {"blazemeter": {"browser-open": False}}})
        prov.engine.config[ScenarioExecutor.EXEC] = [{
            "executor": "mock",
            "locations": {
                "aws": 1
            },
            "files": ModuleMock().get_resource_files()
        }]
        prov.user._request = self._request_mock

        prov.prepare()
        prov.startup()
        prov.check()
        prov.shutdown()
        prov.post_process()

    def _request_mock(self, url, data=None, headers=None, method=None):
        if method == 'GET' or (not method and not data):
            method = 'GET'
            resp = self.mock_get[url]
        elif method == 'POST' or (not method and data):
            method = 'POST'
            resp = self.mock_post[url]
        else:
            raise ValueError()

        if isinstance(resp, list):
            ret = resp.pop()
        else:
            ret = resp

        logging.debug("Emulated %s %s: %s", method, url, ret)
        return ret
