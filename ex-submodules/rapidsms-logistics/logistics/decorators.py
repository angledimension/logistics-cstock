from django.conf import settings
from django.utils.importlib import import_module
const = import_module(settings.CONST)
roles = import_module(settings.ROLES)

def logistics_contact_required():
    """
    This decorator currently only works on an instance
    of a handler object. 
    """
    def wrapper(f):
        def require_logistics_contact(self, *args, **kwargs):
            if not hasattr(self.msg,'logistics_contact'):
                self.respond(const.Messages.REGISTRATION_REQUIRED_MESSAGE)
                # don't proceed with executing f
            else:
                return f(self, *args, **kwargs)
        return require_logistics_contact
    return wrapper

def logistics_permission_required(operation):
    """
    This decorator currently only works on an instance
    of a handler object. It also assumes that 
    logistics_contact_required has already been run.
    """
    def wrapper(f):
        def require_role(self, *args, **kwargs):
            if not roles.has_permissions_to(self.msg.logistics_contact, operation):
                self.respond(const.Messages.UNSUPPORTED_OPERATION)
            else:
                return f(self, *args, **kwargs)
        return require_role
    return wrapper

def logistics_contact_and_permission_required(operation):
    """
    This decorator currently only works on an instance
    of a handler object. 
    """
    def both(f):
        return logistics_contact_required()(logistics_permission_required(operation)(f)) # yikes
    return both
    