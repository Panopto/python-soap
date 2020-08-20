import re


class ClientWrapper(object):
    '''
    A class wrapping the zeep SOAP infrastructure to make it more pythonic.
    zeep uses proxies to optimisitically invoke services, ports, and operations,
    which may or may not exist in the wsdl.
    This wrapper class inspects the wsdl to provide the available services, ports, and operations
    in a pythonic way to make programatic discovery of the same easy.
    wsdl-specified namespaces and types are also exposed for convenience. In many cases, zeep can
    cons up those types from pythonic objects, but not always.
    '''

    @staticmethod
    def _parse_operation_signature(op_sig):
        '''
        Some operations return nothing, so their output signature is the empty string. Map that to None.
        Otherwise, rip apart the signature into names and types.
        '''
        return {t[0]: t[1] for t in [s.split(': ') for s in op_sig.split(', ')]} if op_sig else None

    @staticmethod
    def _parse_element_signature(el_sig):
        '''
        sample simple element: ns1:string(xsd:string)
        sample complex element: ns0:GetUserDetailedUsage(
                auth: ns2:AuthenticationInfo, userId: ns1:guid, pagination: ns2:Pagination)
        '''
        element_pattern = '^(?P<namespace>[^:]+):(?P<name>[^\(]+)\((?P<memberlist>[^\)]+)\)$'
        match = re.match(element_pattern, el_sig)
        if match:
            memberlist = []
            # sample named type: folderId: ns1:guid
            # sample unnamed type: xsd:unsignedByte
            for member_components in [m.split(':') for m in match.group('memberlist').split(', ')]:
                # anytype is special case, it is basically null (or None in python)
                if len(member_components) == 1 and member_components[0] == 'None':
                    memberlist.append(None)
                else:
                    try:
                        # name field is optional (not present for unnamed simple types), so parse from the back
                        member = {
                            'namepsace': member_components[-2].strip(),
                            'type': member_components[-1]
                        }
                        if len(member_components) == 3:
                            member['name'] = member_components[0]
                        memberlist.append(member)
                    except Exception:
                        raise Exception(member_components)

            return {
                'namespace': match.group('namespace'),
                'name': match.group('name'),
                'members': memberlist
            }

    @staticmethod
    def _parse_type_signature(t_sig):
        # some types basically look just like elements, so try that parsing first
        # otherwise all types are just ns:name
        el_sig = ClientWrapper._parse_element_signature(t_sig)
        if el_sig:
            return el_sig
        else:
            ns, name = t_sig.split(':')
            return {'namespace': ns, 'name': name}

    @staticmethod
    def _unpack_response(response):
        if hasattr(response, '__dict__'):
            ret = {}
            ordict = response.__dict__['__values__']
            for k, v in ordict.items():
                ret[k] = ClientWrapper._unpack_response(v)
            return ret
        elif type(response) is list:
            return [ClientWrapper._unpack_response(l) for l in response]
        else:
            return response

    def __init__(self, client):
        self.client = client
        if client:
            self._unpack_types()
            self._unpack_services()
            self._service = self.bind()

    def _unpack_services(self):
        self.services = {}
        for service_name, service in self.client.wsdl.services.items():
            srv = {}
            self.services[service_name] = srv
            for port_name, port in service.ports.items():
                prt = {}
                srv[port_name] = prt
                for operation_name, operation in port.binding._operations.items():
                    try:
                        prt[operation_name] = {
                            io: ClientWrapper._parse_operation_signature(getattr(operation, io).signature())
                            for io in ('input', 'output')
                        }
                    except Exception:
                        raise Exception(operation_name)

    def _unpack_types(self):
        wsdl = self.client.wsdl
        self.namespaces = wsdl.types.prefix_map
        self.elements = {
            '{}:{}'.format(sig['namespace'], sig['name']): sig for sig in
            [ClientWrapper._parse_element_signature(el.signature(schema=wsdl.types))
             for el in wsdl.types.elements] if sig
        }
        self.types = {
            '{}:{}'.format(sig['namespace'], sig['name']): sig for sig in
            [ClientWrapper._parse_type_signature(t.signature(schema=wsdl.types))
             for t in wsdl.types.types] if sig
        }

    def bind(self, service_name=None, port_name=None):
        '''
        Set the active service of this ClientWrapper to the specified service and port names.
        If either is unspecified, the default is used. In most cases, that's desired.
        '''
        service_name = service_name or list(self.services.keys())[0]
        port_name = port_name or list(self.services[service_name].keys())[0]
        self._service = self.client.bind(service_name, port_name)
        self.bound_service_name = service_name
        self.bound_port_name = port_name
        return self._service

    def bound_operation(self, operation_name=None):
        '''
        Return the signature details of the specified operation within the currently bound service and port.
        If unspecified or if the operation_name doesn't exist, return the supported operation names.
        '''
        operations = self.services[self.bound_service_name][self.bound_port_name]
        return operations.get(operation_name, sorted(operations.keys()))

    def call_service(self, operation_name, **kwargs):
        '''
        Invoke an operation against the currently bound service and port.
        Automatically unpack the response into a pythonic object.
        '''
        response = self._service[operation_name](**kwargs)
        if response:
            return ClientWrapper._unpack_response(response)

    def call_service_raw(self, operation_name, **kwargs):
        '''
        Invoke an operation against the currently bound service and port.
        Return the response without any unpacking. Good for reading the raw response.
        '''
        with self.client.settings(raw_response=True):
            return self._service[operation_name](**kwargs)
