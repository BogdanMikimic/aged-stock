import pandas as pd
from django.contrib.auth.models import User
from ..models import CustomerService


def only_one_tab_check(spreadsheet_and_path:str) -> bool:
    """
    Checks that the spreadsheet has only one tab
    """
    file = pd.ExcelFile(spreadsheet_and_path, engine='openpyxl')
    if len(file.sheet_names) == 1:
        file.close()
        return True
    else:
        file.close()
        return False


def check_spreadsheet_contains_data(spreadsheet_and_path:str) -> bool:
    """
    Checks that the document is not blank
    """
    df = pd.read_excel(spreadsheet_and_path)
    # check if the document actually holds any values
    if not (df.notna().any().any()):
        return False
    else:
        return True


def return_data_frame_without_empty_rows_and_cols(spreadsheet_and_path:str) -> object:
    """
    Returns only the data as a pandas dataframe, removing empty rows and columns
    """
    df = pd.read_excel(spreadsheet_and_path, header=None)
    # delete rows where all elements are NaN
    df = df.dropna(how='all')
    # delete columns where all elements are NaN
    df = df.dropna(axis=1, how='all')
    # Use the first row as headers
    df.columns = df.iloc[0]  # Set the first row as the column headers
    df = df[1:]  # Drop the first row since it's now the header
    # Reset the index of the DataFrame
    df.reset_index(drop=True, inplace=True)
    return df


def check_headers(expected_headers: list[str], dataframe:object) -> bool:
    """
    Checks the headers in the dataframe against expected headers and returns True if they are the same
    and Fa;se if they are not
    """
    # Retrieve the actual headers from the DataFrame
    actual_headers = dataframe.columns.tolist()
    # Check if the expected headers match the actual headers
    if list(expected_headers) == list(actual_headers):
        return True
    else:
        return False


def check_salespeople_in_database(dataframe: object) -> tuple[list[str], list[str]] | bool:
    """
    It checks if all the salespeople in the xlsx exist in the database, if not it returns them to be created.
    It checks if all the salespeople in the database exist in the xlsx, if not they are marked for deletion.
    If nothing needs to be deleted or created returns a boolean (True)
    Salespeople accounts need to be created before customers, because they act as a foreign key in customers
    For security the accounts need to be created or deleted manually

    :param dataframe: a pandas dataframe
    :returns: A tuple of lists with accounts to be created or deleted if any or True if none needs to be created
    """
    customers_in_xlsx_list = dataframe['Sales Rep'].tolist()
    customers_in_database_raw = User.objects.values('first_name', 'last_name')
    customers_in_database_list = list()
    for customer in customers_in_database_raw:
        customers_in_database_list.append(f'{customer["first_name"]} {customer["last_name"]}')
    to_be_created = list()
    to_be_deleted = list()
    # check accounts to be created
    for customer_in_excel in customers_in_xlsx_list:
        if customer_in_excel not in customers_in_database_list:
            to_be_created.append(customer_in_excel)
    # check accounts to be deleted
    for customer_in_database in customers_in_database_list:
        if customer_in_database not in customers_in_xlsx_list:
            to_be_deleted.append(customer_in_database)

    if len(to_be_created) > 0 or len(to_be_deleted) > 0:
        return to_be_created, to_be_deleted
    else:
        return True


def create_customer_care_accounts(dataframe: object) -> None:
    customer_care_agents_list = dataframe['Customer Care Agent'].tolist()
    # create customer care if it does not exist
    for pers in customer_care_agents_list:
        CustomerService.objects.get_or_create(customer_service_rep=pers)

    # delete existing customer care rep if not in the xlsx
    customer_care_db_list = CustomerService.objects.values_list('customer_service_rep', flat=True)
    c_care_to_delete = list()
    for c_care_agent in customer_care_db_list:
        if c_care_agent not in customer_care_agents_list:
            c_care_to_delete.append(c_care_agent)

    for cc_to_delete in c_care_to_delete:
        del_obj = CustomerService.objects.get(customer_service_rep=cc_to_delete)
        del_obj.delete()



def create_customer_accounts(dataframe: object) -> None:
    pass
    # TODO: finish create_customer_accounts function

