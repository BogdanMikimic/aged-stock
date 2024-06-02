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
from selenium.webdriver.common.by import By
from django.contrib.auth.models import User
import os
import datetime
import pandas as pd
import time
import PyPDF2

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
        """
        This tests the available stocks page filtering and searching functionality
        """
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


class UserOffers(StaticLiveServerTestCase):
    def setUp(self) -> None:
        # Define the directory where files will be downloaded
        self.download_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "downloads")

        # Create the directory if it doesn't exist
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)

        # Set Firefox profile preferences for download
        option = webdriver.FirefoxOptions()
        option.set_preference("browser.download.folderList", 2)  # Use custom download location
        option.set_preference("browser.download.dir", self.download_dir)
        option.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/pdf")  # MIME type for PDF
        option.set_preference("pdfjs.disabled", True)  # Disable Firefox's built-in PDF viewer

        # Initialize the Firefox WebDriver with the specified profile
        self.browser = webdriver.Firefox(options=option)
        self.browser.implicitly_wait(10)

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

        # he uploads the xlsx files in the database
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

        """

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
        # and makes the offer for 100 kg
        quantity_field = self.browser.find_element(By.NAME, 'quantity')
        quantity_field.clear()
        quantity_field.send_keys('100')
        # set the discount to 1
        discount_field = self.browser.find_element(By.NAME, 'discount_in_percent')
        discount_field.clear()
        discount_field.send_keys('1')
        # set the price to 1
        price_field = self.browser.find_element(By.NAME, 'price')
        price_field.clear()
        price_field.send_keys('1')
        # set the date to today
        date_field = self.browser.find_element(By.NAME, 'date_of_offer')
        today_date = '2024-05-28'
        date_field.clear()
        date_field.send_keys(today_date)
        # click the button to make the offer
        make_offer_button = self.browser.find_element(By.NAME,
                                                'postOne')
        make_offer_button.click()

        # she checks that the offer was submitted to the database
        self.assertEqual(OffersLog.objects.count(), 1)
        stock = OffersLog.objects.all()[0]
        self.assertEqual(stock.sales_rep_that_made_the_offer, User.objects.filter(first_name='Morgan', last_name='Davis').get())
        self.assertEqual(stock.offered_stock, AvailableStock.objects.filter(available_product=Products.objects.filter(cod_material='MIS-019-865').get()).get())
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
        # and she is redirected to the page with the offer form
        # she selects one of her customers
        select_element = self.browser.find_element(By.NAME, "customer")
        select = Select(select_element)
        select.select_by_visible_text('Advanced Orchards Finance Ltd.')
        # and makes the offer for 200 kg
        quantity_field = self.browser.find_element(By.NAME, 'quantity')
        # she sees that the form automatically caps her at the maximum available quantity, 300kg
        self.assertIn('300kg available', self.browser.find_elements(By.CLASS_NAME, 'label_input')[1].text)
        self.assertEqual(self.browser.find_element(By.NAME, 'quantity').get_attribute('max'), '300')
        quantity_field.clear()
        quantity_field.send_keys('200')
        # set the discount to 2
        discount_field = self.browser.find_element(By.NAME, 'discount_in_percent')
        discount_field.clear()
        discount_field.send_keys('2')
        # set the price to 1
        price_field = self.browser.find_element(By.NAME, 'price')
        price_field.clear()
        price_field.send_keys('1')
        # set the date to today
        date_field = self.browser.find_element(By.NAME, 'date_of_offer')
        today_date = '2024-05-28'
        date_field.clear()
        date_field.send_keys(today_date)
        # however, before she gets to place the order, her colleague offers 200 out of the 300 kg to one of his customers
        ## we will simulate this by directly decreasing the available stock by 200kg from the available quantity, without an offer
        my_stock = AvailableStock.objects.filter(available_product=Products.objects.filter(cod_material='COM-008-310').get()).get()
        my_stock.available_quantity_in_kg -= 200
        my_stock.save()

        #she clicks the button to make the offer
        make_offer_button = self.browser.find_element(By.NAME,
                                                      'postOne')
        make_offer_button.click()

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
        select_element = self.browser.find_element(By.NAME, "customer")
        select = Select(select_element)
        select.select_by_visible_text('Advanced Orchards Finance Ltd.')
        # and makes the offer for 100 kg
        quantity_field = self.browser.find_element(By.NAME, 'quantity')
        quantity_field.clear()
        quantity_field.send_keys('100')
        # set the discount to 2
        discount_field = self.browser.find_element(By.NAME, 'discount_in_percent')
        discount_field.clear()
        discount_field.send_keys('2')
        # set the price to 1
        price_field = self.browser.find_element(By.NAME, 'price')
        price_field.clear()
        price_field.send_keys('1')
        # set the date to today
        date_field = self.browser.find_element(By.NAME, 'date_of_offer')
        today_date = '2024-05-28'
        date_field.clear()
        date_field.send_keys(today_date)
        # however, before she gets to place the order, her colleague offers the remaining 100 kg
        ## we will simulate this by directly decreasing the available stock to zero, without an offer
        my_stock = AvailableStock.objects.filter(available_product=Products.objects.filter(
            cod_material='COM-008-310').get()).get()
        my_stock.available_quantity_in_kg = 0
        my_stock.save()

        #she clicks the button to make the offer
        make_offer_button = self.browser.find_element(By.NAME,
                                                      'postOne')
        make_offer_button.click()

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
        select_element = self.browser.find_element(By.NAME, "customer")
        select = Select(select_element)
        select.select_by_visible_text('Advanced Orchards Finance Ltd.')
        # and makes the offer for 200 kg
        quantity_field = self.browser.find_element(By.NAME, 'quantity')
        quantity_field.clear()
        quantity_field.send_keys('200')
        # set the discount to 2
        discount_field = self.browser.find_element(By.NAME, 'discount_in_percent')
        discount_field.clear()
        discount_field.send_keys('2')
        # set the price to 1
        price_field = self.browser.find_element(By.NAME, 'price')
        price_field.clear()
        price_field.send_keys('1')
        # set the date to today
        date_field = self.browser.find_element(By.NAME, 'date_of_offer')
        today_date = '2024-05-28'
        date_field.clear()
        date_field.send_keys(today_date)
        # she clicks the button to make the offer
        make_offer_button = self.browser.find_element(By.NAME,
                                                      'postOne')
        make_offer_button.click()

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
            customer_that_received_offer=Customers.objects.filter(customer_name="Creamy Cocoa Bites").get()).get()
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
        qty = self.browser.find_element(By.NAME, 'quantity')
        qty.clear()
        qty.send_keys('150')
        disc = self.browser.find_element(By.NAME, 'discount_in_percent')
        disc.clear()
        disc.send_keys('2.50')
        price = self.browser.find_element(By.NAME, 'price')
        price.clear()
        price.send_keys('1.50')
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

        # she checks that the declined offer appears as declined in the offers log page

        # she checks that the filter for hiding declined offers functions correctly

        # she checks that the offer is correctly marked in the offers log database

        # she checks that the offer is correctly marked in the Available stock database

        # a manager logs in
        # he notices he has a reports button
        # he checks the offers page to see Morgan's activity
        # he checks some filters



























