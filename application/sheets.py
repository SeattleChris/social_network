from flask import current_app as app
from os import path
from googleapiclient.discovery import build
from google.oauth2 import service_account
# import google.auth
from datetime import datetime as dt
from pprint import pprint

SHARED_SHEET_ID = '1LyUFeo5in3F-IbR1eMnkp-XeQXD_zvfYraxCJBUkZPs'
service_config = {
    'sheets': {
        'file': 'env/sheet_secret.json',
        'scopes': ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        }
}


def get_creds(config):
    """ Using google.oauth2.service_account to get credentials for the service account """
    app.logger.info('---------- Get Creds ----------')
    if not path.exists(config.get('file')):
        message = 'Wrong Path to Secret File'
        app.logger.error(message)
        raise FileNotFoundError(message)
    if app.config.get('LOCAL_ENV') is True:
        # Could add local testing credential method.
        message = "Won't work when running locally"
        app.logger.error(message)
        raise EnvironmentError(message)
    credentials = service_account.Credentials.from_service_account_file(config['file'])
    return credentials.with_scopes(config.get('scopes'))


def perm_add(sheet_id, add_users, service=None):
    """ Used to update permissions. Currently Only add users.
        add_users can be a list of strings, with each string an email address to give reader permissions.
        add_users can be a list of objects, each with a 'emailAddress' key, and an option 'role' key.
        add_users can be a single entity of either of the above.
        This function returns a dictionary that includes all permissions for the provided sheet, & URL for the sheet.
    """
    def callback(request_id, response, exception):
        if exception:
            # TODO: Handle error
            app.logger.info(exception)
        else:
            app.logger.info(f"Permission Id: {response.get('id')} Request Id: {request_id}")

    if not service:
        creds = get_creds(service_config['sheets'])
        service = build('drive', 'v3', credentials=creds, cache_discovery=False)
    batch = service.new_batch_http_request(callback=callback)
    if not isinstance(add_users, list):
        add_users = [add_users]
    for user in add_users:
        if isinstance(user, str):
            user = {'emailAddress': user}
        user_permission = {
            'type': 'user',
            'role': user.get('role', 'reader'),
            'emailAddress': user.get('emailAddress')
        }
        batch.add(service.permissions().create(
                fileId=sheet_id,
                body=user_permission,
                fields='id',
        ))
        # domain_permission = {
        #     'type': 'domain',
        #     'role': 'reader',
        #     'domain': 'export-sheet@social-network-255302.iam.gserviceaccount.com'  # app.config.get('DEPLOYED_URL')
        # }
        # batch.add(service.permissions().create(
        #         fileId=sheet_id,
        #         body=domain_permission,
        #         fields='id',
        # ))
    batch.execute()
    return perm_list(sheet_id, service=service)


def all_files(*args, service=None):
    """ List, and possibly manage, all files owned by the app """
    if not service:
        creds = get_creds(service_config['sheets'])
        service = build('drive', 'v3', credentials=creds, cache_discovery=False)
    files_list = service.files().list().execute().get('items', [])
    return files_list


