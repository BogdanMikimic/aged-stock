# Stock management tool
This application is a tiered web tool designed for aged stock management, catering to three user levels: admins, managers, and salespeople. 
Its core function is to facilitate the creation and management stock offers 
nearing expiration date (called aged stock). It also embeds reporting, so managers can oversee the teams
activity without requiring the salespeople to fill in activity reports. The database schema and architecture
is designed to be extended to include automated email communication, data backups, machine learning and
data analysis algorithmsa s well as a help page that were not included in this version.


## User Access: 
Only pre-existing accounts can access the tool, with account creation exclusive to admins.
There are 3 types of accounts:
* salespeople (as users)
* managers (as superusers)
* admin (as a superuser called Mikimic - must be called so)

## App flow and features:
### The special admin (username Mikimic) user
#### I. Superuser Mikimic uploads customer and sales reps from a xlsx file, and creates user and superuser accounts
* admin (Mikimic) logs into his account where he has an extra button where he can upload 3 types of xlsx files (only 2 are implemented, the one for historic data is not)
* first type is a xlsx containing information about customers, salespeople and managers - this is always the latest situation about what sales people, customer care reps and customers the company has
* the admin is restricted to uploading xlsx files, the file is checked to contain only one tab, not be blank and contain the right headers
* each customer is linked via foreign key to a user and a customer care agent, so the first thing the system checks is if all the customers have accounts
* the system also checks if there are accounts that need deleting (if a user is not in the xlsx, but it is in the database, it will be flagged for deletion)
* for security reasons users are created and deleted manually by the admin 
* there is no distinction in xlsx between users (salespeople) and superusers (managers)
* functionally, the superusers (managers) have an extra button on the landing page and in navigation to a dashboard where they can see the activity of salespeople, thus removing the need for reporting
 * (xlsx test files can be found in "proj_aged/core/aged/lab/DataSafeOnes" "7_Updated_with_Unique_company_numbers.xlsx" is the complete file, the ones starting wit 8_ up to 18_ are used in unit and functional tests)
#### II. Superuser Mikimic uploads stock data from a xlsx file 
* second type of file is a xlsx containing information about aged stock available at the moment 
* this file is uploaded via the 3rd button (Aged stock)
* the stock xlsx file is tested content-wise as the one above; the stocks are also checked not to be expired on upload (by design, they should not be) 
* upon xlsx uploading, stock is split into Brands, MaterialType, LocationsForStocks, Products (models) an uploaded in the database (see database schema diagram for details)
* Brands, MaterialType, LocationsForStocks, Products are not automatically removed, and new ones are added to existing ones. They are finite collections that rarely change
* Products are linked trough foreign key to Brands, MaterialType, so they need to be uploaded first
* AvailableStock model is populated with the stock available, and serves as the main model the User interacts with to make offers 
* the stock available in the xlsx is not always accurate, so if the stock already exists in the database,it is trusted to be the right quantity
* the unique identifiers of a stock are the SKU (the code of the material), the batch number and the expiration data. No 2 stocks come from the same batch with the same expiration date in different quantities
* AvailableStock is linked by foreign key to LocationsForStocks and Products, so these need to be uploaded first
### Normal users (salesperson)
#### The "all stock" page
* Regular users have access to an "all stock page" that presents all the available stock, ordered descending by expiration date
* At the top of the page, the user has access to filters - which are auto-generated checkboxes, based on the existing
material categories (cocoa, chocolate, etc)
* The system is set to hide sold and under offer products by default
* There is a search bar that allows searching for products, that works together with the filters
* Next to each product, there is a button that allows the user to create an offer for that specific stock
#### Order creation form
* Clicking the button opens up a form where the user can select one of its customers (only it's customers are available
to him, select a part or all of the quantity available, select a price, a discount, a date for the offer -that can be in the future
(offers expire in 7 calendar days)
* If another user fills in a form to offer the same product, and the current offer no longer has the
needed quantity available, the user is redirected to a page that allows him to re-make the offer with
a new quantity (if there is some of the stock available) or to a page that lets him know there is no
stock available
* upon successful completion of the form, he is redirected to a page where he is presented with
the option to download the offer as a pdf
#### Order confirmation and PDF
* the user has another   

### Superusers (managers)

### Tasks

## Unit and functional tests
* unit tests: see proj_aged/core/aged/tests.py  
* functional tests: see proj_aged/core/functional_tests/tests.py  
* NOTE: the provided "...AgedStock...xlsx" documents contain an expiration date for
products. Some functional tests - like the one testing the function that clears
expired products, will wipe out all expired products from the database, not to mention
that there is another function that skip expired products in the .xlsx when uploading the
data in the database in the first place. Most functional tests work by searching for existing 
products in the tables - which won't be there if the product is expired, so you will get errors
when running the tests. So make sure to modify the expiration dates and place them in the future
in the xlsx files (01_good_AgedStock.xlsx which is the main file that contains the complete dataset, 
but the other ones containing the AgedStock words are used too for different tests).

## Install and run
* it requires Python 3.11
* copy this repository
* create and activate a virtual environment
* install all the needed dependencies from requirements.txt
> pip install -r requirements.txt
* navigate to manage.py ('proj_aged/core/manage.py')and make the migrations (it creates the database and populates it)
> manage.py makemigrations
> manage.py migrate
* create a superuser with a username Mikimic 
> manage.py createsuperuser
* run the develpoment server
> manage.py runserver
* go to your browser and navigate to http://localhost:8000/admin
* log in as the superuser Mikimic with the account you created
* go to admin "AUTHENTICATION AND AUTHORIZATION" -> "Users" and under "Personal info" add "First name": Miki, 
"Last name": Mic 
* click on the "upload files" button (your database is currently empty)
* first you need to upload the data from one of the spreadsheets containing data
about customer care agents customers and salespeople (click on the "(1) Salespeople, customer care agents and customers"). 
 proj_aged/core/aged/lab/DataSafeOnes, the files beginning with "11_" - "18_". They all contain different information, and they
are used in tests. Be advised you will be prompted to create accounts manually for
all salespeople that are not in the database. For security reasons salespeople accounts
need to be created, modified or deleted manually from the database. You can do that by
logging in as a superuser (Mikimic), navigate to http://localhost:8000/admin 
"AUTHENTICATION AND AUTHORIZATION" -> "Users" -> "ADD USER" (or check the user you want to delete,
and select from the drop-down "Actions" -> "delete selected user" -> press "Go"
If you want). To avoid creating users, simply upload the "proj_aged/core/aged/lab/DataSafeOnes/16_just_one_sales_rep_mikimic.xlsx",
where all the existing customers are moved under Mikimic
* Next, upload the information related to available stocks from the spreadsheets (click on the "(3) Aged stock" button) 
You can do so by uploading files starting with "00_" "05_" from "proj_aged/core/aged/lab/DataSafeOnes.
However, depending on when you use the app, the stocks may be expired, and therefore cleaned up upon
uploading. If you are using this in a year earlier than 2124, you can upload the 
"proj_aged/core/aged/lab/DataSafeOnes/00_good_AgedStock_good_for_100_years.xlsx" file which ensures no stocks are expired
* that's it, you can now use the app

## Notes
* not responsive - works best on large resolutions (1920px x 1080px)
