from django.contrib.staticfiles.testing import StaticLiveServerTestCase # this a  class provided by Django for tests
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from aged.models import AvailableStock,\
    Products,\
    LocationsForStocks,\
    CheckIfFileWasAlreadyUploaded,\
    Brands, \
    Customers, \
    CustomerService

from aged.lab.Aged_stock import date_to_string_or_string_to_date
from selenium.webdriver.common.by import By
from django.contrib.auth.models import User
import os
import pandas as pd
import time

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
            first_name='Miki',
            last_name='Mic',
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
        # he goes back and this time uploads a good file (containing just one salesperson - Mikimic)
        self.browser.find_element(By.CLASS_NAME, 'a_menu').click()
        self.browser.find_element(By.LINK_TEXT, '(1) Salespeople, customer care agents and customers').click()
        # this time he uploads an older file that does not contain the right headers
        xlsx_upload_field = self.browser.find_element(By.ID, 'id_file_field')
        right_relative_path = 'aged/lab/DataSafeOnes/16_just_one_sales_rep_mikimic.xlsx'
        right_absolute_file_path = os.path.abspath(right_relative_path)
        xlsx_upload_field.send_keys(right_absolute_file_path)
        self.browser.find_element(By.ID, 'id_submit_file').click()

        # he checks that the file was uploaded successfully
        self.assertEqual(self.browser.find_element(By.ID, 'id_message').text, 'All accounts updated')

        # he also looks in the database and checks for a few customers
        self.assertTrue(Customers.objects.filter(
            customer_name='Quantum Foods Engineering Ltd.',
            customer_number=5421,
            allocated_customer_service_rep=CustomerService.objects.filter(customer_service_rep='Reese Brown').get()
            ).exists(), )
        self.assertTrue(Customers.objects.filter(
            customer_name='Dark Chocolate Dreams',
            customer_number=1296,
            allocated_customer_service_rep=CustomerService.objects.filter(
                customer_service_rep='Jamie Garcia').get(),
            ).exists())


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

    def test_superuser_checks_the_all_stock_page(self):
        # populate database
        self.browser.get(self.live_server_url)
        username_input = self.browser.find_element(By.ID, 'id_username')
        username_input.send_keys('Mikimic')
        password_input = self.browser.find_element(By.ID, 'id_password')
        password_input.send_keys('adminpassword')
        self.browser.find_element(By.CLASS_NAME, 'input_form_submit').click()
        self.browser.find_element(By.LINK_TEXT, 'Upload Files 🡢').click()
        self.browser.find_element(By.LINK_TEXT, '(1) Salespeople, customer care agents and customers').click()
        xlsx_upload_field = self.browser.find_element(By.ID, 'id_file_field')
        right_relative_path = 'aged/lab/DataSafeOnes/16_just_one_sales_rep_mikimic.xlsx'
        right_absolute_file_path = os.path.abspath(right_relative_path)
        xlsx_upload_field.send_keys(right_absolute_file_path)
        self.browser.find_element(By.ID, 'id_submit_file').click()
        self.browser.get(self.live_server_url)
        self.browser.find_element(By.LINK_TEXT, 'Upload Files 🡢').click()
        self.browser.find_element(By.LINK_TEXT, '(3) Aged stock').click()
        xlsx_upload_field = self.browser.find_element(By.ID, 'id_file_field')
        right_relative_path = 'aged/lab/DataSafeOnes/01_good_AgedStock.xlsx'
        right_absolute_file_path = os.path.abspath(right_relative_path)
        xlsx_upload_field.send_keys(right_absolute_file_path)
        self.browser.find_element(By.ID, 'id_submit_file').click()
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


        #TODO: check button make offer functioning
        # after an offer has been made, check that is under offer and can be filtered
        # after a product has been sold, check that it can be filtered out

class UserOffers(StaticLiveServerTestCase):
    def setUp(self) -> None:
        self.browser = webdriver.Firefox()  # starts firefox
        self.browser.implicitly_wait(5)


        # Admin has an account
        self.superuser = User.objects.create_superuser(
            username='Mikimic',
            first_name='Miki',
            last_name='Mic',
            password='adminpassword',
            email='admin@example.com'
        )

        # He creates one account for Morgan who is a salesperson
        self.regular_user = User.objects.create_user(
            username='Morgan',
            first_name='Morgan',
            last_name='Davis',
            password='password123',
            email='morgan@example.com'
        )
        # And one account for Quinn who is an administration
        self.superuser = User.objects.create_superuser(
            username='Quinn',
            first_name='Quinn',
            last_name='Miller',
            password='password123',
            email='quinn@example.com'
        )

        # he uploads the xlsx in the database
        self.browser.get(self.live_server_url)
        username_input = self.browser.find_element(By.ID, 'id_username')
        username_input.send_keys('Mikimic')
        password_input = self.browser.find_element(By.ID, 'id_password')
        password_input.send_keys('adminpassword')
        self.browser.find_element(By.CLASS_NAME, 'input_form_submit').click()
        self.browser.find_element(By.LINK_TEXT, 'Upload Files 🡢').click()
        self.browser.find_element(By.LINK_TEXT, '(1) Salespeople, customer care agents and customers').click()
        xlsx_upload_field = self.browser.find_element(By.ID, 'id_file_field')
        right_relative_path = 'aged/lab/DataSafeOnes/17_just_two_sales_people.xlsx'
        right_absolute_file_path = os.path.abspath(right_relative_path)
        xlsx_upload_field.send_keys(right_absolute_file_path)
        self.browser.find_element(By.ID, 'id_submit_file').click()
        self.browser.get(self.live_server_url)
        self.browser.find_element(By.LINK_TEXT, 'Upload Files 🡢').click()
        self.browser.find_element(By.LINK_TEXT, '(3) Aged stock').click()
        xlsx_upload_field = self.browser.find_element(By.ID, 'id_file_field')
        right_relative_path = 'aged/lab/DataSafeOnes/01_good_AgedStock.xlsx'
        right_absolute_file_path = os.path.abspath(right_relative_path)
        xlsx_upload_field.send_keys(right_absolute_file_path)
        self.browser.find_element(By.ID, 'id_submit_file').click()

    def tearDown(self) -> None:  # This code runs once AFTER EACH test
        self.browser.quit()  # quits firefox

    def test_a_user_makes_offer(self):
        # Morgan logs in her account
        self.browser.get(self.live_server_url + '/accounts/login/')
        username_input = self.browser.find_element(By.ID, 'id_username')
        username_input.send_keys('Morgan')
        password_input = self.browser.find_element(By.ID, 'id_password')
        password_input.send_keys('password123')
        self.browser.find_element(By.CLASS_NAME, 'input_form_submit').click()
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
        # she selects one of her customers
        select_element = self.browser.find_element(By.NAME, "customer")
        select = Select(select_element)
        select.select_by_visible_text("Creamy Cocoa Bites")



