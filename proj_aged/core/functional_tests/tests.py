from django.contrib.staticfiles.testing import StaticLiveServerTestCase # this a  class provided by Django for tests
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from django.contrib.auth.models import User
from selenium.webdriver.common.keys import Keys
import time
import os

# Morgan - a salesperson in the UK department heard about this cool app that was designed by a colleague
# to help the sales people better manage their aged stock
class LoginIsRequired(StaticLiveServerTestCase):
    def setUp(self) -> None:  # This code runs once BEFORE EACH test
        self.browser = webdriver.Firefox() # starts firefox

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
        self.browser.implicitly_wait(5)


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


