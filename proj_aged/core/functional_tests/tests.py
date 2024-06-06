from django.contrib.staticfiles.testing import StaticLiveServerTestCase # this a  class provided by Django for tests
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from aged.models import AvailableStock,\
    Products,\
    LocationsForStocks,\
    CheckIfFileWasAlreadyUploaded,\
    Brands, \
    Customers, \
    CustomerService, \
    OffersLog

from aged.lab.Aged_stock import date_to_string_or_string_to_date
from aged.lab.Sales_people_and_their_accounts2 import return_data_frame_without_empty_rows_and_cols
from selenium.webdriver.common.by import By
from django.contrib.auth.models import User
import os
import datetime
import pandas as pd
import time
import PyPDF2


message = '''
Hi!

You are now running functional tests for the "Aged Stock" tool.
Each test was checked at the time it was written with the provided dataset,
uploaded from one of the  AgedStock.xlsx files (for instance 01_good_AgedStock.xlsx)

However, because the nature of the app is to manage stock close to the expiration date,
and several functions prevent uploading of expired data from the xlsx file and periodically
clear expired offers/products, some of your tests may fail, or you will get a Selenium error. For
instance Selenium may look for a specific product code in a table row, without finding it, because
at the time you are running the test, the offer is expired, and the product was never uploaded
into the database as available stock in the first place.

If that happens, first check the "proj_aged/core/aged/lab/DataSafeOnes/01_good_AgedStock.xlsx" file,
column I - Expiration date, and make sure all dates are in the future.

Next, MixinFunctions.my_offer_date returns 2 dates - a "present" date and "future" offer date.
It will make sense for you to change those to a more appropriate dates that represent the present/future.  
'''
print(message)

class MixinFunctions:
    def return_xlsx_dataframe(self, relative_path_to_xlsx: str) -> pd.DataFrame:
        right_absolute_file_path = os.path.abspath(relative_path_to_xlsx)
        return return_data_frame_without_empty_rows_and_cols(right_absolute_file_path)

    def my_offer_date(self, is_present=True) -> str:
        """
        This function is used to return dates for the creation of offers
        I used 2 type of dates in the code for the offers, a 'present' one, and a 'future' one
        They were used to check different filters and that data registered correctly in the database.
        """
        if is_present:
            return '2024-05-28'
        else:
            return '2024-06-03'

    def make_offer(self,
                   customer_name: str,
                   offered_quantity: str,
                   discount_percent: str,
                   price_per_kg: str,
                   date_of_offer: str) -> None:
        """
        Contains all the Selenium logic to fill the form that creates a product offer
        """
        # select customer
        select_element = self.browser.find_element(By.NAME, 'customer')
        select = Select(select_element)
        select.select_by_visible_text(customer_name)
        # offered quantity
        quantity_field = self.browser.find_element(By.NAME, 'quantity')
        quantity_field.clear()
        quantity_field.send_keys(offered_quantity)
        # offered discount
        discount_field = self.browser.find_element(By.NAME, 'discount_in_percent')
        discount_field.clear()
        discount_field.send_keys(discount_percent)
        # offered price/kg
        price_field = self.browser.find_element(By.NAME, 'price')
        price_field.clear()
        price_field.send_keys(price_per_kg)
        # offer date YYYY-MM-DD format -> '2024-05-28'
        date_field = self.browser.find_element(By.NAME, 'date_of_offer')
        date_field.clear()
        date_field.send_keys(date_of_offer)

    def create_account(self, first_name: str, last_name: str, is_superuser=True) -> None:
        if is_superuser:
            if first_name == 'Miki':
                User.objects.create_superuser(
                    username='Mikimic',
                    first_name='Miki',
                    last_name='Mic',
                    password='adminpassword',
                    email='admin@example.com'
                    )
            else:
                User.objects.create_superuser(
                    username=first_name,
                    first_name=first_name,
                    last_name=last_name,
                    password='password123',
                    email=f'{first_name}@example.com'
                )
        else:
            User.objects.create_user(
                username=first_name,
                first_name=first_name,
                last_name=last_name,
                password='password123',
                email=f'{first_name}@example.com'
            )

    def log_in_account(self, username: str, password: str) -> None:
        """
        Logs user or superuser in its account
        """
        self.browser.get(self.live_server_url + '/accounts/login/')
        username_input = self.browser.find_element(By.ID, 'id_username')
        username_input.send_keys(username)
        password_input = self.browser.find_element(By.ID, 'id_password')
        password_input.send_keys(password)
        self.browser.find_element(By.CLASS_NAME, 'input_form_submit').click()

    def upload_aged_stock_only(self, relative_path_to_aged_stock_xlsx) -> None:
        self.log_in_account('Mikimic', 'adminpassword')
        self.browser.get(self.live_server_url)
        self.browser.find_element(By.LINK_TEXT, 'Upload Files 🡢').click()
        self.browser.find_element(By.LINK_TEXT, '(3) Aged stock').click()
        xlsx_upload_field = self.browser.find_element(By.ID, 'id_file_field')
        relative_file_path = relative_path_to_aged_stock_xlsx
        absolute_file_path = os.path.abspath(relative_file_path)
        xlsx_upload_field.send_keys(absolute_file_path)
        self.browser.find_element(By.ID, 'id_submit_file').click()

    def upload_aged_salespeople_only(self, relative_path_to_aged_stock_xlsx) -> None:
        self.log_in_account('Mikimic', 'adminpassword')
        self.browser.get(self.live_server_url)
        self.browser.find_element(By.LINK_TEXT, 'Upload Files 🡢').click()
        self.browser.find_element(By.LINK_TEXT, '(1) Salespeople, customer care agents and customers').click()
        xlsx_upload_field = self.browser.find_element(By.ID, 'id_file_field')
        relative_file_path = relative_path_to_aged_stock_xlsx
        absolute_file_path = os.path.abspath(relative_file_path)
        xlsx_upload_field.send_keys(absolute_file_path)
        self.browser.find_element(By.ID, 'id_submit_file').click()

    def admin_uploads_salespeople_and_aged_stock_xlsx_to_db(self,
                                                            relative_path_to_salespeople_xlsx: str,
                                                            relative_path_to_aged_stock_xlsx: str) -> None:

        # first upload the file - with salespeople, customer care agents, and customers
        self.upload_aged_salespeople_only(relative_path_to_salespeople_xlsx)
        # second file (aged stock)
        self.upload_aged_stock_only(relative_path_to_aged_stock_xlsx)


