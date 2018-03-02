import unittest

from .context import kagtcprlib
import kagtcprlib.client
import kagtcprlib.handlers as handlers
import kagtcprlib.opt.kagladder as kagladder

def ping_method_handler(req):
    return "pong"

class TestXMLRequestHandler(unittest.TestCase):
    def setUp(self):
        self.client = kagtcprlib.client.Client()
        self.handler = kagladder.XMLRequestHandler()

    def test_request_from_xml(self):
        xml = "<request><method>ping</method><id>1</id><params><foo>bar</foo></params></request>"
        req = kagladder.Request.from_xml("test", "[12:34:56]", xml)
        self.assertIsNotNone(req)
        self.assertEqual(req.method, "ping")
        self.assertEqual(req.req_id, "1")
        self.assertDictEqual(req.params, {"foo": "bar"})

    def test_format_angelscript_response(self):
        expected = "getRules().set_string('TCPR_RES1', 'pong'); getRules().set_u8('TCPR_REQ1', 2);\n"
        actual = self.handler._format_angelscript_response(1, 'pong', 2)
        self.assertEqual(expected, actual)

    def test_handle_line(self):
        example_line = "<request><method>ping</method><id>1</id><params></params></request>"
        self.handler.add_method_handler("ping", ping_method_handler)

        msg = self.handler._handle_line("[00:00:00]", example_line)

        self.assertEqual(msg, self.handler._format_angelscript_response(1, 'pong', 2))

    def test_multiline_handle(self):
        lines = ["<multiline>",
                 "<request><method>ping</method><id>1</id><params></params></request>",
                 "</multiline>"
                 ]
        self.handler.add_method_handler("ping", ping_method_handler)
        x = self.handler.handle("[12:34:56]", lines[0])
        self.assertIsNone(x)
        x = self.handler.handle("[12:34:57]", lines[1])
        self.assertIsNone(x)
        msg = self.handler.handle("[12:34:57]", lines[2])
        self.assertEqual(msg, self.handler._format_angelscript_response(1, 'pong', 2))
