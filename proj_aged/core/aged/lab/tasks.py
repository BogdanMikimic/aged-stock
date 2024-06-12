import datetime
from ..models import AFostVerificatAzi, AvailableStock, OffersLog

def code_already_run_today() -> bool:
    """
    Checks if the code has already run today
    :return: True if code has already run today, False otherwise
    """
    today_date = datetime.date.today()
    date_in_db = AFostVerificatAzi.objects.all()
    for run_date in date_in_db:
        if run_date == today_date:
            return True

    AFostVerificatAzi(expiredOferedStock=today_date).save()
    return False


def delete_expired_stock_and_mark_offered_as_stock_expired() -> None:
    expired_stock_in_available_stock_list = AvailableStock.objects.filter(expiration_date__lt=datetime.date.today()).all() # caveat - codul ruleaza la 4 dimineata, asa ca nu sterg produsul in ziua in care expira, ci in dimineata zilei urmatoare
    for expired_stock in expired_stock_in_available_stock_list:
    # retrieve all the offers that contain the expired stock
        list_of_offers_containing_expired_stock = OffersLog.objects.filter(offered_stock=expired_stock).all()
        for offer_containing_expired_stock in list_of_offers_containing_expired_stock:
        # mark offer as containing an expired product
            offer_containing_expired_stock.stock_expired = True
            offer_containing_expired_stock.save()
        expired_stock.delete()


def find_offers_that_expire_today_and_return_the_quantity_to_available_stock() -> None:
    # Return the quantity to available stock

    # astea is ofertele expirate
    expired_offer_stock_to_return = OffersLog.objects.filter(expiration_date_of_offer__lt=datetime.date.today()).all()
    for stock in expired_offer_stock_to_return:
        # check if the available stock itself is not expired and has not been removed
        if stock.stock_expired is False and stock.stock_expired != 'Offered':
            # quantity locked in offer
            quantity_blocked_in_offer = stock.offered_sold_or_declined_quantity_kg
            # return the quantity locked in the offer to the available stock
            available_stock = stock.offered_stock
            available_stock.under_offer_quantity_in_kg -= quantity_blocked_in_offer
            available_stock.available_quantity_in_kg += quantity_blocked_in_offer
            available_stock.save()

            # modify the status of the offer
            stock.offer_status = 'Offer Expired'
            stock.date_of_outcome = datetime.date.today() - datetime.timedelta(days=1) # offered expired at EOB, but check is done after 12 AM
            stock.save()