# Morgan - a salesperson in the UK department heard about this cool app that was designed by a colleague
# to help the sales people better manage their aged stock
class LoginIsRequired(StaticLiveServerTestCase):
    def setUp(self) -> None:  # This code runs once BEFORE EACH test
        self.browser = webdriver.Firefox()  # starts firefox
        self.browser.implicitly_wait(5)

    def tearDown(self) -> None:  # This code runs once AFTER EACH test
        self.browser.quit() # quits firefox

    # she got the url from her manager and she looks at the website, but she is greeted by a page that requires
    # a username and a password
    def test_sign_in_is_required(self):
        self.browser.get(self.live_server_url)
        self.assertIsNotNone(self.browser.find_elements(By.ID, 'id_username'), 'There is no "id_username" id on page')
        self.assertIsNotNone(self.browser.find_elements(By.ID, 'id_password'), 'There is no "id_password" id on page')
        # she clicks on the navigation bar on the "Available stock" button only to be greeted by the same request
        available_stock_anchor_tag = self.browser.find_element(By.LINK_TEXT, 'Available stock')
        available_stock_anchor_tag.click()
        self.assertIsNotNone(self.browser.find_elements(By.ID, 'id_username'), 'There is no "id_username" id on page')
        self.assertIsNotNone(self.browser.find_elements(By.ID, 'id_password'), 'There is no "id_password" id on page')
        # she clicks on the navigation bar on the "My offers" button only to be greeted by the same request
        my_offers_anchor_tag = self.browser.find_element(By.LINK_TEXT, 'My offers')
        my_offers_anchor_tag.click()
        self.assertIsNotNone(self.browser.find_elements(By.ID, 'id_username'), 'There is no "id_username" id on page')
        self.assertIsNotNone(self.browser.find_elements(By.ID, 'id_password'), 'There is no "id_password" id on page')
        # finally, she clicks on the navigation bar on the "My offers" button only to be greeted by the same request
        help_page_anchor_tag = self.browser.find_element(By.LINK_TEXT, 'Help')
        help_page_anchor_tag.click()
        self.assertIsNotNone(self.browser.find_elements(By.ID, 'id_username'), 'There is no "id_username" id on page')
        self.assertIsNotNone(self.browser.find_elements(By.ID, 'id_password'), 'There is no "id_password" id on page')

        # convinced that she needs a username and a password, she goes to the admin to have one created


