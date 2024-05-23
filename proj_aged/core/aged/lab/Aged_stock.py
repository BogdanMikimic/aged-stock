import pandas as pd
from datetime import date, datetime
from ..models import CheckIfFileWasAlreadyUploaded, Brands, MaterialType, LocationsForStocks, Products, AvailableStock

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

def get_brand_into_db(dataframe: object) -> None:
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


def get_material_type_into_db(dataframe: object) -> None:
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


def get_stock_location_in_database(dataframe: object) -> None:
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


def get_products_in_the_database(dataframe: object) -> None:
    """
    Product stocks in xlsx can be inaccurate, therefore if a product exists in the database
    with the same product code, the same batch number and the same expiration date,
    and if the product is not expired
    """

    for i in range(len(dataframe)):
        # extract data from xlsx rows
        row = dataframe.iloc[i]
        # check product is not expired
        if not check_is_expired(row['Expiration date']):
            # if product exists in database, leave it alone
            # else upload in database
            pass


class AgedStock:
    # ia ca argument fisierul excel cu aged stock, o citeste, si o intoarce ca lista de dictionare
    # prin optiunea load_workbook(fisier.xlsx, data_only=True) -> data_only=True aduce valorile in loc de formule
    # ultima coloana e vlookup (deci formula) si aduce valorile
    def __init__(self, file_with_path):
        self.my_xcel = file_with_path
        self.excel_object = None
        self.my_tab = None
        self.table_as_list_of_dicts = list()
        self.row_count = 0
        self.cell_count = 0


    def runAll(self):
        #Create excel object
        self.excel_object = load_workbook(self.my_xcel, data_only=True)
        #Select right tab
        self.my_tab = self.excel_object['data']

        #itereaza rand cu rand
        for row in self.my_tab.iter_rows():
            self.row_count += 1
            if self.row_count >1: #treci peste primul rand care e data
                dictionar_row = dict() #creaza un dict care se refreshuie cu fiecare rand
                self.cell_count = 0
                #pune in dictionar datele din fiecare rand si fiecare dictionar in lista
                for cell in row:
                    self.cell_count += 1
                    if self.cell_count == 1:
                        dictionar_row['Plnt'] = cell.value
                    elif self.cell_count == 2:
                        dictionar_row['Stor loc'] = cell.value
                    elif self.cell_count == 3:
                        dictionar_row['Material'] = cell.value
                    elif self.cell_count == 4:
                        dictionar_row['Brand'] = cell.value
                    elif self.cell_count == 5:
                        # I have a material group called MISCEl. with a dot.
                        # That shits on my logic within using the material name
                        # as an HTML custom atribute, so I am taking the dot out
                        #at the source
                        if cell.value.endswith('.'):
                            goodValue = cell.value [:-1]
                        else:
                            goodValue = cell.value
                        print(goodValue)
                        dictionar_row['Matl Group'] = goodValue
                    elif self.cell_count == 6:
                        dictionar_row['Batch'] = cell.value
                    elif self.cell_count == 7:
                        dictionar_row['Quantity'] = cell.value
                    elif self.cell_count == 8:
                        dictionar_row['Unrestricted'] = cell.value
                    elif self.cell_count == 9:
                        dictionar_row['Expiration date'] = cell.value.date()
                    elif self.cell_count == 10:
                        dictionar_row['Description'] = cell.value
                self.table_as_list_of_dicts.append(dictionar_row)
        return self.table_as_list_of_dicts

