from cat.mad_hatter.mad_hatter import MadHatter
from cat.log import log

AWS_PLUGIN_PREFIX = "aws_integration"

class EmptyFactory(settings=None):
    pass

def factory():
    """Create an AWS client using settings from the plugin."""
    mad_hatter = MadHatter()
    
    aws_plugin = None
    for name in mad_hatter.active_plugins:
        if name.startswith(AWS_PLUGIN_PREFIX):
            aws_plugin = mad_hatter.plugins.get(name)
    
    if aws_plugin:
        try:
            plugin_settings = aws_plugin.load_settings()
            if not plugin_settings:
                log.info("Failed to load settings from the plugin.")
                return EmptyFactory
                
            aws_model = aws_plugin.settings_model()
            if not aws_model:
                log.info("No settings model available in the plugin.")
                return EmptyFactory
            
            class Factory():
                def __init__(self, settings=None):
                    self._settings = settings or plugin_settings
                    self._aws_model = aws_model
                    
                def _get_model(self):
                    return self._aws_model
                
                def _get_settings(self):
                    return self._settings
                
                def get_client(self, service_name, settings=None):
                    return self._aws_model.get_aws_client(
                        settings or self._settings, 
                        service_name
                    )
                
                def get_resource(self, service_name, settings=None):
                    return self._aws_model.get_aws_resource(
                        settings or self._settings, 
                        service_name
                    )
            
            return Factory
        except Exception as e:
            log.info("An error occurred while creating the AWS Factory: %s", e)
    else:
        log.info("No AWS integration plugin found.")
    return EmptyFactory

class Boto3(factory()):
    def __init__(self, settings=None):
        super().__init__(settings)