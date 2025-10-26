import logging, logging.config
from pathlib import Path
import configparser

logging_config_file = Path(__file__).with_name("logging-config.ini")


def configure_logging(level='INFO', json_logging=False, loggers_to_reset=[]):
    """Configure global logging for the application
    Args:
        level: The level to set the root logger to
        json_logging: Whether to use json logging
        loggers_to_reset:
            A list of logger names to reset after configuring the logging framework. 
            Ensure you import the modules prior to calling this function, otherwise they may be re-reset when the modules are imported.
    """

    # Don't attempt to use the yaml forms of the logging config file, the yaml parsers reconfigure the logging framework and break it
    logging_config = configparser.ConfigParser()
    logging_config.read(logging_config_file)
    logging_config['logger_root']['level'] = level

    if json_logging: 
        for section in logging_config.sections():
            if section.startswith('logger_'):
                logging_config[section]['handlers'] = 'console_json'
    
    logging.config.fileConfig(logging_config)

    root_logger = logging.getLogger()
    root_logger_handlers = [handler for handler in root_logger.handlers]

    # Reset uvicorn's logger after we configure the framework because they force it to be non-json
    try:
        import uvicorn.config

        #TODO: uvicorn.config.LOGGING_CONFIG is overriding this during app startup, but we need to move on for now.
        for logger in [uvicorn.config.logger, logging.getLogger("uvicorn.error"), logging.getLogger("uvicorn.access")]:
            for handler in logger.handlers:
                logger.removeHandler(handler)
            for handler in root_logger_handlers:
                logger.addHandler(handler)
            logger.propagate = False
    except ImportError:
        pass

    for logger_name in loggers_to_reset:
        logger = logging.getLogger(logger_name)
        logger.handlers = root_logger.handlers
        logger.propagate = False
        logger.setLevel(root_logger.level)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)