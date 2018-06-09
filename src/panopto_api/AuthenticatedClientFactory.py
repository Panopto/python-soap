from zeep import Client
from ClientWrapper import ClientWrapper
import urllib3


class AuthenticatedClientFactory(object):
    '''
    A class encapsulating the Panopto authentication protocol, using username/password specified at construction.
    Use the class to get clients for supported endpoints and authenticate them with the stored credentials.
    '''
    def __init__(self, host, username, password, verify_ssl=True):
        self.host = host
        self.username = username
        self.password = password
        self.verify_ssl = verify_ssl
        if not verify_ssl:
            # urllib provides warnings which look like errors when making unsecured calls to https endpoints.
            # when a user creates an unverified factory, the expectation is that they won't be incessantly warned
            # about the dangers of making calls therefrom. disable those warnings.
            urllib3.disable_warnings()
        self.cookie = None

    def _decorate_endpoint(self, endpoint_path, over_ssl=False):
        return 'http{}://{}/{}'.format(
            's' if over_ssl else '',
            self.host,
            endpoint_path)

    @staticmethod
    def get_endpoint(service=None):
        '''
        Obtain the fully-qualified endpoint for the specified service.
        If no service is specified, obtain a list of the supported services.
        '''
        endpoints = {
            'AccessManagement': '4.0',
            'Auth': '4.2',
            'RemoteRecorderManagement': '4.2',
            'SessionManagement': '4.6',
            'UsageReporting': '4.0',
            'UserManagement': '4.0'
        }
        if service and service in endpoints:
            return 'Panopto/PublicAPI/{}/{}.svc'.format(endpoints[service], service)
        else:
            return sorted(endpoints.keys())

    def get_client(self, endpoint, over_ssl=False, authenticate_now=True, as_wrapper=True):
        '''
        Create a client to the specified endpoint with options:
            over_ssl: hit the endpoint over ssl
            authenticate_now: authenticate the client with the factory's cookie
        '''
        transport = None
        if not self.verify_ssl:
            from requests import Session
            from zeep.transports import Transport
            session = Session()
            session.verify = False
            transport = Transport(session=session)
        if endpoint in AuthenticatedClientFactory.get_endpoint():
            endpoint = AuthenticatedClientFactory.get_endpoint(endpoint)
        client = Client(
            wsdl=self._decorate_endpoint(endpoint, over_ssl)+'?singleWsdl',
            transport=transport)
        if authenticate_now:
            self.authenticate_client(client)
        if as_wrapper:
            client = ClientWrapper(client)
        return client

    def authenticate_factory(self):
        '''
        Authenticate the factory by renewing the cookie with stored credentials.
        '''
        # need to hit auth endpoint over ssl to get cookie
        # but we might not be authenticated yet so explicitly don't authenticate the auth client!
        auth_endpoint = AuthenticatedClientFactory.get_endpoint('Auth')  # Panopto/PublicAPI/4.2/Auth.svc'
        auth_client = self.get_client(auth_endpoint, authenticate_now=False, as_wrapper=False)
        auth_service = auth_client.create_service(
            binding_name='{http://tempuri.org/}BasicHttpBinding_IAuth',
            address=self._decorate_endpoint(auth_endpoint, over_ssl=True))

        # need to pick apart raw response to get the cookie
        with auth_client.options(raw_response=True):
            response = auth_service.LogOnWithPassword(
                userKey=self.username,
                password=self.password)
            if response.status_code == 200:
                self.cookie = response.headers['Set-Cookie']
                return True

        return False

    def authenticate_client(self, client):
        '''
        Authenticate the client with the factory's cookie.
        If the factory doesn't have a cookie, authenticate the factory to get one.
        '''
        if self.cookie is None:
            if not self.authenticate_factory():
                return False
        client.transport.session.headers.update({'Cookie': self.cookie})
        return True
