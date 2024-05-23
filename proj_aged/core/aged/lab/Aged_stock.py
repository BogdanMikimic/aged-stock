import pandas as pd
from datetime import date, datetime
from ..models import *

def check_if_file_was_already_uploaded(xlsx_file_path: str) -> bool:
    """
    Sometimes the same xlsx file is being shared.
    No two files have the same creation date

    :param xlsx_file_path: path to the file as a string
    :return: True if file has been already uploaded, False if file was not yet updated
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
    :return: Returns None
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
    :return: Returns None
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
    :return: Returns None
    """
    locations_in_xlsx_set = set(dataframe['Stor loc'].tolist())
    for xlsx_location in locations_in_xlsx_set:
        LocationsForStocks.objects.update_or_create(
            location_of_stocks=xlsx_location
        )

def check_is_expired(product_expiration_date_time:str) -> bool:
    """
    Check the expiration date of the product

    :param product_expiration_date: expiration date of the product as string
    :return: Returns True if the product is expired False if it is not
    """
    # get today's date
    today = date.today()
    # format expiration date to extract only the date (leave out the time)
    exp_date_as_string = product_expiration_date_time.split(' ')[0].strip()
    expiration_date = datetime.strptime(exp_date_as_string, '%Y-%m-%d').date()

    # check if the product is expired
    return expiration_date < today


def put_products_in_the_database(dataframe: object) -> None:
    """
    Puts product in the database.
    Products sometimes get de-listed, and re-listed.
    If a product is truly deleted, it can be deleted manually from the database.

    :param dataframe: pandas dataframe containing products information
    :return: None
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




