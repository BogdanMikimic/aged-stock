# Stock management tool
This application is a tiered web tool designed for aged stock management, catering to three user levels: admins, managers, and salespeople. 
Its core function is to streamline the handling of inventory of products nearing expiration date.

## User Access: 
Only pre-existing accounts can access the tool, with account creation exclusive to admins.
There are 3 types of accounts:
* salespeople (as users)
* managers (as superusers)
* admin (as a superuser called Mikimic)

## App flow and features
### The Special admin (username Mikimic)
* admin (Mikimic) logs into his account where he has an extra button where he can upload 3 types of xlsx files (only 2 are implemented, the one for historic data is not)
* first type is a xlsx containing information about customers, salespeople and managers - this is always the latest situation about what sales people, customer care reps and customers the company has
* the admin is restricted to uploading xlsx files, the file is checked to contain only one tab, not be blank and contain the right headers
* each customer is linked via foreign key to a user and a customer care agent, so the first thing the system checks is if all the customers have accounts
* the system also checks if there are accounts that need deleting (if a user is not in the xlsx, but it is in the database, it will be flagged for deletion)
* for security reasons users are created and deleted manually by the admin 
* there is no distinction in xlsx between users (salespeople) and superusers (managers)
* functionally, the superusers (managers) have an extra button on the landing page and in navigation to a dashboard where they can see the activity of salespeople, thus removing the need for reporting
* second type of file is a xlsx containing information about aged stock available in the company
* the admin had the same restrictions and checks are performed as for the file above

## Dashboard: 
Displays aged stocks in descending order by expiration, featuring dynamic filters based on stock attributes (e.g., "compounds") and a search functionality.

## Order Creation: 
Users can generate orders from stock listings, with a form displaying customer-specific information, quantities, discounts, and pricing. Orders result in a branded PDF offer, including customer and Customer Care agent details, along with the current and offer expiration dates.

## Stock Management: 
Created offers deduct the offered quantity from the stock. In case of overlapping orders exceeding available stock, priority is given based on submission time. Users are notified about stock quantity issues.

## Offer Management: 
Users and managers can view offers in their dashboards, with options to mark offers as sold (restocking the quantity), refused (restocking the quantity), or modify the offer quantity.

## Automations: 
A script periodically cleans up expired stock and adjusts inventory based on offer expiration.