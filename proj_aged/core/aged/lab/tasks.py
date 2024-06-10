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
