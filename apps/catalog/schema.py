"""OpenAPI extras for the optional Identity bearer check."""

from drf_spectacular.extensions import OpenApiAuthenticationExtension


class OptionalIdentityAuthenticationScheme(OpenApiAuthenticationExtension):
    target_class = 'apps.catalog.auth.OptionalIdentityAuthentication'
    name = 'identityBearer'

    def get_security_definition(self, auto_schema):
        return {
            'type': 'http',
            'scheme': 'bearer',
            'bearerFormat': 'JWT',
            'description': 'Optional Identity access token. Omit it for an anonymous install ping.',
        }
