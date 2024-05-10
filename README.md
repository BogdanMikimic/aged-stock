# Stock management tool
This application is a tiered web tool designed for aged stock management, catering to three user levels: admins, managers, and salespeople. Its core function is to streamline the handling of older inventory. Key features include:

## User Access: 
Only pre-existing accounts can access the tool, with account creation exclusive to admins.

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