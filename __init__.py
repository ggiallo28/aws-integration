from cat.mad_hatter.mad_hatter import MadHatter
from cat.mad_hatter.decorators import tool, hook, plugin
from cat.log import log

AWS_PLUGIN_PREFIX = "aws_integration"


class BaseFactory:
    """Base class for all factories to ensure consistent interfaces."""

    def __init__(self, settings=None):
        self._settings = settings

    def get_client(self, service_name, settings=None):
        raise NotImplementedError("Subclasses must implement this method.")

    def get_resource(self, service_name, settings=None):
        raise NotImplementedError("Subclasses must implement this method.")


class AWSFactory(BaseFactory):
    """Specific factory capable of creating AWS clients and resources based on aws_model."""

    def __init__(self, settings, aws_model):
        super().__init__(settings)
        self._aws_model = aws_model

    def get_client(self, service_name, settings=None):
        return self._aws_model.get_aws_client(settings or self._settings, service_name)

    def get_resource(self, service_name, settings=None):
        return self._aws_model.get_aws_resource(
            settings or self._settings, service_name
        )


class EmptyFactory(BaseFactory):
    """Fallback factory that does nothing but log calls to show missing configurations."""

    def get_client(self, service_name, settings=None):
        log.info("No operation available. Ensure plugin is configured correctly.")
        return None

    def get_resource(self, service_name, settings=None):
        log.info("No operation available. Ensure plugin is configured correctly.")
        return None


def factory():
    """Create an AWS client factory from the aws_integration plugin settings."""
    mad_hatter = MadHatter()
    for name in mad_hatter.active_plugins:
        if name.startswith(AWS_PLUGIN_PREFIX):
            aws_plugin = mad_hatter.plugins.get(name)
            if aws_plugin:
                try:
                    plugin_settings = aws_plugin.load_settings()
                    aws_model = aws_plugin.settings_model()
                    if plugin_settings and aws_model:
                        return AWSFactory(plugin_settings, aws_model)
                except Exception as e:
                    log.info(f"An error occurred while creating the AWS Factory: {e}")
                break
    log.info("No AWS integration plugin found or failed to initialize.")
    return EmptyFactory()


class Boto3:
    """Wrapper class that uses a factory to get AWS clients and resources based on plugin configuration."""

    def __init__(self, settings=None):
        self.factory_instance = factory()
        self.settings = settings

    def get_client(self, service_name, settings=None):
        return self.factory_instance.get_client(service_name, settings or self.settings)

    def get_resource(self, service_name, settings=None):
        return self.factory_instance.get_resource(
            service_name, settings or self.settings
        )


__all__ = ["Boto3"]
