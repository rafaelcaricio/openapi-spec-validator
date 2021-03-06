"""OpenAPI spec validator decorators module."""
import logging

from openapi_spec_validator.managers import VisitingManager

log = logging.getLogger(__name__)


class DerefValidatorDecorator:
    """Dereferences instance if it is a $ref before passing it for validation.

    :param instance_resolver: Resolves refs in the openapi service spec
    """
    def __init__(self, instance_resolver):
        self.instance_resolver = instance_resolver
        self.visiting = VisitingManager()

    def __call__(self, func):
        def wrapped(validator, schema_element, instance, schema):
            if not isinstance(instance, dict) or '$ref' not in instance:
                for res in func(validator, schema_element, instance, schema):
                    yield res
                return

            ref = instance['$ref']

            # ref already visited
            if ref in self.visiting:
                return

            self._attach_scope(instance)
            with self.visiting.visit(ref):
                with self.instance_resolver.resolving(ref) as target:
                    for res in func(validator, schema_element, target, schema):
                        yield res

        return wrapped

    def _attach_scope(self, instance):
        log.debug('Attaching x-scope to %s', instance)
        if 'x-scope' in instance:
            log.debug('Ref %s already has scope attached', instance['$ref'])
            return

        instance['x-scope'] = list(self.instance_resolver._scopes_stack)
