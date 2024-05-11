from django.test import TestCase
from aged.lab.Sales_people_and_their_accounts2 import only_one_tab_check


class CheckSalespeopleFileUpload(TestCase):

    def test_uploaded_file_has_one_tab(self):
        # check function that checks there is only one tab works properly
        self.assertTrue(only_one_tab_check("aged\\lab\\DataSafeOnes\\7_Updated_with_Unique_company_numbers.xlsx"))
        # check function that checks there is only one tab works properly
        self.assertFalse(only_one_tab_check("aged\\lab\\DataSafeOnes\\8_multiple_tabs.xlsx"),
                          'The function fails to detect that the uploaded file has multiple tabs')