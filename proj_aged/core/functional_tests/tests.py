from django.contrib.staticfiles.testing import StaticLiveServerTestCase # this a  class provided by Django for tests
from selenium import webdriver
from aged.models import AvailableStock, Products, LocationsForStocks, CheckIfFileWasAlreadyUploaded, Brands
from aged.lab.Aged_stock import date_to_string_or_string_to_date
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from django.contrib.auth.models import User
from selenium.webdriver.common.keys import Keys
import os
import pandas as pd

# Morgan - a salesperson in the UK department heard about this cool app that was designed by a colleague
# to help the sales people better manage their aged stock
class LoginIsRequired(StaticLiveServerTestCase):
    def setUp(self) -> None:  # This code runs once BEFORE EACH test
        self.browser = webdriver.Firefox() # starts firefox
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

class AdminUploadsSpreadsheetTest(StaticLiveServerTestCase):
    def setUp(self) -> None:  # This code runs once BEFORE EACH test
        self.browser = webdriver.Firefox() # starts firefox
        # Admin creates a superuser for himself (needs to be Mikimic)
        self.superuser = User.objects.create_superuser(
            username='Mikimic',
            password='adminpassword',
            email='admin@example.com'
        )



    def tearDown(self) -> None:  # This code runs once AFTER EACH test
        self.browser.quit()  # quits firefox

    # And logs into his acocunt - which differs from anyone else's because it has an "Upload Files ->" button
    def test_log_in_and_customer_file_upload_for_admin(self):
        self.browser.get(self.live_server_url)
        username_input = self.browser.find_element(By.ID, 'id_username')
        username_input.send_keys('Mikimic')
        password_input = self.browser.find_element(By.ID, 'id_password')
        password_input.send_keys('adminpassword')
        self.browser.find_element(By.CLASS_NAME, 'input_form_submit').click()
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
        # he goes back and tries again
        self.browser.find_element(By.CLASS_NAME, 'a_menu').click()
        self.browser.find_element(By.LINK_TEXT, '(1) Salespeople, customer care agents and customers').click()
        # but this time he uploads a file that holds an empty spreadsheet
        xlsx_upload_field = self.browser.find_element(By.ID, 'id_file_field')
        wrong_relative_path = 'aged/lab/DataSafeOnes/9_blank_file.xlsx'
        wrong_absolute_file_path = os.path.abspath(wrong_relative_path)
        xlsx_upload_field.send_keys(wrong_absolute_file_path)
        self.browser.find_element(By.ID, 'id_submit_file').click()
        # and this time the error message is different
        self.assertEqual(self.browser.find_element(By.ID, 'upload_status').text,
                         'The file has no data. Fix file and re-upload')
        # he goes back and tries again
        self.browser.find_element(By.CLASS_NAME, 'a_menu').click()
        self.browser.find_element(By.LINK_TEXT, '(1) Salespeople, customer care agents and customers').click()
        # this time he uploads an older file that does not contain the right headers
        xlsx_upload_field = self.browser.find_element(By.ID, 'id_file_field')
        wrong_relative_path = 'aged/lab/DataSafeOnes/10_wrong_headers.xlsx'
        wrong_absolute_file_path = os.path.abspath(wrong_relative_path)
        xlsx_upload_field.send_keys(wrong_absolute_file_path)
        self.browser.find_element(By.ID, 'id_submit_file').click()
        # and this time the error message is different - telling him about the wrong headers
        self.assertTrue(self.browser.find_element(By.ID, 'upload_status').text.startswith("The file has the wrong headers."))

        # TODO: test create_customer_care_accounts function
        # TODO: finish create_customer_accounts function

    # the admin goes to upload the aged stock file
    def test_log_in_and_stock_file_upload_for_admin(self):
        # he logs in to his account
        self.browser.get(self.live_server_url)
        username_input = self.browser.find_element(By.ID, 'id_username')
        username_input.send_keys('Mikimic')
        password_input = self.browser.find_element(By.ID, 'id_password')
        password_input.send_keys('adminpassword')
        self.browser.find_element(By.CLASS_NAME, 'input_form_submit').click()
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
        # he goes back
        self.browser.find_element(By.CLASS_NAME, 'a_menu').click()
        self.browser.find_element(By.LINK_TEXT, '(3) Aged stock').click()
        # he tries again, this time uploading a blank file
        xlsx_upload_field = self.browser.find_element(By.ID, 'id_file_field')
        wrong_relative_path = 'aged/lab/DataSafeOnes/03_wrong_AgedStock_no_data.xlsx'
        wrong_absolute_file_path = os.path.abspath(wrong_relative_path)
        xlsx_upload_field.send_keys(wrong_absolute_file_path)
        self.browser.find_element(By.ID, 'id_submit_file').click()
        # and he is meet by an error message
        self.assertEqual(self.browser.find_element(By.ID, 'span_message').text,
                         'The file does not contain any data.')
        # he goes back
        self.browser.find_element(By.CLASS_NAME, 'a_menu').click()
        self.browser.find_element(By.LINK_TEXT, '(3) Aged stock').click()
        # he tries again, this time uploading a file with the wrong headers
        xlsx_upload_field = self.browser.find_element(By.ID, 'id_file_field')
        wrong_relative_path = 'aged/lab/DataSafeOnes/04_wrong_AgedStock_not_correct_headers.xlsx'
        wrong_absolute_file_path = os.path.abspath(wrong_relative_path)
        xlsx_upload_field.send_keys(wrong_absolute_file_path)
        self.browser.find_element(By.ID, 'id_submit_file').click()
        # and he is meet by an error message
        self.assertTrue(self.browser.find_element(By.ID, 'span_message').text.startswith(
            'The file requires the following headers:'))

        # he goes back, and uploads the good file
        self.browser.find_element(By.CLASS_NAME, 'a_menu').click()
        self.browser.find_element(By.LINK_TEXT, '(3) Aged stock').click()
        # he tries again, this time uploading a file with the wrong headers
        xlsx_upload_field = self.browser.find_element(By.ID, 'id_file_field')
        right_relative_path = 'aged/lab/DataSafeOnes/01_good_AgedStock.xlsx'
        right_absolute_file_path = os.path.abspath(right_relative_path)
        xlsx_upload_field.send_keys(right_absolute_file_path)
        self.browser.find_element(By.ID, 'id_submit_file').click()
        # he is met by a message that says the file was uploaded successfully
        self.assertEqual(self.browser.find_element(By.ID, 'span_message').text, 'File uploaded')

        # he checks his xlsx file for a few random products and checks that there are in the database
        self.assertTrue(AvailableStock.objects.filter(
            available_product=Products.objects.filter(cod_material='MIS-002-871').get(),
            stock_location=LocationsForStocks.objects.filter(location_of_stocks='GBX').get(),
            expiration_date=date_to_string_or_string_to_date('2025-01-23'),
            batch=86697483,
            # he is mindful that the app converts floats to integers
            original_quantity_in_kg=131,
            under_offer_quantity_in_kg=0,
            sold_quantity_in_kg=0,
            available_quantity_in_kg=131
        ).exists())

        self.assertTrue(AvailableStock.objects.filter(
            available_product=Products.objects.filter(cod_material='CHO-154-472').get(),
            stock_location=LocationsForStocks.objects.filter(location_of_stocks='GBX').get(),
            expiration_date=date_to_string_or_string_to_date('2024-09-04'),
            batch=9189809447,
            # he is mindful that the app converts floats to integers
            original_quantity_in_kg=500,
            under_offer_quantity_in_kg=0,
            sold_quantity_in_kg=0,
            available_quantity_in_kg=500
        ).exists())

        # he also checks that the database captures the fact that the file was already
        # uploaded by recording the creation date of the file
        date_file_was_created_db_list = CheckIfFileWasAlreadyUploaded.objects.values_list('data_creare_fisier',
                                                                                          flat=True)
        file = pd.ExcelFile(right_absolute_file_path, engine='openpyxl')
        workbook = file.book
        creation_date = str(workbook.properties.created)
        self.assertTrue(creation_date in date_file_was_created_db_list)

        # and also checks that some brands were uploaded in the database
        self.assertTrue(Brands.objects.filter(brand='Chocogreat').exists())
        self.assertTrue(Brands.objects.filter(brand='ChocoElite').exists())


        # self.fail('finish the test ')
