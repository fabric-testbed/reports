#!/usr/bin/env python3

import connexion
import waitress as waitress

from analytics_api.common.globals import Globals, GlobalsSingleton
from analytics_api.swagger_server import encoder
rest_port_str = 8080

Globals.config_file = "../config.yml"


def main():
    GlobalsSingleton.get()
    app = connexion.App(__name__, specification_dir='swagger/',
                        options={"swagger_ui": True})
    app.app.json_encoder = encoder.JSONEncoder
    app.add_api('swagger.yaml', arguments={'title': 'Analytics API with PostgreSQL'}, pythonic_params=True)
    app.debug = True
    waitress.serve(app, port=int(rest_port_str), threads=8)


if __name__ == '__main__':
    main()
