from typing import Any, Dict


def init_logging(
    conf_filename: str, load_common_config: bool = True, stdout_formatter: str = "verbose", **kwargs: Any
) -> None:
    """
    Read logging configuration from file and configure loggers.

    :param conf_filename: config filename, should be located in `conf` directory
    :param load_common_config: if True, load common_logging.yml and merge config from `conf_filename`
    :param stdout_formatter: should be one of the formatters defined inside config
    :param kwargs: any additional params, they are transformed to upper-case and used to replace $VARIABLEs in
        logging config
    :return:
    """

    def read_logging_config(conf_filename: str, **kwargs: Any) -> Dict[str, Any]:
        file_path: str = realpath(join(__file__, "../../conf/%s" % (conf_filename,)))
        yaml_parser: YAML = YAML()
        with open(file_path) as fd:
            yml_source: str = fd.read()
            yml_source = yml_source.replace("$PROJECT_DIR", realpath(join(__file__, "../../")))
            for key, value in kwargs.items():
                yml_source = yml_source.replace(f"${key.upper()}", value)
            io_stream: io.StringIO = io.StringIO(yml_source)
            config: Dict = yaml_parser.load(io_stream)
        return config

    import io
    import logging.config
    from os.path import join, realpath

    from ruamel.yaml import YAML

    logging_config = {}
    kwargs["stdout_formatter"] = stdout_formatter

    if load_common_config:
        logging_config = read_logging_config("common_logging.yml", **kwargs)

    logging_config.update(read_logging_config(conf_filename, **kwargs))
    logging.config.dictConfig(logging_config)
