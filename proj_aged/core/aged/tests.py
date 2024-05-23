from django.test import TestCase
from django.contrib.auth.models import User
from .models import CustomerService, Customers
import pandas as pd
from aged.lab.Sales_people_and_their_accounts2 import only_one_tab_check, \
    check_spreadsheet_contains_data,\
    return_data_frame_without_empty_rows_and_cols,\
    check_headers,\
    check_salespeople_in_database,\
    create_customer_care_accounts,\
    create_customer_accounts
from aged.lab.Aged_stock import check_if_file_was_already_uploaded

class CheckSalespeopleFileUpload(TestCase):

    def test_uploaded_file_has_one_tab(self):
        # check function that checks there is only one tab works properly
        self.assertTrue(only_one_tab_check("aged\\lab\\DataSafeOnes\\7_Updated_with_Unique_company_numbers.xlsx"))
        # check function that checks there is only one tab works properly
        self.assertFalse(only_one_tab_check("aged\\lab\\DataSafeOnes\\8_multiple_tabs.xlsx"),
                          'The function fails to detect that the uploaded file has multiple tabs')

    def test_spreadsheet_is_not_blank(self):
        # check file has data
        self.assertTrue(check_spreadsheet_contains_data("aged\\lab\\DataSafeOnes\\7_Updated_with_Unique_company_numbers.xlsx"))
        # upload a blank file to check
        self.assertFalse(check_spreadsheet_contains_data("aged\\lab\\DataSafeOnes\\9_blank_file.xlsx"))

    def test_there_are_no_empty_rows_or_columns(self):
        # load original excel that has an empty row and column
        original_dataframe = pd.read_excel("aged\\lab\\DataSafeOnes\\7_Updated_with_Unique_company_numbers.xlsx")
        # test that the cell 0,0 (top left) has no data
        self.assertTrue(pd.isna(original_dataframe.iloc[0, 0]))
        # clean the dataframe of empty columns and rows
        cleaned_df = return_data_frame_without_empty_rows_and_cols(
            "aged\\lab\\DataSafeOnes\\7_Updated_with_Unique_company_numbers.xlsx")
        # check that in cell 0,0 (top left) we have data
        self.assertFalse(pd.isna(cleaned_df.iloc[0, 0]))

    def test_right_headers(self):
        dataframe = return_data_frame_without_empty_rows_and_cols(
            "aged\\lab\\DataSafeOnes\\7_Updated_with_Unique_company_numbers.xlsx")
        right_headers = ['Customer Name', 'Customer Number', 'Sales Rep', 'Customer Care Agent']
        self.assertTrue(check_headers(right_headers, dataframe))
        wrong_headers = ['Customer Cat Name', 'Customer Number', 'Sales Rep', 'Customer Care']
        self.assertFalse(check_headers(wrong_headers, dataframe))

    def test_user_in_database(self):
        # this test should return 3 accounts to be created no accounts to be deleted
        dataframe = return_data_frame_without_empty_rows_and_cols("aged\\lab\\DataSafeOnes\\11_3_new_salespeople.xlsx")
        users_to_be_created_or_deleted = check_salespeople_in_database(dataframe)
        self.assertEqual(len(users_to_be_created_or_deleted[0]), 3, 'There should be 3 new accounts to be created')
        self.assertEqual(len(users_to_be_created_or_deleted[1]), 0, 'There should be 0 accounts to be deleted')

        # create one user so the test returns 2 accounts to be creates and zero to be deleted
        User.objects.create_user(
            username='Taylor',
            first_name='Taylor',
            last_name= 'Miller',
            password='hg£$f%sadhgf334r5!'
        )
        users_to_be_created_or_deleted = check_salespeople_in_database(dataframe)
        self.assertEqual(len(users_to_be_created_or_deleted[0]), 2, 'There should be 2 new accounts to be created')
        self.assertEqual(len(users_to_be_created_or_deleted[1]), 0, 'There should be 0 accounts to be deleted')

        # create the rest of the accounts so there are 0 accounts to create and 0 accounts to delete
        User.objects.create_user(
            username='Morgan',
            first_name='Morgan',
            last_name= 'Davis',
            password='hg£$f%sdashgf334r5!'
        )
        User.objects.create_user(
            username='Casey',
            first_name='Casey',
            last_name= 'Martinez',
            password='hg£$f%sdarhgf334r5!'
        )
        self.assertTrue(check_salespeople_in_database(dataframe))

        # create another user non-existent in the xlsx so the test returns 0 accounts to be created and 1 to be deleted
        User.objects.create_user(
            username='Spiderman',
            first_name='Peter',
            last_name= 'Parker',
            password='dwaf%sadhgf334r5!'
        )
        users_to_be_created_or_deleted = check_salespeople_in_database(dataframe)
        self.assertEqual(len(users_to_be_created_or_deleted[0]), 0, 'There should be 0 new accounts to be created')
        self.assertEqual(len(users_to_be_created_or_deleted[1]), 1, 'There should be 1 account to be deleted')

    def test_customer_care_accounts_created_deleted(self):
        # upload 3 new salespeople in the database
        dataframe = return_data_frame_without_empty_rows_and_cols("aged\\lab\\DataSafeOnes\\11_3_new_salespeople.xlsx")
        create_customer_care_accounts(dataframe)
        self.assertEqual(CustomerService.objects.count(), 3)
        self.assertTrue(CustomerService.objects.filter(customer_service_rep='Taylor Smith').exists())
        self.assertTrue(CustomerService.objects.filter(customer_service_rep='Jordan Miller').exists())
        self.assertTrue(CustomerService.objects.filter(customer_service_rep='Jamie Garcia').exists())

        # delete Jamie Garcia from the xlsx and check if it's deleted from database
        dataframe = return_data_frame_without_empty_rows_and_cols(
            "aged\\lab\\DataSafeOnes\\12_only_2_customer_care_agents.xlsx")
        create_customer_care_accounts(dataframe)
        self.assertFalse(CustomerService.objects.filter(customer_service_rep='Jamie Garcia').exists())

    def test_upload_update_customer(self):
        # create users
        User.objects.create_user(
            username='Morgan',
            first_name='Morgan',
            last_name= 'Davis',
            password='hg£$f%sdashgf334r5!'
        )
        User.objects.create_user(
            username='Miller',
            first_name='Taylor',
            last_name= 'Miller',
            password='hg£$f%sdarhgf334r5!'
        )
        # create customer care agents
        dataframe = return_data_frame_without_empty_rows_and_cols(
            "aged\\lab\\DataSafeOnes\\12_only_2_customer_care_agents.xlsx")
        create_customer_care_accounts(dataframe)
        # create 'Artisan Grill' and 'Classic Delights' customers and check that they exist
        create_customer_accounts(dataframe)
        customers = Customers.objects.values_list('customer_name', flat=True)
        self.assertTrue('Artisan Grill' in customers)
        self.assertTrue('Classic Delights' in customers)

        # change customer care agent and check customer is linked to the right cc agent
        dataframe = return_data_frame_without_empty_rows_and_cols(
            "aged\\lab\\DataSafeOnes\\13_customer_care_agents_swap.xlsx")
        # creates a new customer care 'Bruce Wayne'
        create_customer_care_accounts(dataframe)
        self.assertTrue('Bruce Wayne' in CustomerService.objects.values_list('customer_service_rep', flat=True))
        # 'Classic Delights' should now have a customer care agent called 'Bruce Wayne'
        create_customer_accounts(dataframe)
        target_customer = Customers.objects.filter(customer_name='Classic Delights').get()
        self.assertEqual(target_customer.allocated_customer_service_rep.customer_service_rep, 'Bruce Wayne')

        # change salesperson in the xlsx (create it here) and check customer is linked to the right salesperson
        User.objects.create_user(
            username='Fox',
            first_name='Fox',
            last_name='Mulder',
            password='hg£$f%sdarhgf334r5!'
        )
        dataframe = return_data_frame_without_empty_rows_and_cols(
            "aged\\lab\\DataSafeOnes\\14_New_sales_people_for_same_customer.xlsx")
        create_customer_accounts(dataframe)
        target_customer = Customers.objects.filter(customer_name='Classic Delights').get()
        self.assertEqual(target_customer.salesperson_owning_account.first_name, 'Fox')
        self.assertEqual(target_customer.salesperson_owning_account.last_name, 'Mulder')

        # make an account inactive in the database - 'Classic Delights' deleted in the database
        dataframe = return_data_frame_without_empty_rows_and_cols(
            "aged\\lab\\DataSafeOnes\\15_deleted_customer.xlsx")
        create_customer_accounts(dataframe)
        target_customer = Customers.objects.filter(customer_name='Classic Delights').get()
        self.assertEqual(target_customer.salesperson_owning_account, None)
        self.assertEqual(target_customer.allocated_customer_service_rep, None)
        self.assertEqual(target_customer.customer_status, 'Inactive')

class CheckAgedStockUploads(TestCase):
    def test_aged_stock_file_upload(self):
        # check file was not yet uploaded - returns False if not
        self.assertFalse(check_if_file_was_already_uploaded("aged\\lab\\DataSafeOnes\\01_good_AgedStock.xlsx"))
        # run the test again with the same file, and it should return True
        self.assertTrue(check_if_file_was_already_uploaded("aged\\lab\\DataSafeOnes\\01_good_AgedStock.xlsx"))

