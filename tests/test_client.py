import unittest

from .context import kagtcprlib

class TestClient(unittest.TestCase):

    def setUp(self):
        self.client = kagtcprlib.Client()
        self.example_req = "<request><id>1</id><method>ping</method><params><foo>bar</foo></params></request>"

    def tearDown(self):
        # Else we get duplicate log messages since the new client adds extra handlers
        self.client.log.handlers = []

    def test_parse_request(self):    
        req = self.client._parse_request("00:00:00", self.example_req)
        self.assertEqual(req.client_name, self.client.name)
        self.assertEqual(req.timestamp, "00:00:00")
        self.assertEqual(req.req_id, "1")
        self.assertEqual(req.method, "ping")
        self.assertEqual(req.params["foo"], "bar")

    def test_handle_line(self):
        res = self.client._handle_line("blah")
        self.assertEqual(res, None)

        res = self.client._handle_line("[00:00:00] hello")
        self.assertEqual(res, None)

        res = self.client._handle_line("[00:00:00] <request></request>")
        self.assertEqual(res, None)

        # Should be None until we add a handler
        res = self.client._handle_line("[00:00:00] {}".format(self.example_req))
        self.assertEqual(res, "getRules().set_string('TCPR_RES1', ''); getRules().set_u8('TCPR_REQ1', 3);\n")

        self.client.add_handler("ping", ping_handler)
        res = self.client._handle_line("[00:00:00] {}".format(self.example_req))
        self.assertEqual(res, "getRules().set_string('TCPR_RES1', 'pong'); getRules().set_u8('TCPR_REQ1', 2);\n")

    def test_multiline(self):
        self.client.add_handler("ping", ping_handler)

        self.assertFalse(self.client._in_multiline)
        self.assertEqual(self.client._multiline_timestamp, None)
        self.assertEqual(len(self.client._multiline_content), 0)

        res = self.client._handle_line("[00:00:00] <multiline>")
        self.assertEqual(res, None)
        self.assertTrue(self.client._in_multiline)
        self.assertEqual(self.client._multiline_timestamp, "00:00:00")
        self.assertEqual(len(self.client._multiline_content), 0)

        self.client._handle_line("[00:00:00] {}".format(self.example_req[:10]))
        self.client._handle_line("[00:00:00] {}".format(self.example_req[10:]))
        res = self.client._handle_line("[00:00:00] </multiline>")

        self.assertEqual(self.client._in_multiline, False)
        self.assertEqual(res, "getRules().set_string('TCPR_RES1', 'pong'); getRules().set_u8('TCPR_REQ1', 2);\n")

def ping_handler(req):
    return "pong"

if __name__ == '__main__':
    unittest.main()
