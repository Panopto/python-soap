from panopto_api.AuthenticatedClientFactory import AuthenticatedClientFactory
import unittest


class TestSoapApi(unittest.TestCase):
    """
    Tests the SoapApi
    """
    @classmethod
    def setup_class(self):
        """
        Initialize the test via pytest
        """

    def test_create_auth_client_factory(self):
        """
        Tests creating an auth client
        """
        host = 'localhost'
        username = 'admin'
        password = 'password'
        auth = AuthenticatedClientFactory(
                host, username, password, verify_ssl=host != 'localhost')
        self.assertIsNotNone(auth)