class AdminUploadsSpreadsheetTest(StaticLiveServerTestCase, MixinFunctions):
    def setUp(self) -> None:  # This code runs once BEFORE EACH test
        self.browser = webdriver.Firefox() # starts firefox
        # Admin creates a superuser for himself (needs to be Mikimic)
        self.create_account('Miki', 'Mic')

    def tearDown(self) -> None:  # This code runs once AFTER EACH test
        self.browser.quit()  # quits firefox

    # And logs into his account - which differs from anyone else's because it has an "Upload Files ->" button
    def test_log_in_and_customer_file_upload_for_admin(self):
        self.log_in_account('Mikimic', 'adminpassword')
        upload_files_button = self.browser.find_element(By.LINK_TEXT, 'Upload Files 🡢')
        self.assertIsNotNone(upload_files_button)
        # He clicks on upload files button
        upload_files_button.click()
        # and he is greeted by the question "What file you need to upload?"
        self.assertEqual(self.browser.find_elements(By.CLASS_NAME, 'p_menu')[1].text, 'What file you need to upload?')
        # he navigates down to the "(1) Salespeople, customer care agents and customers" button and clicks on it
        self.browser.find_element(By.LINK_TEXT, '(1) Salespeople, customer care agents and customers').click()
        # a new page with a form opens
        # he navigates to the upload field and browse for a file to upload
        # unfortunately he uploads the wrong file that has more than one tab
        xlsx_upload_field = self.browser.find_element(By.ID, 'id_file_field')
        wrong_relative_path = 'aged/lab/DataSafeOnes/8_multiple_tabs.xlsx'
        wrong_absolute_file_path = os.path.abspath(wrong_relative_path)
        xlsx_upload_field.send_keys(wrong_absolute_file_path)
        self.browser.find_element(By.ID, 'id_submit_file').click()
        # and he is meet by an error message
        self.assertEqual(self.browser.find_element(By.ID, 'upload_status').text,
                         'The file has more than one tab. Fix file and re-upload')

        # he goes back and tries again, but this time he uploads a file that holds an empty spreadsheet
        self.upload_aged_salespeople_only('aged/lab/DataSafeOnes/9_blank_file.xlsx')
        # and this time the error message is different
        self.assertEqual(self.browser.find_element(By.ID, 'upload_status').text,
                         'The file has no data. Fix file and re-upload')

        # he goes back and tries again, this time he uploads an older file that does not contain the right headers
        self.upload_aged_salespeople_only('aged/lab/DataSafeOnes/10_wrong_headers.xlsx')
        # and this time the error message is different - telling him about the wrong headers
        self.assertTrue(self.browser.find_element(By.ID, 'upload_status').text.startswith("The file has the wrong headers."))

        # he goes back and this time uploads a good file (containing just one salesperson - Mikimic)
        self.upload_aged_salespeople_only('aged/lab/DataSafeOnes/16_just_one_sales_rep_mikimic.xlsx')
        # he checks that the file was uploaded successfully
        self.assertEqual(self.browser.find_element(By.ID, 'id_message').text, 'All accounts updated')

        # he also looks in the database and checks for a few customers that were in the xlsx file
        my_customers_xlsx = self.return_xlsx_dataframe('aged/lab/DataSafeOnes/16_just_one_sales_rep_mikimic.xlsx')
        random_rows = my_customers_xlsx.sample(n=2)
        self.assertTrue(Customers.objects.filter(
            customer_name=random_rows.iloc[0]['Customer Name'],
            customer_number=random_rows.iloc[0]['Customer Number'],
            allocated_customer_service_rep=CustomerService.objects.filter(
                customer_service_rep=random_rows.iloc[0]['Customer Care Agent']).get()
            ).exists())
        self.assertTrue(Customers.objects.filter(
            customer_name=random_rows.iloc[1]['Customer Name'],
            customer_number=random_rows.iloc[1]['Customer Number'],
            allocated_customer_service_rep=CustomerService.objects.filter(
                customer_service_rep=random_rows.iloc[1]['Customer Care Agent']).get()
            ).exists())

    # the admin goes to upload the aged stock file
    def test_log_in_and_stock_file_upload_for_admin(self):
        # he logs in to his account
        self.log_in_account('Mikimic', 'adminpassword')
        upload_files_button = self.browser.find_element(By.LINK_TEXT, 'Upload Files 🡢')
        # He clicks on upload files button
        upload_files_button.click()
        # and then he clicks on the aged stock upload
        self.browser.find_element(By.LINK_TEXT, '(3) Aged stock').click()
        # he is greeted by a message that contains the word 'aged stock'
        self.assertEqual(self.browser.find_element(By.ID,'span_aged_stock').text, 'aged stock')
        # he navigates to the upload field and browse for a file to upload
        # unfortunately he uploads the wrong file that has more than one tab
        xlsx_upload_field = self.browser.find_element(By.ID, 'id_file_field')
        wrong_relative_path = 'aged/lab/DataSafeOnes/02_wrong_AgedStock_more_than_one_tab.xlsx'
        wrong_absolute_file_path = os.path.abspath(wrong_relative_path)
        xlsx_upload_field.send_keys(wrong_absolute_file_path)
        self.browser.find_element(By.ID, 'id_submit_file').click()
        # and he is meet by an error message
        self.assertEqual(self.browser.find_element(By.ID, 'span_message').text,
                         'The file has more than one tab. Fix file and re-upload')

        # he goes back, and he tries again, this time uploading a blank file
        self.upload_aged_stock_only('aged/lab/DataSafeOnes/03_wrong_AgedStock_no_data.xlsx')
        # and he is meet by an error message
        self.assertEqual(self.browser.find_element(By.ID, 'span_message').text,
                         'The file does not contain any data.')

        # he goes back, and tries again, this time uploading a file with the wrong headers
        self.upload_aged_stock_only('aged/lab/DataSafeOnes/04_wrong_AgedStock_not_correct_headers.xlsx')
        # and he is meet by an error message
        self.assertTrue(self.browser.find_element(By.ID, 'span_message').text.startswith(
            'The file requires the following headers:'))

        # he goes back, and uploads the correct file
        self.upload_aged_stock_only('aged/lab/DataSafeOnes/01_good_AgedStock.xlsx')
        # he is met by a message that says the file was uploaded successfully
        self.assertEqual(self.browser.find_element(By.ID, 'span_message').text, 'File uploaded')

        # he checks his xlsx file for a few random products and checks that there are in the database
        my_stock_xlsx = self.return_xlsx_dataframe('aged/lab/DataSafeOnes/01_good_AgedStock.xlsx')
        random_rows = my_stock_xlsx.sample(n=2)
        self.assertTrue(AvailableStock.objects.filter(
            available_product=Products.objects.filter(cod_material=random_rows.iloc[0]['Material']).get(),
            stock_location=LocationsForStocks.objects.filter(location_of_stocks=random_rows.iloc[0]['Stor loc']).get(),
            expiration_date=random_rows.iloc[0]['Expiration date'].date(),
            batch=random_rows.iloc[0]['Batch'],
            # he is mindful that the app converts floats to integers
            original_quantity_in_kg=int(random_rows.iloc[0]['Quantity']),
            under_offer_quantity_in_kg=0,
            sold_quantity_in_kg=0,
            available_quantity_in_kg=int(random_rows.iloc[0]['Quantity'])
        ).exists())

        self.assertTrue(AvailableStock.objects.filter(
            available_product=Products.objects.filter(cod_material=random_rows.iloc[1]['Material']).get(),
            stock_location=LocationsForStocks.objects.filter(location_of_stocks=random_rows.iloc[1]['Stor loc']).get(),
            expiration_date=random_rows.iloc[1]['Expiration date'].date(),
            batch=random_rows.iloc[1]['Batch'],
            # he is mindful that the app converts floats to integers
            original_quantity_in_kg=int(random_rows.iloc[1]['Quantity']),
            under_offer_quantity_in_kg=0,
            sold_quantity_in_kg=0,
            available_quantity_in_kg=int(random_rows.iloc[1]['Quantity'])
        ).exists())

        # he also checks that the database captures the fact that the file was already
        # uploaded by recording the creation date of the file
        date_file_was_created_db_list = CheckIfFileWasAlreadyUploaded.objects.values_list('data_creare_fisier',
                                                                                          flat=True)
        right_absolute_file_path = os.path.abspath('aged/lab/DataSafeOnes/01_good_AgedStock.xlsx')
        file = pd.ExcelFile(right_absolute_file_path, engine='openpyxl')
        workbook = file.book
        creation_date = str(workbook.properties.created)
        self.assertTrue(creation_date in date_file_was_created_db_list)

        # and also checks that some brands were uploaded in the database
        self.assertTrue(Brands.objects.filter(brand='Chocogreat').exists())
        self.assertTrue(Brands.objects.filter(brand='ChocoElite').exists())

    def test_superuser_checks_the_all_stock_page(self):
        """
        This tests the available stocks page filtering and searching functionality
        """
        # populate database
        self.admin_uploads_salespeople_and_aged_stock_xlsx_to_db('aged/lab/DataSafeOnes/16_just_one_sales_rep_mikimic.xlsx',
                                                                 'aged/lab/DataSafeOnes/01_good_AgedStock.xlsx')

        # he goes to the page where all stock is displayed (userallstock), opened from 'Sell some stuff 🡢'
        self.browser.get(self.live_server_url)
        self.browser.find_element(By.LINK_TEXT, 'Sell some stuff 🡢').click()
        # the page tile is " Available stock "
        self.assertEqual(self.browser.title, 'Available stock')
        # he notices that there is a search functionality too, so he checks that out, by imputing CHO-168-194
        # he knows he only has one of these SKUs in the database
        search_bar = self.browser.find_element(By.ID, 'searchBar')
        search_bar.send_keys('CHO-168-194')
        self.browser.find_element(By.ID, 'searchButton').click()
        table_rows = self.browser.find_elements(By.TAG_NAME, 'tr')
        time.sleep(5)
        for row in table_rows:
            if row.value_of_css_property('display') == 'table-row':
                if not row.get_attribute('class') == "tr_first_line":
                    self.assertEqual(row.find_element(By.CLASS_NAME, 'table_sku').text, 'CHO-168-194')
        # there is a paragraph inviting him to click on it to open the filters
        clickable_paragraph = self.browser.find_element(By.ID, 'p_filter_message')
        clickable_paragraph.click()
        # he observes that the first element in the table starts with MIS, that suggest that the type of material is
        # miscellaneous - abbreviated MISCEL, so he clicks the checkbox to hide it
        self.browser.find_element(By.ID, 'MISCEL').click()
        # he checks that all the MISC elements are no longer in list
        misc_elements_list = self.browser.find_elements(By.XPATH, '//tr[@data-material="MISCEL"]')
        for itm in misc_elements_list:
            self.assertEqual(itm.value_of_css_property('visibility'), 'collapse')
        # he hides the fillings to
        self.browser.find_element(By.ID, 'FILLING').click()
        # he checks that all the MISC elements are no longer in list
        misc_elements_list = self.browser.find_elements(By.XPATH, '//tr[@data-material="FILLING"]')
        for itm in misc_elements_list:
            self.assertEqual(itm.value_of_css_property('visibility'), 'collapse')

        # he clicks the MISC checkbox again and checks that the MISCEL are back on the list
        self.browser.find_element(By.ID, 'MISCEL').click()
        # he checks that all the MISC elements are back in the list
        misc_elements_list = self.browser.find_elements(By.XPATH, '//tr[@data-material="MISCEL"]')
        for itm in misc_elements_list:
            self.assertEqual(itm.value_of_css_property('visibility'), 'visible')


