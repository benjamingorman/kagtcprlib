import unittest

from .context import kagtcprlib

class TestClient(unittest.TestCase):

    def setUp(self):
        self.client = kagtcprlib.Client()
        self.example_req = "<request><id>1</id><method>ping</method><params><foo>bar</foo></params></request>"

    def test_parse_request(self):    
        req = self.client._parse_request("00:00:00", self.example_req)
        self.assertEqual(req.timestamp, "00:00:00")
        self.assertEqual(req.reqID, "1")
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

def ping_handler(req):
    return "pong"

if __name__ == '__main__':
    unittest.main()
