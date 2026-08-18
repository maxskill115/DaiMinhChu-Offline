import os
import tempfile
import threading
import unittest
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

_TEST_DIR = tempfile.TemporaryDirectory()
os.environ["DMC_SAVE_FILE"] = str(Path(_TEST_DIR.name) / "transport-save.json")

from app import (  # noqa: E402
    DMCHandler,
    STORE,
    _chat_get_response,
    _create_lien_minh_response,
    _lay_nhan_vat_response,
    _unsupported_static_response,
)
from crypto import decrypt_text  # noqa: E402


class RuntimeTransportRegressionTests(unittest.TestCase):
    def setUp(self) -> None:
        STORE.reset()
        STORE.choose_hero("NV_LenhHoXung")

    def test_lowercase_error_code_zero_is_success_for_recruit(self) -> None:
        response = _lay_nhan_vat_response({"Aid": 1})
        self.assertEqual(response["errorCode"], 0)
        self.assertTrue(response["errorMsg"].startswith("NV_"))

    def test_lowercase_read_success_and_controlled_failure(self) -> None:
        self.assertEqual(_chat_get_response({})["errorCode"], 0)
        self.assertNotEqual(_create_lien_minh_response({})["errorCode"], 0)

    def test_generic_static_fallback_fails_both_error_conventions(self) -> None:
        response = _unsupported_static_response({})
        self.assertEqual(response["ErrorCode"], 0)
        self.assertNotEqual(response["errorCode"], 0)

    def test_chat_get_legacy_http_get_returns_encrypted_success(self) -> None:
        server = ThreadingHTTPServer(("127.0.0.1", 0), DMCHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            url = f"http://127.0.0.1:{server.server_port}/Server/Webservice/User.asmx/ChatGet"
            with urllib.request.urlopen(url, timeout=3) as response:
                self.assertEqual(response.status, 200)
                plaintext = decrypt_text(response.read().decode("utf-8"))
            self.assertIn('"errorCode":0', plaintext)
            self.assertIn('"chatQuery":[]', plaintext)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
