"""
This module provides a class encapsulating the Panopto authentication protocol
"""
# Standard Library
from typing import List, Optional, Union
import logging
import xml.etree.ElementTree as ET

# Third Party
from zeep import Client

# Local
from panopto_api.ClientWrapper import ClientWrapper


LOG = logging.getLogger(__name__)


class UnexpectedAuthenticationResponseException(Exception):
    """
    Exception raised when an unexpected response is encountered during authentication
    """
    pass


class AuthenticatedClientFactory(object):
    """
    A class encapsulating the Panopto authentication protocol, using username/password specified at construction.
    Use the class to get clients for supported endpoints and authenticate them with the stored credentials.
    """
    ENDPOINTS = {
        'AccessManagement': '4.0',
        'Auth': '4.2',
        'RemoteRecorderManagement': '4.2',
        'SessionManagement': '4.6',
        'UsageReporting': '4.0',
        'UserManagement': '4.0'
    }

    def __init__(self, host: str, username: str, password: str):
        self.host = host
        self.username = username
        self.password = password
        self.cookie = None

    def _decorate_endpoint(self, endpoint_path: str, over_ssl: bool = False) -> str:
        return 'http{}://{}/{}'.format('s' if over_ssl else '', self.host, endpoint_path)

    @staticmethod
    def get_endpoint(service: Optional[str] = None) -> Union[str, List[str]]:
        """
        Obtain the fully-qualified endpoint for the specified service.
        If no service is specified, obtain a list of the supported services.
        """
        if service and service in AuthenticatedClientFactory.ENDPOINTS:
            return 'Panopto/PublicAPI/{}/{}.svc'.format(AuthenticatedClientFactory.ENDPOINTS[service], service)
        else:
            return sorted(AuthenticatedClientFactory.ENDPOINTS.keys())

    def get_client(self, endpoint: str, over_ssl: bool = False, authenticate_now: bool = True, as_wrapper: bool = True) \
            -> Union[Client, ClientWrapper]:
        """
        Create a client to the specified endpoint with options:
            over_ssl: hit the endpoint over ssl
            authenticate_now: authenticate the client with the factory's cookie
        """
        transport = None
        if endpoint in AuthenticatedClientFactory.get_endpoint():
            endpoint = AuthenticatedClientFactory.get_endpoint(endpoint)
        client = Client(wsdl=self._decorate_endpoint(endpoint, over_ssl)+'?singleWsdl', transport=transport)
        if authenticate_now:
            self.authenticate_client(client)
        if as_wrapper:
            client = ClientWrapper(client)
        return client

    def parse_log_on_with_password_response(self, xml_str: str):
        """
        Parse the response from the LogOnWithPassword operation.
        """
        xml_ns = {
            'soap': 'http://schemas.xmlsoap.org/soap/envelope/',
            'ns': 'http://tempuri.org/'
        }
        root = ET.fromstring(xml_str)
        for entry in root.findall('soap:Body/ns:LogOnWithPasswordResponse', xml_ns):
            return bool(entry.find('ns:LogOnWithPasswordResult', xml_ns).text.lower() == 'true')
        raise UnexpectedAuthenticationResponseException('Unexpected response from LogOnWithPassword: {}'.format(xml_str))

    def authenticate_factory(self) -> bool:
        """
        Authenticate the factory by renewing the cookie with stored credentials.
        """
        # Need to hit auth endpoint over ssl to get cookie,
        # but we might not be authenticated yet so explicitly don't authenticate the auth client!
        auth_endpoint = AuthenticatedClientFactory.get_endpoint('Auth')  # Panopto/PublicAPI/4.2/Auth.svc
        auth_client = self.get_client(auth_endpoint, authenticate_now=False, as_wrapper=False)
        auth_service = auth_client.create_service(
            binding_name='{http://tempuri.org/}BasicHttpBinding_IAuth',
            address=self._decorate_endpoint(auth_endpoint, over_ssl=True)
        )

        # need to pick apart raw response to get the cookie
        with auth_client.settings(raw_response=True):
            response = auth_service.LogOnWithPassword(userKey=self.username, password=self.password)
            if response.status_code == 200:
                xml_str = response.content.decode('utf-8')
                logon_response = self.parse_log_on_with_password_response(xml_str)
                if logon_response:
                    self.cookie = response.headers['Set-Cookie']
                    return True

        return False

    def authenticate_client(self, client: Client) -> bool:
        """
        Authenticate the client with the factory's cookie.
        If the factory doesn't have a cookie, authenticate the factory to get one.
        """
        if self.cookie is None:
            if not self.authenticate_factory():
                return False
        client.transport.session.headers.update({'Cookie': self.cookie})
        return True
