from os import environ

CLIENT_ID = environ.get("CLIENT_ID")
CLIENT_SECRET = environ.get("CLIENT_SECRET")
FB_CLIENT_ID = environ.get("FB_CLIENT_ID")
FB_CLIENT_SECRET = environ.get("FB_CLIENT_SECRET")


# class Config:
#     """ Flask configuration variables """

# The secret key is used by Flask to encrypt session cookies.
SECRET_KEY = environ.get('SECRET_KEY')
# FLASK_APP = environ.get('FLASK_APP')
# FLASK_ENV = environ.get('FLASK_ENV')
PROJECT_ID = environ.get('PROJECT_ID')
CLOUDSQL_USER = environ.get('DB_USER')
CLOUDSQL_PASSWORD = environ.get('DB_PASSWORD')
CLOUDSQL_DATABASE = environ.get('DB_NAME')
# Set the following value to the Cloud SQL connection name, e.g.
#   "project:region:cloudsql-instance".
# You must also update the value in app.yaml.
CLOUDSQL_CONNECTION_NAME = environ.get('DB_CONNECTION_NAME')

# The CloudSQL proxy is used locally to connect to the cloudsql instance.
# To start the proxy, use:
#   $ cloud_sql_proxy -instances=your-connection-name=tcp:3306
# Port 3306 is the standard MySQL port, but change it if needed.

# Alternatively, you could use a local MySQL instance for testing.
LOCAL_SQLALCHEMY_DATABASE_URI = (
    'mysql+pymysql://{user}:{password}@127.0.0.1:3306/{database}').format(
        user=CLOUDSQL_USER, password=CLOUDSQL_PASSWORD,
        database=CLOUDSQL_DATABASE)

# When running on App Engine a unix socket is used to connect to the cloudsql instance.
LIVE_SQLALCHEMY_DATABASE_URI = (
    'mysql+pymysql://{user}:{password}@localhost/{database}'
    '?unix_socket=/cloudsql/{connection_name}').format(
        user=CLOUDSQL_USER, password=CLOUDSQL_PASSWORD,
        database=CLOUDSQL_DATABASE, connection_name=CLOUDSQL_CONNECTION_NAME)

if environ.get('GAE_INSTANCE'):
    SQLALCHEMY_DATABASE_URI = LIVE_SQLALCHEMY_DATABASE_URI
else:
    SQLALCHEMY_DATABASE_URI = LOCAL_SQLALCHEMY_DATABASE_URI
