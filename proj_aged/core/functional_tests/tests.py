from django.contrib.staticfiles.testing import StaticLiveServerTestCase # this a  class provided by Django for tests
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from django.contrib.auth.models import User
from selenium.webdriver.common.keys import Keys
import time

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
        WebDriverWait(self.browser, 10).until(EC.presence_of_element_located((By.ID, 'id_username')))
        self.assertIsNotNone(self.browser.find_elements(By.ID, 'id_username'), 'There is no "id_username" id on page')
        self.assertIsNotNone(self.browser.find_elements(By.ID, 'id_password'), 'There is no "id_password" id on page')
        # she clicks on the navigation bar on the "My offers" button only to be greeted by the same request
        my_offers_anchor_tag = self.browser.find_element(By.LINK_TEXT, 'My offers')
        my_offers_anchor_tag.click()
        WebDriverWait(self.browser, 10).until(EC.presence_of_element_located((By.ID, 'id_username')))
        self.assertIsNotNone(self.browser.find_elements(By.ID, 'id_username'), 'There is no "id_username" id on page')
        self.assertIsNotNone(self.browser.find_elements(By.ID, 'id_password'), 'There is no "id_password" id on page')
        # finally, she clicks on the navigation bar on the "My offers" button only to be greeted by the same request
        help_page_anchor_tag = self.browser.find_element(By.LINK_TEXT, 'Help')
        help_page_anchor_tag.click()
        WebDriverWait(self.browser, 10).until(EC.presence_of_element_located((By.ID, 'id_username')))
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
    def test_log_in_for_admin(self):
        self.browser.get(self.live_server_url)
        username_input = self.browser.find_element(By.ID, 'id_username')
        username_input.send_keys('Mikimic')
        password_input = self.browser.find_element(By.ID, 'id_password')
        password_input.send_keys('adminpassword')
        self.browser.find_element(By.CLASS_NAME, 'input_form_submit').click()
        self.assertIsNotNone(self.browser.find_element(By.LINK_TEXT, 'Upload Files 🡢'))



