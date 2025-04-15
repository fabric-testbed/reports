from analytics_api.response_code import authorization_controller as rc
"""
controller generated to handled auth operation described at:
https://connexion.readthedocs.io/en/latest/security.html
"""
def check_bearerAuth(token):
    return rc.check_bearerAuth(token)


