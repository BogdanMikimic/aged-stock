from django.test import TestCase
import pandas as pd
from aged.lab.Sales_people_and_their_accounts2 import only_one_tab_check, \
    check_spreadsheet_contains_data,\
    return_data_frame_without_empty_rows_and_cols,\
    check_headers


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
        cleaned_df = return_data_frame_without_empty_rows_and_cols("aged\\lab\\DataSafeOnes\\7_Updated_with_Unique_company_numbers.xlsx")
        # check that in cell 0,0 (top left) we have data
        self.assertFalse(pd.isna(cleaned_df.iloc[0, 0]))

    def test_right_headers(self):
        dataframe = return_data_frame_without_empty_rows_and_cols("aged\\lab\\DataSafeOnes\\7_Updated_with_Unique_company_numbers.xlsx")
        right_headers = ['Customer Name', 'Customer Number', 'Sales Rep', 'Customer Care Agent']
        self.assertTrue(check_headers(right_headers, dataframe))
        wrong_headers = ['Customer Cat Name', 'Customer Number', 'Sales Rep', 'Customer Care']
        self.assertFalse(check_headers(wrong_headers, dataframe))