class UserOffers(StaticLiveServerTestCase, MixinFunctions):
    def setUp(self) -> None:
        # Define the directory where files will be downloaded
        self.download_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'downloads')

        # Create the directory if it doesn't exist
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)

        # Set Firefox profile preferences for download
        option = webdriver.FirefoxOptions()
        option.set_preference('browser.download.folderList', 2)  # Use custom download location
        option.set_preference('browser.download.dir', self.download_dir)
        option.set_preference('browser.helperApps.neverAsk.saveToDisk', 'application/pdf')  # MIME type for PDF
        option.set_preference('pdfjs.disabled', True)  # Disable Firefox's built-in PDF viewer

        # Initialize the Firefox WebDriver with the specified profile
        self.browser = webdriver.Firefox(options=option)
        self.browser.implicitly_wait(10)

        # Admin has an account
        self.create_account('Miki', 'Mic')
        # He creates one account for Morgan who is a salesperson
        self.create_account('Morgan', 'Davis', False)
        # And one account for Quinn who is a manager
        self.create_account('Quinn', 'Miller')

        # he uploads the xlsx files in the database
        self.admin_uploads_salespeople_and_aged_stock_xlsx_to_db('aged/lab/DataSafeOnes/17_just_two_sales_people.xlsx',
                                                                 'aged/lab/DataSafeOnes/01_good_AgedStock.xlsx')

    def tearDown(self) -> None:  # This code runs once AFTER EACH test
        self.browser.quit()  # quits firefox

    def test_a_user_makes_offer(self):
        """
        This tests:
        - user (salesperson) logs in
        - clicking on the make offer button takes you to a form for that particular product
        - user can only see its own customers in the drop-down
        - quantity is capped to available quantity
        - making an offer redirects to the completion page
        - making an offer registers correctly in the database
        - downloading and checking the offer as a pdf
        - checks that the offered quantity can be revealed by activating the "under offer" filter on all stock page
        - checks that the offered quantity is deducted from the available quantity on the all stock page
        - making another offer, but in the meantime somebody else completes their leaving you with a lower qty
        - making another offer, but in the meantime somebody else completes their leaving you with a zero qty
        - (restores the quantities and allows user to make initial second offer)
        - checks that the offers register in offers log
        - checks that the filter out "offered" check box works in the offers log
        - checks that the offer can be marked sold
        - checks that the filter out "sold" check box works in the offers log
        - checks that the offer is registered correctly as sold in the offersLog model in the database
        - check that the sold quantity is correctly deduced from AvailableStock model in the database
        - check that the sold quantity is deducted and the remaining qty displays correctly in the all stocks page
        - check that the sold quantity registers correctly in the all stocks page
        - check that filtering by sold works correctly in the all stocks page
        - checks that the offer can be changed
        - checks that the changed offer is registered correctly in the offersLog model in the database
        - check that the changed quantity is correctly recorder in AvailableStock model in the database
        - check that the changed quantity is adjusted and the remaining qty displays correctly in the all stocks page
        - checks that the offer can be marked as declined
        - checks that the filter out "declined" check box works in the offers log
        - checks that the offer is registered correctly as declined in the offersLog model in the database
        - check that the declined quantity is correctly adjusted in AvailableStock model in the database
        - check that the declined quantity is restored and the remaining qty displays correctly in the all stocks page
        - check that the declined quantity registers correctly in the all stocks page
        - tests changing the offered quantity, but someone removes the value before the form is submitted

        """

        # Morgan logs in her account
        self.log_in_account('Morgan', 'password123')
        # and she is greeted by 2 buttons
        self.assertEqual(len(self.browser.find_elements(By.CLASS_NAME, 'a_menu')), 2)
        # she clicks on the button taking her to the available products pages
        self.browser.find_element(By.LINK_TEXT, 'Sell some stuff 🡢').click()

        # she sees a product - MIS-019-865, and she wants to offer it to a client, so she clicks the "Make offer" button
        self.browser.find_element(By.XPATH, "//tr[td[text()='MIS-019-865']]//a[@class='a_menu_make_offer']").click()
        # she lands on a page announcing her that she is about to make an offer for the MIS-019-865 product
        self.assertEqual(self.browser.find_element(By.CLASS_NAME, 'table_customer').text, 'MIS-019-865')
        # she notices all her customers are in the drop-down, so she checks a few
        customers = self.browser.find_elements(By.CLASS_NAME, 'input_offer')
        customers_list = [customer.text for customer in customers]
        self.assertTrue('Reliable Ventures Real Estate Ltd.' in customers_list)
        self.assertTrue('Advanced Analytics Agriculture Ltd.' in customers_list)
        self.assertTrue('Zesty Grains' in customers_list)
        # she also looks for some of her colleagues customers to make sure they are NOT in there
        self.assertFalse('Decadent Cocoa Fantasies' in customers_list)
        self.assertFalse('Rapid Foods Development Ltd.' in customers_list)
        self.assertFalse('Urban Utilities Healthcare Ltd.' in customers_list)

        # she makes an offer to one of her customers
        self.make_offer('Creamy Cocoa Bites', '100', '1', '1', self.my_offer_date())
        # click the button to make the offer
        self.browser.find_element(By.NAME, 'postOne').click()

        # she checks that the offer was submitted to the database
        self.assertEqual(OffersLog.objects.count(), 1)
        stock = OffersLog.objects.all()[0]
        self.assertEqual(stock.sales_rep_that_made_the_offer, User.objects.filter(first_name='Morgan',
                                                                                  last_name='Davis').get())
        self.assertEqual(stock.offered_stock,
                         AvailableStock.objects.filter(available_product=Products.objects.filter(cod_material='MIS-019-865').get()).get())
        self.assertEqual(stock.offered_product, Products.objects.filter(cod_material='MIS-019-865').get())
        self.assertEqual(stock.customer_that_received_offer, Customers.objects.filter(customer_name='Creamy Cocoa Bites').get())
        self.assertEqual(stock.offered_sold_or_declined_quantity_kg, 100)
        self.assertEqual(stock.offer_status, 'Offered')
        self.assertEqual(stock.discount_offered_percents, 1.00)
        self.assertEqual(stock.price_per_kg_offered, 1.00)
        self.assertEqual(stock.date_of_offer, datetime.date(2024, 5, 28))
        self.assertEqual(stock.expiration_date_of_offer, datetime.date(2024, 6, 4))
        self.assertEqual(stock.date_of_outcome, None)
        self.assertEqual(stock.stock_expired, False)

        # she is redirected to a page with the title "Great job!"
        self.assertEqual(self.browser.title, "Great job!")
        # she wants a pdf copy of the offer, so she requests one
        self.browser.find_element(By.ID, 'getPdf').click()
        existing_file_name = os.listdir(self.download_dir)[0]
        expected_file_name = 'MIS-019-865-FOR-Creamy Cocoa Bites.pdf'
        # she checks the name of the file to be the right one
        self.assertTrue(existing_file_name, expected_file_name)
        # she checks the content of the file
        reader = PyPDF2.PdfReader(f'{self.download_dir}/{existing_file_name}')
        page = reader.pages[0]
        text = page.extract_text()
        # she checks that the date of the offer is the right one
        self.assertIn(f'Date of offer: {stock.date_of_offer.strftime("%d-%m-%Y")}', text)
        # she checks that the expiration date is the right one
        self.assertIn(f'Offer expiration date: {stock.expiration_date_of_offer.strftime("%d-%m-%Y")}', text)
        # she checks that the offer is addressed to the right customer
        self.assertIn(f'To: {stock.customer_that_received_offer.customer_name}', text)
        # she checks offered price is the correct one
        self.assertIn(f'Price/kg: £{stock.price_per_kg_offered}', text)
        # she checks offered quantity is the correct one
        self.assertIn(f' to offer you {stock.offered_sold_or_declined_quantity_kg}kg', text)
        # she checks that the offered product is the correct one
        self.assertIn('MIS-019-865', text)
        # finally she checks that customer care agent is the correct one
        self.assertIn(f'Customer care agent: {Customers.objects.filter(customer_name="Creamy Cocoa Bites").get().allocated_customer_service_rep.customer_service_rep}', text)

        ## delete file
        os.remove(os.path.abspath(f'{self.download_dir}/{existing_file_name}'))

        # happy with the result she goes back to the aged stock products to check that the offered 100 kg were deducted
        # from the available quantity and the available vas reduced to 62 kg
        self.browser.find_element(By.LINK_TEXT, 'Let me try another one').click()
        self.assertTrue(self.browser.find_element(By.XPATH, "//tr[td[text()='MIS-019-865']]//td[text()='62 kg']"))

        # she opens the filters area
        self.browser.find_element(By.ID, 'p_filter_message').click()
        # she un ticks the "under offer" tick-box
        self.browser.find_element(By.ID, 'underOfferCB').click()
        # now she can see the offer that she made appearing as a separate line
        ## I am removing the zeros from day and month so 04 becomes 4
        exp_date = f'{stock.expiration_date_of_offer.strftime("%B")} {stock.expiration_date_of_offer.day}, {stock.expiration_date_of_offer.year}'
        expiration_column = f" Under offer by {stock.sales_rep_that_made_the_offer} expires: {exp_date} "
        ## this creates a query that looks for the table row that condais 3 <td> elements.
        ## each with the correct text data
        #  and ;  and td[text()='Under offer by Morgan expires: June 4, 2024']
        xpath = (
            f"//tr[@class='tr_offered' and td[text()='MIS-019-865'] and td[text()='100 kg'] and td[text()='{expiration_column}']]"
        )
        self.assertTrue(self.browser.find_element(By.XPATH, xpath))

        # she sees another stock, COM-008-310, 300kg available, and she wants to offer 200kg of it to another customer
        # she clicks on the button to make the offer
        self.browser.find_element(By.XPATH, "//tr[td[text()='COM-008-310']]//a[@class='a_menu_make_offer']").click()
        self.make_offer('Advanced Orchards Finance Ltd.', '200', '2', '1', self.my_offer_date())

        # she sees that the form automatically caps her at the maximum available quantity, 300kg
        self.assertIn('300kg available', self.browser.find_elements(By.CLASS_NAME, 'label_input')[1].text)
        self.assertEqual(self.browser.find_element(By.NAME, 'quantity').get_attribute('max'), '300')

        # however, before she gets to place the order, her colleague offers 200 out of the 300 kg to one of his
        # customers
        ## we will simulate this by directly decreasing the available stock by 200kg from the available quantity,
        ## without an offer
        my_stock = AvailableStock.objects.filter(available_product=Products.objects.filter(cod_material='COM-008-310').get()).get()
        my_stock.available_quantity_in_kg -= 200
        my_stock.save()

        #she clicks the button to make the offer
        self.browser.find_element(By.NAME, 'postOne').click()
        # she notices she is redirected to a page with the title "Not enough stock"
        self.assertEqual(self.browser.title, 'Not enough stock')
        # she is meet by an announcement that there is not enough stock available because someone already
        # offered some of it to someone else
        self.assertEqual(self.browser.find_elements(By.CLASS_NAME, 'p_menu')[1].text,
                         "Seems like someone beat you to it, and there isn't enough stock left.")
        # she is told that the remaining quantity is 100kg
        self.assertEqual(self.browser.find_element(By.ID, 'id_available_qty').text,
                         "100kg")
        # she is presented with three buttons
        self.assertEqual(len(self.browser.find_elements(By.CLASS_NAME, 'a_menu')), 3)
        # and she decides to remake the offer, so she clicks on the "Remake offer" button
        self.browser.find_element(By.LINK_TEXT, 'Remake offer').click()
        # she is met with the form that registers the offer, for the same product
        self.assertEqual(self.browser.find_elements(By.CLASS_NAME, 'p_menu')[1].text,
                         'You are about to make an offer for: COM-008-310')
        self.assertEqual(self.browser.find_element(By.CLASS_NAME, 'table_customer').text, 'COM-008-310')
        # she also sees that the available quantity is 100kg, and the system limits it to 100kg
        self.assertIn('100kg available', self.browser.find_elements(By.CLASS_NAME, 'label_input')[1].text)
        self.assertEqual(self.browser.find_element(By.NAME, 'quantity').get_attribute('max'), '100')

        # she makes the offer for the remaining 100kg quantity
        self.make_offer('Advanced Orchards Finance Ltd.', '100', '2', '1', self.my_offer_date())
        # however, before she gets to place the order, her colleague offers the remaining 100 kg
        ## we will simulate this by directly decreasing the available stock to zero, without an offer
        my_stock = AvailableStock.objects.filter(available_product=Products.objects.filter(
            cod_material='COM-008-310').get()).get()
        my_stock.available_quantity_in_kg = 0
        my_stock.save()
        #she clicks the button to make the offer
        self.browser.find_element(By.NAME, 'postOne').click()
        # she notices she is redirected to a page with the title "Not enough stock"
        self.assertEqual(self.browser.title, 'Not enough stock')
        # she is meet by an announcement that there is not enough stock available because someone already
        # offered all of it to someone else
        self.assertEqual(self.browser.find_elements(By.CLASS_NAME, 'p_menu')[1].text,
                         "Seems like someone beat you to it, and there isn't enough stock left.")
        # she is told that the remaining quantity is 0kg
        self.assertEqual(self.browser.find_element(By.ID, 'id_zero_stock_left').text,
                         "There are 0kg left")

        # this time she is presented with only 2 buttons instead of 3 - she no longer has the option to offer the stock
        self.assertEqual(len(self.browser.find_elements(By.CLASS_NAME, 'a_menu')), 2)

        ## for good measure let's restore the quantity to it's original value
        my_stock = AvailableStock.objects.filter(available_product=Products.objects.filter(
            cod_material='COM-008-310').get()).get()
        my_stock.available_quantity_in_kg = 300
        my_stock.save()
        ## and let Morgan go through with the original offer of 200 kg
        self.browser.find_elements(By.CLASS_NAME, 'a_menu')[0].click()
        self.browser.find_element(By.XPATH, "//tr[td[text()='COM-008-310']]//a[@class='a_menu_make_offer']").click()
        self.make_offer('Advanced Orchards Finance Ltd.', '200', '2', '1', self.my_offer_date())
        # she clicks the button to make the offer
        self.browser.find_element(By.NAME, 'postOne').click()

        # she is redirected to a page with the title "Great job!"
        self.assertEqual(self.browser.title, "Great job!")

        # she navigates home
        self.browser.find_element(By.LINK_TEXT, 'I know! (home)').click()
        # and then she navigates to the pending offers page
        self.browser.find_element(By.LINK_TEXT, 'See "My offers" log 🡢').click()
        # she opens the filters section
        self.browser.find_element(By.ID, 'p_filter_message').click()
        # she clicks on the "hide Offered" tick box, and she checks that the line of the sold is now hidden
        self.browser.find_element(By.ID, 'Offered').click()
        # and she checks the offers are no longer there
        for element in self.browser.find_elements(By.CLASS_NAME, 'Offered'):
            self.assertIn(element.get_attribute('style'), 'visibility: collapse;')
        # she unticks the offered checkbox
        self.browser.find_element(By.ID, 'Offered').click()
        # she checks that the 2 offers she made are there
        offers = self.browser.find_elements(By.CLASS_NAME, 'Offered')
        self.assertEqual(len(offers), 2)
        # she checks that the first offer is for the MIS-019-865 material
        first_offer_data_td = offers[0].find_elements(By.TAG_NAME, 'td')
        self.assertEqual(first_offer_data_td[0].text, 'MIS-019-865')
        # she checks that the customer is Creamy Cocoa Bites
        self.assertEqual(first_offer_data_td[1].text, 'Creamy Cocoa Bites')
        # she checks that offer was made for 100kg
        self.assertEqual(first_offer_data_td[2].text, '100')
        # she checks that the discount applied is 1.00%
        self.assertEqual(first_offer_data_td[3].text, '1.00')
        # she checks that the price per kilo is 1.00
        self.assertEqual(first_offer_data_td[4].text, '1.00')
        # she checks that the date of the offer is correct May 28, 2024
        self.assertEqual(first_offer_data_td[5].text, 'May 28, 2024')
        # and she checks that the expiration date is correct June 4, 2024
        self.assertEqual(first_offer_data_td[6].text, 'June 4, 2024')
        # she checks that the date of the outcome is None
        self.assertEqual(first_offer_data_td[7].text, 'None')
        # she also checks that the offer is rightfully labeled as offered
        self.assertEqual(first_offer_data_td[8].text, 'Offered')

        # she receives news that the customer accepts the offer, so she wishes to change the offer to "sold"
        # she clicks on the "change offer" button
        first_offer_data_td[9].find_element(By.TAG_NAME, 'a').click()
        # and lands on a page with the title "Change offer status"
        self.assertEqual(self.browser.title, 'Change offer status')
        # on the page she sees four buttons
        self.assertEqual(len(self.browser.find_elements(By.TAG_NAME, 'button')), 4)
        # and she clicks on the one that changes the offer to sold
        self.browser.find_element(By.NAME, 'sold').click()
        # and she is returned to the page with her reports, and now the MIS-019-865 offer is changed to sold
        sold_tag_details = self.browser.find_element(By.CLASS_NAME, 'Sold').find_elements(By.TAG_NAME, 'td')
        self.assertEqual(sold_tag_details[0].text, 'MIS-019-865')
        today_date_right_string_format = f'{datetime.datetime.today().date().strftime("%B")} {datetime.datetime.today().date().day}, {datetime.datetime.today().date().year}'
        self.assertEqual(sold_tag_details[7].text, today_date_right_string_format)
        self.assertEqual(sold_tag_details[8].text, 'Sold')
        # she opens the filters section
        self.browser.find_element(By.ID, 'p_filter_message').click()
        # she clicks on the "hide sold" tick box, and she checks that the line of the sold is now hidden
        self.browser.find_element(By.ID, 'Sold').click()
        for element in self.browser.find_elements(By.CLASS_NAME, 'Sold'):
            self.assertIn(element.get_attribute('style'), 'visibility: collapse;')

        # she checks the database to see that the offered quantity instance is marked as sold
        stock = OffersLog.objects.filter(offered_stock=AvailableStock.objects.filter(
            available_product=Products.objects.filter(cod_material='MIS-019-865').get()).get(),
            customer_that_received_offer=Customers.objects.filter(customer_name='Creamy Cocoa Bites').get()).get()
        self.assertEqual(stock.offered_sold_or_declined_quantity_kg, 100)
        self.assertEqual(stock.offer_status, 'Sold')
        self.assertEqual(stock.date_of_outcome, datetime.datetime.today().date())

        # she checks the database to see that the sold quantity is correctly deduced from the total available stock
        available_stock = AvailableStock.objects.filter(
            available_product=Products.objects.filter(cod_material='MIS-019-865').get()).get()
        self.assertEqual(available_stock.original_quantity_in_kg, 162)
        self.assertEqual(available_stock.under_offer_quantity_in_kg, 0)
        self.assertEqual(available_stock.sold_quantity_in_kg, 100)
        self.assertEqual(available_stock.available_quantity_in_kg, 62)

        # she navigates to the main "all stock" page, and she checks that the remaining quantity of 62 kfg is
        # displayed correctly
        self.browser.find_element(By.LINK_TEXT, 'Back to available stock').click()
        xpath = "//tr[td[text()='MIS-019-865'] and td[text()='62 kg']]"
        self.assertTrue(self.browser.find_element(By.XPATH, xpath))
        # she checks that the "sold" filter works on "all stock" page
        self.browser.find_element(By.ID, 'p_filter_message').click()
        # she checks that the correct quantity is registered as sold
        xpath = "//tr[td[text()='MIS-019-865'] and td[text()='100 kg'] and td[text()=' Sold by Morgan ']]"
        self.assertTrue(self.browser.find_element(By.XPATH, xpath))

        # she is contacted by the customer for the other offer and the customer ask her to re-do the offer for 150kg
        # and asks for a lower price
        # she goes back to the offers screen, and she changes the existing offer to 150 kg 2.5% discount and a price per
        # kg of 1,5
        self.browser.find_element(By.LINK_TEXT, 'My offers').click()
        xpath = "//tr[td[text()='COM-008-310']]//a[@class='a_menu_make_offer']"
        self.browser.find_element(By.XPATH, xpath).click()
        self.browser.find_element(By.NAME, 'changeOfferRedirect').click()
        self.make_offer('Advanced Orchards Finance Ltd.', '150', '2.50', '1.50', self.my_offer_date())
        self.browser.find_element(By.CLASS_NAME, 'input_form_submit_offer').click()

        # she lands on the order confirmation page
        self.assertEqual(self.browser.title, 'Great job!')

        # and she navigates to the offers log page
        self.browser.find_element(By.LINK_TEXT, 'My offers').click()

        # she checks that the new offer registered correctly on the offers log (pending offers) page
        self.assertEqual(self.browser.title, 'Pending offers')
        offers = self.browser.find_elements(By.CLASS_NAME, 'Offered')
        self.assertEqual(len(offers), 1)
        # she checks that the first offer is for the COM-008-310 material (should be the only one offered)
        first_offer_data_td = offers[0].find_elements(By.TAG_NAME, 'td')
        self.assertEqual(first_offer_data_td[0].text, 'COM-008-310')
        # she checks that the customer is CAdvanced Orchards Finance Ltd.
        self.assertEqual(first_offer_data_td[1].text, 'Advanced Orchards Finance Ltd.')
        # she checks that offer was made for 150kg
        self.assertEqual(first_offer_data_td[2].text, '150')
        # she checks that the discount applied is 2.50%
        self.assertEqual(first_offer_data_td[3].text, '2.50')
        # she checks that the price per kilo is 1.50
        self.assertEqual(first_offer_data_td[4].text, '1.50')
        # she also checks that the offer is rightfully labeled as offered
        self.assertEqual(first_offer_data_td[8].text, 'Offered')

        # she checks that the offer is registered correctly on the OffersLog database
        stock = OffersLog.objects.filter(offered_stock=AvailableStock.objects.filter(
            available_product=Products.objects.filter(cod_material='COM-008-310').get()).get(),
            customer_that_received_offer=Customers.objects.filter(customer_name="Advanced Orchards Finance Ltd.").get()).get()
        self.assertEqual(stock.offered_sold_or_declined_quantity_kg, 150)
        self.assertEqual(stock.offer_status, 'Offered')

        # she checks that the quantities are correctly displayed in the available stock
        available_stock = AvailableStock.objects.filter(
            available_product=Products.objects.filter(cod_material='COM-008-310').get()).get()
        self.assertEqual(available_stock.original_quantity_in_kg, 300)
        self.assertEqual(available_stock.under_offer_quantity_in_kg, 150)
        self.assertEqual(available_stock.sold_quantity_in_kg, 0)
        self.assertEqual(available_stock.available_quantity_in_kg, 150)

        # the customer declines the offer, so she marks it as declined
        # she clicks the button to change the offer
        xpath = "//tr[td[text()='COM-008-310']]//a[@class='a_menu_make_offer']"
        self.browser.find_element(By.XPATH, xpath).click()
        # she checks she is on the right page
        self.assertEqual(self.browser.title, 'Change offer status')
        self.browser.find_element(By.NAME, 'declined').click()

        # she checks that the declined offer appears as declined in the offers log page
        xpath = "//tr[td[text()='COM-008-310'] and td[text()='150'] and td[text()='Declined']]"
        self.assertTrue(self.browser.find_element(By.XPATH, xpath))

        # she checks that the filter for hiding declined offers functions correctly
        self.browser.find_element(By.ID, 'p_filter_message').click()
        self.browser.find_element(By.ID, 'Declined').click()
        for element in self.browser.find_elements(By.CLASS_NAME, 'Declined'):
            self.assertIn(element.get_attribute('style'), 'visibility: collapse;')

        # she checks that the quantity is restored to the original quantity on the all available stocks page
        self.browser.find_element(By.LINK_TEXT, 'Back to available stock').click()
        xpath = "//tr[td[text()='COM-008-310'] and td[text()='300 kg']]"
        self.assertTrue(self.browser.find_element(By.XPATH, xpath))

        # she checks that the offer is correctly marked in the offers log database
        stock = OffersLog.objects.filter(offered_stock=AvailableStock.objects.filter(
            available_product=Products.objects.filter(cod_material='COM-008-310').get()).get(),
            customer_that_received_offer=Customers.objects.filter(customer_name="Advanced Orchards Finance Ltd.").get()).get()
        self.assertEqual(stock.offered_sold_or_declined_quantity_kg, 150)
        self.assertEqual(stock.offer_status, 'Declined')

        # she checks that the offer is correctly marked in the Available stock database
        available_stock = AvailableStock.objects.filter(
            available_product=Products.objects.filter(cod_material='COM-008-310').get()).get()
        self.assertEqual(available_stock.original_quantity_in_kg, 300)
        self.assertEqual(available_stock.under_offer_quantity_in_kg, 0)
        self.assertEqual(available_stock.sold_quantity_in_kg, 0)
        self.assertEqual(available_stock.available_quantity_in_kg, 300)

        # she goes and makes another offer for 230kg of the product FIL-002-400 which has 255kg available
        self.browser.find_element(By.XPATH, "//tr[td[text()='FIL-002-400']]//a[@class='a_menu_make_offer']").click()
        self.make_offer('Decadent Cocoa Bars', '230', '1', '1', self.my_offer_date())
        self.browser.find_element(By.NAME, 'postOne').click()

        # the customer contacts her to ask for 10 kg more
        # so she goes to offers to change the offer
        self.browser.find_element(By.LINK_TEXT, 'My offers').click()
        xpath = "//tr[td[text()='FIL-002-400']]//a[@class='a_menu_make_offer']"
        self.browser.find_element(By.XPATH, xpath).click()
        self.browser.find_element(By.NAME, 'changeOfferRedirect').click()
        self.make_offer('Decadent Cocoa Bars', '240', '1', '1', self.my_offer_date())

        # however a colleague swoops in and offers 21kg to someone else, and she is left with 4kg, 6kg short
        # of what she needs
        my_stock = AvailableStock.objects.filter(available_product=Products.objects.filter(
            cod_material='FIL-002-400').get()).get()
        my_stock.available_quantity_in_kg -= 21
        my_stock.save()
        # she is met by a message informing her someone beat her to it
        self.browser.find_element(By.CLASS_NAME, 'input_form_submit_offer').click()
        self.assertIn('It seems like someone beat you to it, and there is not enough stock left to increase the offered',
                      self.browser.find_element(By.ID, 'id_message').text)
        # there are only 4kg left, so a total quantity available should be 230kg from the original offer +4kg so 234 kg
        self.assertEqual(self.browser.find_element(By.ID, 'total_left_quantity').text, '234kg')


