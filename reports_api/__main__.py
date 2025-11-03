#!/usr/bin/env python3
import logging

import connexion
import waitress as waitress

from reports_api.common.globals import Globals, GlobalsSingleton
from reports_api.openapi_server import encoder
rest_port_str = 8080

#Globals.config_file = "test_config.yml"


def main():
    GlobalsSingleton.get()
    logging.getLogger('sqlalchemy.engine.Engine').setLevel(logging.WARNING)
    app = connexion.App(__name__, specification_dir='openapi_server/openapi/')
    app.app.json_encoder = encoder.JSONEncoder
    app.add_api('openapi.yaml', arguments={'title': 'Reports API with PostgreSQL'}, pythonic_params=True)
    app.debug = True
    waitress.serve(app, port=int(rest_port_str), threads=8)


if __name__ == '__main__':
    main()
