from os import environ

# class Config:
#     """ Flask configuration variables """
SECRET_KEY = environ.get('SECRET_KEY')  # for session cookies & flash messages
# FLASK_APP = environ.get('FLASK_APP')
# FLASK_ENV = environ.get('FLASK_ENV')
FB_CLIENT_ID = environ.get("FB_CLIENT_ID")
FB_CLIENT_SECRET = environ.get("FB_CLIENT_SECRET")
DEV_RUN = True if environ.get('DEV_RUN') == 'True' else False
PROJECT_NAME = environ.get('PROJECT_NAME')
PROJECT_ID = environ.get('PROJECT_ID')
PROJECT_NUMBER = environ.get('PROJECT_NUMBER')
PROJECT_REGION = environ.get('PROJECT_REGION')
CLOUDSQL_INSTANCE = environ.get('DB_INSTANCE')
CLOUDSQL_USER = environ.get('DB_USER')
CLOUDSQL_PASSWORD = environ.get('DB_PASSWORD')
CLOUDSQL_DATABASE = environ.get('DB_NAME')
DEPLOYED_URL = environ.get('DEPLOYED_URL')
# Set the following value to the Cloud SQL connection name, e.g.
#   "project:region:cloudsql-instance".
# You must also update the value in app.yaml.
# CLOUDSQL_CONNECTION_NAME = f'{PROJECT_ID}:{PROJECT_REGION}:{CLOUDSQL_INSTANCE}'
CLOUDSQL_CONNECTION_NAME = environ.get('DB_CONNECTION_NAME')
if DEV_RUN:
    PROJECT_NAME = environ.get('DEV_PROJECT_NAME', PROJECT_NAME)
    PROJECT_ID = environ.get('DEV_PROJECT_ID', PROJECT_ID)
    PROJECT_NUMBER = environ.get('DEV_PROJECT_NUMBER', PROJECT_NUMBER)
    PROJECT_REGION = environ.get('DEV_PROJECT_REGION', PROJECT_REGION)
    CLOUDSQL_INSTANCE = environ.get('DEV_DB_INSTANCE', CLOUDSQL_INSTANCE)
    CLOUDSQL_USER = environ.get('DEV_DB_USER', CLOUDSQL_USER)
    CLOUDSQL_PASSWORD = environ.get('DEV_DB_PASSWORD', CLOUDSQL_PASSWORD)
    CLOUDSQL_DATABASE = environ.get('DEV_DB_NAME', CLOUDSQL_DATABASE)
    DEPLOYED_URL = environ.get('DEV_URL', DEPLOYED_URL)
    CLOUDSQL_CONNECTION_NAME = environ.get('DB_CONNECTION_NAME', CLOUDSQL_CONNECTION_NAME)
# The CloudSQL proxy is used locally to connect to the cloudsql instance.
# To start the proxy, use:
#   $ cloud_sql_proxy -instances=your-connection-name=tcp:3306
# Port 3306 is the standard MySQL port, but change it if needed.
# Alternatively, you could use a local MySQL instance for testing.
LOCAL_SQLALCHEMY_DATABASE_URI = (
    'mysql+pymysql://{user}:{password}@127.0.0.1:3306/{database}?charset=utf8mb4').format(
        user=CLOUDSQL_USER, password=CLOUDSQL_PASSWORD,
        database=CLOUDSQL_DATABASE)
# When running on App Engine a unix socket is used to connect to the cloudsql instance.
LIVE_SQLALCHEMY_DATABASE_URI = (
    'mysql+pymysql://{user}:{password}@localhost/{database}'
    '?unix_socket=/cloudsql/{connection_name}&charset=utf8mb4').format(
        user=CLOUDSQL_USER, password=CLOUDSQL_PASSWORD,
        database=CLOUDSQL_DATABASE, connection_name=CLOUDSQL_CONNECTION_NAME)
LOCAL_URL = 'http://127.0.0.1:8080'
if environ.get('GAE_INSTANCE'):
    SQLALCHEMY_DATABASE_URI = LIVE_SQLALCHEMY_DATABASE_URI
    URL = DEPLOYED_URL
    LOCAL_ENV = False
else:
    SQLALCHEMY_DATABASE_URI = LOCAL_SQLALCHEMY_DATABASE_URI
    environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    URL = LOCAL_URL
    LOCAL_ENV = True