class SuperUserSalespeopleCheck(StaticLiveServerTestCase, MixinFunctions):
    def setUp(self) -> None:
        """
        Creates the webdriver object
        Creates 2 superuser accounts, one is Mikimic
        Uploads the customer and stocks files that populate the database
        Creates 2 sales accounts
        For each sales account creates one offer that is sold, one declined and one under offer
        Runs the filter tests on the reports page
        """
        # Initialize the Firefox WebDriver with the specified profile
        self.browser = webdriver.Firefox()
        self.browser.implicitly_wait(10)
        # Admin has an account
        self.create_account('Miki', 'Mic')
        # He creates one account for Morgan who is a salesperson
        self.create_account('Morgan', 'Davis', False)
        # He creates another account for Alex who is a salesperson
        self.create_account('Alex', 'Martinez', False)
        # And one account for Quinn who is a manager
        self.create_account('Quinn', 'Miller')

        # he uploads the xlsx files in the database
        self.admin_uploads_salespeople_and_aged_stock_xlsx_to_db('aged/lab/DataSafeOnes/18_just_three_sales_people.xlsx',
                                                                 'aged/lab/DataSafeOnes/01_good_AgedStock.xlsx')
        # Morgan logs in her account
        self.log_in_account('Morgan', 'password123')

        # she navigates to her account, and she makes an offer for 100kg MIS-019-865
        self.browser.find_element(By.LINK_TEXT, 'Sell some stuff 🡢').click()
        self.browser.find_element(By.XPATH, "//tr[td[text()='MIS-019-865']]//a[@class='a_menu_make_offer']").click()
        self.make_offer('Creamy Cocoa Bites', '100', '1', '1', self.my_offer_date())
        # click the button to make the offer
        self.browser.find_element(By.NAME, 'postOne').click()

        # the offer is accepted, so she marks it sold
        self.browser.find_element(By.LINK_TEXT, 'My offers').click()
        self.browser.find_element(By.XPATH, "//tr[td[text()='MIS-019-865']]//a[@class='a_menu_make_offer']").click()
        self.browser.find_element(By.NAME, 'sold').click()

        # she goes back to make another offer
        self.browser.find_element(By.LINK_TEXT, 'Available stock').click()
        self.browser.find_element(By.XPATH, "//tr[td[text()='COM-008-310']]//a[@class='a_menu_make_offer']").click()
        self.make_offer('Advanced Orchards Finance Ltd.', '200', '2', '1', self.my_offer_date())
        # she clicks the button to make the offer
        self.browser.find_element(By.NAME, 'postOne').click()

        # the offer is rejected so she marks it declined
        self.browser.find_element(By.LINK_TEXT, 'My offers').click()
        self.browser.find_element(By.XPATH, "//tr[td[text()='COM-008-310']]//a[@class='a_menu_make_offer']").click()
        self.browser.find_element(By.NAME, 'declined').click()

        # she goes back and makes another offer
        self.browser.find_element(By.LINK_TEXT, 'Available stock').click()
        self.browser.find_element(By.XPATH, "//tr[td[text()='FIL-002-400']]//a[@class='a_menu_make_offer']").click()
        self.make_offer('Fine Herbs', '25', '2.5', '1.5', self.my_offer_date())
        # she clicks the button to make the offer
        self.browser.find_element(By.NAME, 'postOne').click()

        # Alex logs in his account
        self.log_in_account('Alex', 'password123')

        # he navigates to her account, and she makes an offer for 75kg MIS-006-402
        self.browser.find_element(By.LINK_TEXT, 'Sell some stuff 🡢').click()
        self.browser.find_element(By.XPATH, "//tr[td[text()='MIS-006-402']]//a[@class='a_menu_make_offer']").click()
        self.make_offer('Decadent Chocolate Treats', '75', '1', '2', self.my_offer_date())
        # click the button to make the offer
        self.browser.find_element(By.NAME, 'postOne').click()

        # the offer is accepted, so he marks it sold
        self.browser.find_element(By.LINK_TEXT, 'My offers').click()
        self.browser.find_element(By.XPATH, "//tr[td[text()='MIS-006-402']]//a[@class='a_menu_make_offer']").click()
        self.browser.find_element(By.NAME, 'sold').click()

        # he goes back to make another offer
        self.browser.find_element(By.LINK_TEXT, 'Available stock').click()
        self.browser.find_element(By.XPATH, "//tr[td[text()='VEN-002-873']]//a[@class='a_menu_make_offer']").click()
        self.make_offer('Polar Resources Industries Ltd.', '2', '5', '10', self.my_offer_date(False))
        self.browser.find_element(By.NAME, 'postOne').click()

        # the offer is rejected so he marks it declined
        self.browser.find_element(By.LINK_TEXT, 'My offers').click()
        self.browser.find_element(By.XPATH, "//tr[td[text()='VEN-002-873']]//a[@class='a_menu_make_offer']").click()
        self.browser.find_element(By.NAME, 'declined').click()

        # he goes back and makes another offer
        self.browser.find_element(By.LINK_TEXT, 'Available stock').click()
        self.browser.find_element(By.XPATH, "//tr[td[text()='COM-005-872']]//a[@class='a_menu_make_offer']").click()
        self.make_offer('Vital Supplies Engineering Ltd.', '100', '1.5', '1.5', self.my_offer_date(False))
        # she clicks the button to make the offer
        self.browser.find_element(By.NAME, 'postOne').click()

    def tearDown(self) -> None:  # This code runs once AFTER EACH test
        self.browser.quit()  # quits firefox

    def test_manager_checks_reports(self):
        # Quinn logs in into his account - he is a manager
        self.log_in_account('Quinn', 'password123')

        # He navigates to its reports page - only available to superusers - the page title is Reports
        self.browser.find_element(By.LINK_TEXT, 'Reports').click()
        self.assertEqual(self.browser.title, 'Reports')
        # he is meet by a page that displays 6 rows of data, showing the activity of his sales people
        self.assertEqual(len(self.browser.find_elements(By.TAG_NAME, 'tr')), 7)  # one table row is for table headers
        # he sees that he has an option to filter out his by salesperson, or to see them all
        # He opts to see only Morgan's activity
        select_element = self.browser.find_element(By.NAME, 'nameOfUser')
        select = Select(select_element)
        select.select_by_visible_text('Morgan')
        self.browser.find_element(By.CLASS_NAME, 'input_submit_superuser_form').click()
        # and now he only sees 3 table rows
        self.assertEqual(len(self.browser.find_elements(By.TAG_NAME, 'tr')), 4)  # one table row is for table headers
        # he checks that they all belong to Morgan
        table_rows = self.browser.find_elements(By.TAG_NAME, 'tr')
        for row in table_rows[1:]:
            self.assertEqual(row.find_elements(By.TAG_NAME, 'td')[0].text, 'Morgan')

        # he sees that he has another filter available to him, that shows him the activity by offer status
        # he decides to check what offers Morgan hs that are under offer
        select_element = self.browser.find_element(By.NAME, 'offerStatus')
        select = Select(select_element)
        select.select_by_visible_text('Offered')
        self.browser.find_element(By.CLASS_NAME, 'input_submit_superuser_form').click()
        # and now he only sees 1 table row
        self.assertEqual(len(self.browser.find_elements(By.TAG_NAME, 'tr')), 2) # one is with the table header
        # he checks that the data belongs to Morgan and the status is under offer
        table_rows = self.browser.find_elements(By.TAG_NAME, 'tr')
        for row in table_rows[1:]:
            self.assertEqual(row.find_element(By.CLASS_NAME, 'table_sales_rep').text, 'Morgan')
            self.assertEqual(row.find_element(By.CLASS_NAME, 'table_status_offered').text, 'Offered')

        # he goes to the salesperson filter and decides to see all under offer offers, no matter who made them
        select_element = self.browser.find_element(By.NAME, 'nameOfUser')
        select = Select(select_element)
        select.select_by_visible_text('All')
        self.browser.find_element(By.CLASS_NAME, 'input_submit_superuser_form').click()
        # he now sees that there are 2 rows available to him
        self.assertEqual(len(self.browser.find_elements(By.TAG_NAME, 'tr')), 3)  # one is with the table header
        # he looks at the third filter, and selects only under offer offers made between the 28th and 29th of May
        # he selects the date of 28 May for the start date
        start_date_filter_field = self.browser.find_element(By.ID, 'start')
        start_date = '2024-05-28'
        start_date_filter_field.clear()
        start_date_filter_field.send_keys(start_date)

        # he selects the date of 29 May for the start date
        end_date_filter_field = self.browser.find_element(By.ID, 'stop')
        end_date = '2024-05-29'
        end_date_filter_field.clear()
        end_date_filter_field.send_keys(end_date)

        # he presses the search button
        self.browser.find_element(By.CLASS_NAME, 'input_submit_superuser_form').click()
        # he now sees only one person in the list
        self.assertEqual(len(self.browser.find_elements(By.TAG_NAME, 'tr')), 2)  # one is with the table header
        # he checks that the offer is made by Morgan, is offered and the offer date is the 28th of May
        table_rows = self.browser.find_elements(By.TAG_NAME, 'tr')
        for row in table_rows[1:]:
            self.assertEqual(row.find_element(By.CLASS_NAME, 'table_sales_rep').text, 'Morgan')
            self.assertEqual(row.find_element(By.CLASS_NAME, 'table_status_offered').text, 'Offered')
            self.assertEqual(row.find_elements(By.TAG_NAME, 'td')[7].text, 'May 28, 2024')