def perm_list(sheet_id, service=None):
    """ For a given worksheet, list who currently has access to view it. """
    if not service:
        creds = get_creds(service_config['sheets'])
        service = build('drive', 'v3', credentials=creds, cache_discovery=False)
    data = service.files().get(fileId=sheet_id, fields='name, id, permissions').execute()
    pprint(data)
    data['id'] = data.get('id', data.get('fileId', sheet_id))
    data['link'] = data.get('link', f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit#gid=0")
    return data


def create_sheet(campaign, service=None):
    """ Takes in an instance from the Campaign model and create a worksheet. """
    app.logger.info('================== create sheet =======================')
    if not service:
        creds = get_creds(service_config['sheets'])
        service = build('sheets', 'v4', credentials=creds, cache_discovery=False)
    timestamp = int(dt.timestamp(dt.now()))
    name = str(campaign.name).replace(' ', '_')
    title = f"{name}_{timestamp}"
    spreadsheet = {'properties': {'title': title}}
    spreadsheet = service.spreadsheets().create(body=spreadsheet, fields='spreadsheetId').execute()
    return update_sheet(campaign, id=spreadsheet.get('spreadsheetId'), service=service)


# TODO: ? Is this going to be used, or it should be deleted?
def read_sheet_full(id=SHARED_SHEET_ID, service=None):
    """ Get the information (not the values) for a worksheet with permissions granted to our app service. """
    app.logger.info('================== read sheet full =======================')
    if not service:
        creds = get_creds(service_config['sheets'])
        service = build('sheets', 'v4', credentials=creds, cache_discovery=False)
    ranges = ['Sheet1!A1:B3']
    include_grid_data = True  # Ignored if a field mask was set in the request.
    request = service.spreadsheets().get(spreadsheetId=id, ranges=ranges, includeGridData=include_grid_data)
    spreadsheet = request.execute()
    id = spreadsheet.get('spreadsheetId')
    pprint(spreadsheet)
    link = f"https://docs.google.com/spreadsheets/d/{id}/edit#gid=0"
    return (spreadsheet, id, link)


def read_sheet(id=SHARED_SHEET_ID, range_=None, service=None):
    """ Read a sheet that our app service account has been given permission for. """
    app.logger.info(f'============== read sheet: {id} =====================')
    if not service:
        creds = get_creds(service_config['sheets'])
        service = build('sheets', 'v4', credentials=creds, cache_discovery=False)
    # TODO: Currently okay if range_ is known. Otherwise we need to figure it so we can see the sheet data.
    range_ = range_ or 'Sheet1!A1:B3'
    value_render_option = 'FORMATTED_VALUE'  # 'FORMATTED_VALUE' | 'UNFORMATTED_VALUE' | 'FORMULA'
    date_time_render_option = 'FORMATTED_STRING'  # 'FORMATTED_STRING' | 'SERIAL_NUMBER'
    major_dimension = 'ROWS'  # 'ROWS' | 'COLUMNS'
    request = service.spreadsheets().values().get(
        spreadsheetId=id,
        range=range_,
        valueRenderOption=value_render_option,
        dateTimeRenderOption=date_time_render_option,
        majorDimension=major_dimension
        )
    spreadsheet = request.execute()
    spreadsheet['id'] = spreadsheet.get('spreadsheetId', id)
    spreadsheet['link'] = spreadsheet.get('link', f"https://docs.google.com/spreadsheets/d/{id}/edit#gid=0")
    return spreadsheet


def clean(obj):
    """ Make sure this obj is serializable. Datetime objects should be turned to strings. """
    if isinstance(obj, dt):
        return obj.isoformat()
    return obj


def get_vals(campaign):
    """ Get the values we want to put into our worksheet report """
    brands = ['Brand', ', '.join([ea.name for ea in campaign.brands])]
    users = ['Influencer', ', '.join([ea.name for ea in campaign.users])]
    brand_data = [campaign.brands[0].insight_report(label_only=True)]
    for brand in campaign.brands:
        brand_data.append(brand.insight_report())
    columns = campaign.report_columns()
    # all fields need to be serializable, which means all datetime fields should be changed to strings.
    results = [[clean(getattr(post, ea, '')) for ea in columns] for post in campaign.posts]
    sheet_rows = [brands, users, [''], *brand_data, [''], columns, *results]
    app.logger.info(f"-------- get_vals Total rows: {len(sheet_rows)}, with {len(results)} rows of posts --------")
    return sheet_rows


def compute_A1(arr2d, start='A1', sheet='Sheet1'):
    """ Determine A1 format for 2D-array input, on given sheet, starting at given cell """
    row_count = len(arr2d)
    col_count = len(max(arr2d, key=len))
    # TODO: write regex that separates the letter and digit sections. 'A1' would have following result:
    col, row = 'A', 1
    final_col = chr(ord(col) + col_count)
    final_row = row_count + row
    return f"{sheet}!{start}:{final_col}{final_row}"


def update_sheet(campaign, id=SHARED_SHEET_ID, service=None):
    """ Get the data we want, then append it to the worksheet """
    app.logger.info('================== update sheet =======================')
    if not service:
        creds = get_creds(service_config['sheets'])
        service = build('sheets', 'v4', credentials=creds, cache_discovery=False)
    value_input_option = 'USER_ENTERED'  # 'RAW' | 'USER_ENTERED' | 'INPUT_VALUE_OPTION_UNSPECIFIED'
    insert_data_option = 'OVERWRITE'  # 'OVERWITE' | 'INSERT_ROWS'
    major_dimension = 'ROWS'  # 'ROWS' | 'COLUMNS'
    vals = get_vals(campaign)
    range_ = compute_A1(vals) or 'Sheet1!A1:B2'
    value_range_body = {
        "majorDimension": major_dimension,
        "range": range_,
        "values": vals
    }
    request = service.spreadsheets().values().append(
        spreadsheetId=id,
        range=range_,
        valueInputOption=value_input_option,
        insertDataOption=insert_data_option,
        body=value_range_body
        )
    spreadsheet = request.execute()
    return read_sheet(id=spreadsheet.get('spreadsheetId'), range_=range_, service=service)
