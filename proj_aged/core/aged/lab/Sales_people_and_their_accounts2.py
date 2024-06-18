import pandas as pd
from django.contrib.auth.models import User
from ..models import CustomerService, Customers


def only_one_tab_check(spreadsheet_and_path:str) -> bool:
    """
    Checks that the spreadsheet has only one tab
    :param spreadsheet_and_path: path to spreadsheet
    :return: True if the spreadsheet has only one tab, False otherwise
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
    Checks that the document is not blank.
    :param spreadsheet_and_path: path to spreadsheet
    :return: True if the document is not blank, False otherwise
    """
    df = pd.read_excel(spreadsheet_and_path)
    # check if the document actually holds any values
    if not (df.notna().any().any()):
        return False
    else:
        return True


def return_data_frame_without_empty_rows_and_cols(spreadsheet_and_path: str) -> pd.DataFrame:
    """
    Returns only the data as a pandas dataframe, removing empty rows and columns
    :param spreadsheet_and_path: path to spreadsheet
    :return: Pandas dataframe
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


def check_headers(expected_headers: list[str], dataframe: object) -> bool:
    """
    Checks the headers in the dataframe against expected headers
    :param expected_headers: expected headers of the spreadsheet as list of strings
    :param dataframe: Pandas dataframe
    :return: True if the headers match, False otherwise
    """
    # retrieve the actual headers from the DataFrame
    actual_headers = dataframe.columns.tolist()
    # check if the expected headers match the actual headers
    if expected_headers == actual_headers:
        return True
    else:
        return False


def check_salespeople_in_database(dataframe: object) -> tuple[list[str], list[str]] | bool:
    """
    It checks if all the salespeople in the xlsx exist in the database, if not it returns them to be created.
    It checks if all the salespeople in the database exist in the xlsx, if not they are marked for deletion.
    If nothing needs to be deleted or created returns a boolean (False)
    Salespeople accounts need to be created before customers, because they act as a foreign key in customers
    For security the accounts need to be created or deleted manually

    :param dataframe: a pandas dataframe
    :returns: A tuple of lists with accounts to be created or deleted if any or False if none needs to be created
    """
    customers_in_xlsx_list = set(dataframe['Sales Rep'].tolist())
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
        # ignore the superuser Miki Mic
        if customer_in_database != "Miki Mic" and customer_in_database not in customers_in_xlsx_list:
            to_be_deleted.append(customer_in_database)
    # if there are accounts to be created, return a tuple of lists
    if len(to_be_created) > 0 or len(to_be_deleted) > 0:
        return to_be_created, to_be_deleted
    # if all accounts exist, return False
    else:
        return False


def create_customer_care_accounts(dataframe: object) -> None:
    """
    Populates the database with customer care entries rom xlsx
    Deletes the customer care entries that are not in the xlsx

    :param dataframe: Pandas dataframe
    """

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

def do_not_use_in_production_automatic_accounts_creation(dataframe: object) -> None:
    """
    Just a speedy function to create user accounts. Don't use it in production
    """

    sales_reps = return_data_frame_without_empty_rows_and_cols(dataframe)['Customer Name'].to_list()
    for sale_rep in sales_reps:
        User.objects.create_user(
            username=f'{sale_rep.split(" ")[0]}',
            first_name=f'{sale_rep.split(" ")[0]}',
            last_name= f'{sale_rep.split(" ")[1]}',
            password='a'
        )


def create_customer_accounts(dataframe: object) -> None:
    """
    Adds/updates customers in the database and link them to the foreign keys of Sales person and customer care rep.
    It marks as inactive customers not in the database

    :param dataframe: a Pandas dataframe representing the most current sales people, customer care and customers table
    """
    for i in range(len(dataframe)):
        # extract data from xlsx rows
        row = dataframe.iloc[i]
        # retrieve the sales person and customer care agent that matches the database
        sales_person = User.objects.filter(first_name=row['Sales Rep'].split(' ')[0],
                                           last_name=row['Sales Rep'].split(' ')[1]).get()
        customer_care_agent = CustomerService.objects.filter(customer_service_rep=row['Customer Care Agent']).get()
        Customers.objects.update_or_create(
            customer_name=row['Customer Name'],
            defaults={
            'customer_number':row['Customer Number'],
            'salesperson_owning_account':sales_person,
            'allocated_customer_service_rep':customer_care_agent,
            'customer_status':'Active'}
        )

    # deactivate inactive customers that do not appear in the xlsx anymore
    customers = dataframe['Customer Name'].tolist()
    inactive_customers = Customers.objects.exclude(customer_name__in=customers)
    inactive_customers.update(allocated_customer_service_rep=None,
                              salesperson_owning_account=None,
                              customer_status='Inactive')