class AutomatedTasksCheck(StaticLiveServerTestCase, MixinFunctions):
    # Mikimic, as a superuser, had set up a page that can be accessed by a bot account
    def setUp(self) -> None:
        self.browser = webdriver.Firefox()
        self.browser.implicitly_wait(10)
        # he creates an account for himeslf
        self.create_account('Miki', 'Mic')
        # and he creates an account for the bot that has to be named Testbot
        self.create_account('Testbot', 'Bot')
        # he creates the other accounts required in order to be able to upload his salespeople file
        self.create_account('Morgan', 'Davis', False)
        self.create_account('Alex', 'Martinez', False)
        self.create_account('Quinn', 'Miller')

        # he uploads the xlsx files in the database
        self.admin_uploads_salespeople_and_aged_stock_xlsx_to_db('aged/lab/DataSafeOnes/18_just_three_sales_people.xlsx',
                                                                 'aged/lab/DataSafeOnes/01_good_AgedStock.xlsx')
        # he also keeps the xlsx handy
        self.aged_stock_xlsx_dataframe = self.return_xlsx_dataframe('aged/lab/DataSafeOnes/01_good_AgedStock.xlsx')


    def tearDown(self) -> None:
        self.browser.quit()

    def test_expired_offers_are_removed(self):
        pass



























