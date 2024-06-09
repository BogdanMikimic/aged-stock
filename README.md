# Stock management tool
This application is a tiered web tool designed for aged stock management, catering to three user levels: admins, managers, and salespeople. 
Its core function is to facilitate the creation and management of stock offers 
nearing expiration date (called aged stock). It also embeds reporting, so managers can oversee the teams
activity without requiring the salespeople to fill in activity reports. The database schema and architecture
is designed to be extended to include automated email communication, data backups, machine learning and
data analysis algorithms that were not included in this version.


## User Access: 
Only pre-existing accounts can access the tool, with account creation exclusive to admins.
There are 3 types of accounts:
* salespeople (as users)
* managers (as superusers)
* admin (as a superuser called Mikimic)

## App flow and features
### The special admin (username Mikimic) position
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
### Normal users (salespeople)

### Superusers (managers)


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

