from panopto_api.AuthenticatedClientFactory import AuthenticatedClientFactory
import unittest


class TestSoapApi(unittest.TestCase):
    """
    Tests the SoapApi
    """
    @classmethod
    def setup_class(cls):
        """
        Initialize the test via pytest
        """

    def test_create_auth_client_factory(self):
        """
        Tests creating an auth client
        """
        # Arrange
        host = 'localhost'
        username = 'admin'
        password = 'password'

        # Act
        auth = AuthenticatedClientFactory(host, username, password)

        # Assert
        self.assertIsNotNone(auth)

    def test_endpoint_iteration(self):
        """
        Tests creating an auth client
        """
        # Arrange
        host = 'localhost'
        username = 'admin'
        password = 'password'
        auth = AuthenticatedClientFactory(host, username, password)
        responses = []

        # Act
        for endpoint in AuthenticatedClientFactory.ENDPOINTS:
            responses.append(auth.get_endpoint(endpoint))

        # Assert
        self.assertEqual(len(responses), len(AuthenticatedClientFactory.ENDPOINTS))
