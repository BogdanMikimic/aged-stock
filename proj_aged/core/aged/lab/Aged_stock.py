import pandas as pd
from datetime import date, datetime
from ..models import *

def check_if_file_was_already_uploaded(xlsx_file_path: str) -> bool:
    """
    Sometimes the same xlsx file is being shared.
    No two files have the same creation date

    :param xlsx_file_path: path to the file as a string
    :returns: True if file has been already uploaded, False if file was not yet updated
    """

    file = pd.ExcelFile(xlsx_file_path, engine='openpyxl')
    workbook = file.book
    creation_date = str(workbook.properties.created)

    data_file_created_list = CheckIfFileWasAlreadyUploaded.objects.values_list('data_creare_fisier', flat=True)

    if creation_date in data_file_created_list:
        file.close()
        return True
    else:
        file.close()
        CheckIfFileWasAlreadyUploaded(data_creare_fisier=creation_date).save()
        return False

def put_brand_into_db(dataframe: object) -> None:
    """
    Brings the unique brands into the database.
    Brands are rarely changed and there are just a few of them, so they are not deleted from the database.

    :param dataframe: pandas dataframe containing stock information
    :returns: Returns None
    """
    brands_in_xlsx_set = set(dataframe['Brand'].tolist())
    for xlsx_brand in brands_in_xlsx_set:
        Brands.objects.update_or_create(
            brand=xlsx_brand
        )


def put_material_type_into_db(dataframe: object) -> None:
    """
    Brings unique material types into the database.
    There is a small number of material types (Chocolate, nuts, etc),
    and most of them will stay the same through, so no material type is
    deleted.

    :param dataframe: pandas dataframe containing stock information
    :returns: Returns None
    """
    material_types_in_xlsx_set = set(dataframe['Matl Group'].tolist())
    for xlsx_material_type in material_types_in_xlsx_set:
        MaterialType.objects.update_or_create(
            material_type=xlsx_material_type
        )


def put_stock_location_in_database(dataframe: object) -> None:
    """
    Brings unique stock locations into the database.
    There are only a few locations - one or two that won;t change much,
    so no location is deleted.

    :param dataframe: pandas dataframe containing stock information
    :returns: Returns None
    """
    locations_in_xlsx_set = set(dataframe['Stor loc'].tolist())
    for xlsx_location in locations_in_xlsx_set:
        LocationsForStocks.objects.update_or_create(
            location_of_stocks=xlsx_location
        )

def date_to_string_or_string_to_date(my_date: str|object) -> str|object:
    """
    Converts datetime-date objects into strings
    and strings representing dates in the format
    year-month-day into datetime-date objects

    :param my_date: either a string in the Y-m-d format or a datetime.date object
    :returns: either a string in the Y-m-d format or a datetime.date object, opposite to what it received as input
    """
    if isinstance(my_date, str):
        return datetime.strptime(my_date, '%Y-%m-%d').date()
    else:
        return my_date.strftime('%Y-%m-%d')

def check_is_expired_in_xlsx(product_expiration_date_time:str|object) -> bool:
    """
    Check the expiration date of the product
    checks if data is string and converts string to datetime object

    :param product_expiration_date_time: expiration date of the product as string, containing date and time
    :returns: Returns True if the product is expired False if it is not
    """
    # get today's date
    today = date.today()
    # format expiration date to extract only the date (leave out the time)
    if isinstance(product_expiration_date_time, str):
        exp_date_as_string = product_expiration_date_time.split(' ')[0].strip()
        expiration_date = date_to_string_or_string_to_date(exp_date_as_string)
    else:
        expiration_date = product_expiration_date_time.date()

    # check if the product is expired
    return expiration_date < today


def put_products_in_the_database(dataframe: object) -> None:
    """
    Puts product in the database.
    Products sometimes get de-listed, and re-listed.
    If a product is truly deleted, it can be deleted manually from the database.

    :param dataframe: pandas dataframe containing products information
    :returns: None
    """
    for i in range(len(dataframe)):
        # extract data from xlsx rows
        row = dataframe.iloc[i]
        product_brand = Brands.objects.filter(brand=row['Brand']).get()
        product_material_type = MaterialType.objects.filter(material_type=row['Matl Group']).get()
        Products.objects.update_or_create(
            cod_material=row['Material'],
            defaults={
            'description': row['Description'],
            'product_brand': product_brand,
            'product_material_type': product_material_type})


def put_available_stock_in_the_database(dataframe: object) -> None:
    """
    Uploads the available stock in the database
    Reports can be inaccurate, so if the stock exists as available in the database,
    the available quantity is trusted
    The stock is uniquely identified by the material name, batch number and expiration date.
    No two stocks can have the same material name, batch number and expiration date.

    :param dataframe: pandas dataframe containing products information
    :returns: None
    """
    for i in range(len(dataframe)):
        # extract data from xlsx rows
        row = dataframe.iloc[i]
        product = Products.objects.filter(cod_material=row['Material']).get()
        # check the product is not already expired in the xlsx file
        print(row['Expiration date'], type(row['Expiration date']))
        if not check_is_expired_in_xlsx(row['Expiration date']):
            # checks if the product with the same code, batch number and expiration date exists in the database
            # if it exists it ignores it and trusts the available stock
            if not AvailableStock.objects.filter(available_product=product,
                                         expiration_date = row['Expiration date'].date(),
                                         batch=row['Batch']).exists():
                new_stock = AvailableStock()
                new_stock.available_product = product
                new_stock.stock_location = LocationsForStocks.objects.filter(location_of_stocks=row['Stor loc']).get()
                new_stock.expiration_date = row['Expiration date'].date()
                new_stock.batch = row['Batch']
                new_stock.original_quantity_in_kg = str(row['Quantity'])
                new_stock.available_quantity_in_kg = str(row['Quantity'])
                new_stock.save()


