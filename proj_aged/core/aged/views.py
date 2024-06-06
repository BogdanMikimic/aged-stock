from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from .models import *
from django.contrib.auth.decorators import user_passes_test
from django.core.files.storage import FileSystemStorage # deals with file stored on drive
from django.http import HttpResponse # returns files to download

# Aged stock xlsx file processing functions
from .lab.Aged_stock import check_if_file_was_already_uploaded,\
      put_brand_into_db,\
      put_material_type_into_db,\
      put_stock_location_in_database,\
      put_products_in_the_database,\
      put_available_stock_in_the_database

from .lab.writePdfOffer import PdfOfferCreator
from .lab.AgedMailSender import MailSender
import datetime
import textwrap

# Salespeople, accounts xlsx file processing functions
from .lab.Sales_people_and_their_accounts2 import only_one_tab_check, \
    check_spreadsheet_contains_data, \
    return_data_frame_without_empty_rows_and_cols,\
    check_headers,\
    check_salespeople_in_database,\
    create_customer_care_accounts, \
    create_customer_accounts,\
    do_not_use_in_production_automatic_accounts_creation

# homepage
@login_required
def homepage(request):
    if request.user.is_superuser:
        return render(request, 'aged/superuserhome.html')
    else:
        return render(request, 'aged/userhome.html')


# --------- uploading xlsx files in the database
@user_passes_test(lambda u: u.get_username() == 'Mikimic')
def fileupload(request):
    return render(request, 'aged/fileupload.html')


# this it is only available to me (file to upload salespeople, customer care people and company names .xlsx file)
@login_required
@user_passes_test(lambda u: u.get_username() == 'Mikimic')
def salespeopleupload(request):
    """
    Parses the xlsx and notifies if User accounts have to be created or deleted
    Creates, deletes customer care accounts
    Creates/retires customer accounts
    """
    if request.method == 'GET':
        return render(request, 'aged/salespeopleupload.html')
    elif request.method == 'POST':
        # upload xlsx file with accounts and sales people
        file_name = 'people.xlsx'
        file_1 = request.FILES['file_1']
        file_object = FileSystemStorage()
        file_object.save(file_name, file_1)
        file_name_with_path = f'media/{file_name}'

        # check xlsx has only one tab
        if not only_one_tab_check(file_name_with_path):
            file_object.delete(file_name)
            upload_status = 'The file has more than one tab. Fix file and re-upload'
            return render(request, 'aged/salespeopleupload.html', {'upload_status': upload_status})

        # check spreadsheet not blank
        if not check_spreadsheet_contains_data(file_name_with_path):
            file_object.delete(file_name)
            upload_status = 'The file has no data. Fix file and re-upload'
            return render(request, 'aged/salespeopleupload.html', {'upload_status': upload_status})

        # check that the spreadsheet contains the expected headers
        dataframe = return_data_frame_without_empty_rows_and_cols(file_name_with_path)
        expected_headers = ['Customer Name', 'Customer Number', 'Sales Rep', 'Customer Care Agent']
        if not check_headers(expected_headers, dataframe):
            file_object.delete(file_name)
            upload_status = f'The file has the wrong headers. The expected headers are: {" ".join(expected_headers)}. Fix file and re-upload'
            return render(request, 'aged/salespeopleupload.html', {'upload_status': upload_status})

        # delete the xlsx file from database
        file_object.delete(file_name)

        # check that all users are in the database and that deleting or creating some is not required
        if not check_salespeople_in_database(dataframe):
            acc_to_create_or_delete = check_salespeople_in_database(dataframe)
            message_create = ''
            accounts_to_create = list()
            message_delete = ''
            accounts_to_delete = list()

            if len(acc_to_create_or_delete[0]) > 0:
                message_create = textwrap.dedent('''Customers are linked to sales people,
                                                   so salespeople accounts need to be created first.
                                                   The following accounts need to be created:''')
                accounts_to_create = acc_to_create_or_delete[0]
            else:
                message_create = textwrap.dedent('''No sales people account to create''')

            if len(acc_to_create_or_delete[1]) > 0:
                message_delete = textwrap.dedent('''There are a few sales people accounts to create:''')

            # do_not_use_in_production_automatic_accounts_creation(dataframe)

            return render(request, 'aged/salespeopleupload.html', {'message_create': message_create,
                                                                   'message_delete': message_delete,
                                                                   'accounts_to_create': accounts_to_create,
                                                                   'accounts_to_delete': accounts_to_delete,
                                                                   })
        else:
            create_customer_care_accounts(dataframe)
            create_customer_accounts(dataframe)
            message = 'All accounts updated'
            return render(request, 'aged/salespeopleupload.html', {'message': message})


@login_required
@user_passes_test(lambda u: u.get_username() == 'Mikimic')
def agedstockupload(request):
    """
    Performs checks on the xlsx file containing stock data
    Checks file only has one tab
    Checks file contains data
    Checks file has the right headers
    Checks file was not uploaded already
    Uploads brands in the database
    Uploads material types in the database (Chocolate, nuts, etc)

    """
    if request.method == 'GET':
        return render(request, 'aged/agedstockupload.html')
    elif request.method == 'POST':
        # upload file, read content, delete file - return content as dict
        file_name = 'stock.xlsx'
        file_2 = request.FILES['file_2']
        file_object = FileSystemStorage()
        file_object.save(file_name, file_2)

        # check if file has only one tab
        if not only_one_tab_check(f'media/{file_name}'):
            message = 'The file has more than one tab. Fix file and re-upload'
            file_object.delete(file_name)
            return render(request, 'aged/agedstockupload.html', {'message': message})

        # check if file contains data
        if not check_spreadsheet_contains_data(f'media/{file_name}'):
            message = 'The file does not contain any data.'
            file_object.delete(file_name)
            return render(request, 'aged/agedstockupload.html', {'message': message})

        # return the dataframe
        dataframe = return_data_frame_without_empty_rows_and_cols(f'media/{file_name}')
        # check headers
        requested_headers = ['Plnt', 'Stor loc', 'Material', 'Brand', 'Matl Group', 'Batch', 'Quantity', 'Unrestricted',
                             'Expiration date', 'Description']
        if not check_headers(requested_headers, dataframe):
            message = f'The file requires the following headers: {", ".join(requested_headers)}'
            file_object.delete(file_name)
            return render(request, 'aged/agedstockupload.html', {'message': message})

        # check if file was already uploaded
        if check_if_file_was_already_uploaded(f'media/{file_name}'):
            message = 'This file was already uploaded'
            file_object.delete(file_name)
            return render(request, 'aged/agedstockupload.html', {'message': message})

        # add new brands into the database
        put_brand_into_db(dataframe)
        # add new material types into the database
        put_material_type_into_db(dataframe)
        # add new locations into the database
        put_stock_location_in_database(dataframe)
        # add products to the database
        put_products_in_the_database(dataframe)
        # populate the available stock table
        put_available_stock_in_the_database(dataframe)

        file_object.delete(file_name)
        message = 'File uploaded'
        return render(request, 'aged/agedstockupload.html', {'message': message})


# --------------- users/superusers check available stock
@login_required
def userseallstock(request):
    """"
    Shows all available stock page
    Retrieve all stock that was offered or sold
    Does not show expired stock
    HTML page can redirect to making offers page/form
    """
    # retrieve offers that are "offered" or "sold", and which are not expired
    touched_stock = OffersLog.objects.filter(stock_expired=False)
    # retrieve all available stock
    free_stock_all = AvailableStock.objects.all().order_by('expiration_date')
    # push all materials to template to use with custom tags in HTML and JS for filtering
    # each material that is available in free and touched stock, is pushed to the table
    material = set()
    materiale = set()
    for itm in touched_stock:
        material.add(itm.offered_product.product_material_type.material_type)
        materiale.add(itm.offered_product.product_material_type)
    for itm in free_stock_all:
        material.add(itm.available_product.product_material_type.material_type)
        materiale.add(itm.available_product.product_material_type)
    material_csv = ",".join(material)
    return render(request, 'aged/userseallstock.html',
                  {'freeStockAll': free_stock_all,
                   'touchedStock': touched_stock,
                   'materiale': materiale,
                   'materialCsv': material_csv})


# --------------- user/superuser makes offer
@login_required
def usersmakeoffer(request, itm_id):
    """
    Returns a form for making offers, custom set up with the material which is offered from previous page,
    and with the user's own customers.
    If someone else sells all/some available quantity,and not enough quantity remains the user is redirected to
    the "not enough quantity page
    Otherwise he is redirected to the successful offer completion page
    """
    stock_item = AvailableStock.objects.filter(id=itm_id).get()
    customers = Customers.objects.filter(salesperson_owning_account=request.user.id).order_by('customer_name')
    theSpecificStock = AvailableStock.objects.filter(id = itm_id).get()

    if request.method == 'GET':
        return render(request, 'aged/usersmakeoffer.html', {'stock_item': stock_item, 'customers': customers})

    elif request.method == 'POST':
        # check if the quantity is still available, if so log the offer
        # if not, redirect user
        if int(theSpecificStock.available_quantity_in_kg) >= int(request.POST.get('quantity')):

            dataOfertaStr = request.POST.get('date_of_offer')
            dateOfOffer = datetime.datetime.fromisoformat(dataOfertaStr).date()
            #expiration date is offer date + 7 days
            expireDateOfOffer = dateOfOffer + datetime.timedelta(days=7)

            log_entry = OffersLog(
                        sales_rep_that_made_the_offer=User.objects.filter(username=request.user.get_username()).get(),
                        offered_stock=theSpecificStock,
                        offered_product=theSpecificStock.available_product,
                        customer_that_received_offer=Customers.objects.filter(id=int(request.POST.get('customer'))).get(),
                        offered_sold_or_declined_quantity_kg=request.POST.get('quantity'),
                        offer_status='Offered',
                        discount_offered_percents=request.POST.get('discount_in_percent'),
                        price_per_kg_offered=request.POST.get('price'),
                        date_of_offer=dateOfOffer,
                        expiration_date_of_offer=expireDateOfOffer
                        )

            log_entry.save()
            stock_item.under_offer_quantity_in_kg += int(request.POST.get('quantity'))
            stock_item.available_quantity_in_kg -= int(request.POST.get('quantity'))
            stock_item.save()

            return redirect('userawesomeoffer', offerId=log_entry.id)

        # if the quantity is no longer available because someone else took it
        else:
            return redirect('notenoughstock', stockId=stock_item.id)


@login_required
def userawesomeoffer (request, offerId):
    """
    This confirms the successful offer and gives the opportunity to download offer as pdf
    """
    myId = offerId
    if request.method == 'GET':
        return render(request, 'aged/userawesomeoffer.html')

    # make offer pdf
    elif request.method == 'POST':
        specificOfferObject = OffersLog.objects.filter(id=myId).get()

        salesPersonName = specificOfferObject.sales_rep_that_made_the_offer.username
        customerServiceRepName = specificOfferObject.customer_that_received_offer.allocated_customer_service_rep.customer_service_rep
        customerName = specificOfferObject.customer_that_received_offer.customer_name
        dateOfOffer = specificOfferObject.date_of_offer
        expireDateOfOffer = specificOfferObject.expiration_date_of_offer
        offeredProduct = specificOfferObject.offered_product.cod_material
        batch = specificOfferObject.offered_stock.batch
        offeredQuantity = specificOfferObject.offered_sold_or_declined_quantity_kg
        offeredPricePerKilo = specificOfferObject.price_per_kg_offered
        productType = specificOfferObject.offered_product.product_material_type.material_type
        productBrand = specificOfferObject.offered_product.product_brand.brand
        stockExpirationDate = specificOfferObject.offered_stock.expiration_date
        pdfTitle = f'{offeredProduct}-FOR-{customerName}'

        pdf = PdfOfferCreator(pdfTitle,
                              salesPersonName,
                              customerServiceRepName,
                              customerName,
                              dateOfOffer,
                              expireDateOfOffer,
                              offeredProduct,
                              batch,
                              offeredQuantity,
                              offeredPricePerKilo,
                              productType,
                              productBrand,
                              stockExpirationDate
                              )
        pdf.makePdf()
        # create response that serves the pdf
        response = HttpResponse(open(f'media/{pdfTitle}.pdf', 'rb'), headers={
                            'Content-Type': 'application/pdf',
                            'Content-Disposition': f'attachment; filename="{pdfTitle}.pdf"',
                            })
        # delete pdf
        myFileObject = FileSystemStorage()
        myFileObject.delete(f'{pdfTitle}.pdf')
        return response


@login_required
def notenoughstock(request, stockId):
    """
    This returns a page with a few options (anchor tags) available to the person, such as
    remaking the offer for the remaining quantity, or navigating back to other pages
    """
    stock_item = AvailableStock.objects.filter(id=stockId).get()
    return render(request, 'aged/notenoghstockavailable.html', {'stock_item': stock_item})


@login_required
def userpendingoffers(request):
    """
    Hides all touched stock older than 60 days (2 months), but show offers in the future
    (if someone decides to make the offer available from tomorrow, or for next week)
    """
    azi = datetime.datetime.today()
    sixtyDaysAgo = (azi - datetime.timedelta(days=60)).date()
    pending = OffersLog.objects.filter(date_of_offer__gte=sixtyDaysAgo, sales_rep_that_made_the_offer=request.user).all().order_by('offer_status')
    return render(request, 'aged/userpendingoffers.html', {'pending': pending})


@login_required
def changeofferedstatus(request, offer_id):
    #TODO: see comments below maybe
    # check if product is expired!!!!!!!!!!!!!!!!!

    # change the status of the offer
    offeredObject = OffersLog.objects.filter(id=offer_id).get()
    if request.method == 'GET':
        return render(request, 'aged/changeofferedstatus.html', {'object': offeredObject})
    elif request.method == 'POST':
        # stockObject =
        azi = datetime.date.today()
        if request.POST.get('sold') == "1":
            # the "mark it sold" button was pushed - so modify in offers log
            offeredObject.offer_status = 'Sold'
            offeredObject.date_of_outcome = azi
            offeredObject.expiration_date_of_offer = None
            offeredObject.save()
            # modify quantity in available stock
            offeredObject.offered_stock.under_offer_quantity_in_kg -= offeredObject.offered_sold_or_declined_quantity_kg
            offeredObject.offered_stock.sold_quantity_in_kg += offeredObject.offered_sold_or_declined_quantity_kg
            offeredObject.offered_stock.save()
            return redirect('userpendingoffers')
        elif request.POST.get('declined') == "1":
            # the "mark it declined" button was pushed - so modify in offers log
            offeredObject.offer_status = 'Declined'
            offeredObject.date_of_outcome = azi
            offeredObject.expiration_date_of_offer = None
            offeredObject.save()
            # modify quantity in available stock
            offeredObject.offered_stock.under_offer_quantity_in_kg -= offeredObject.offered_sold_or_declined_quantity_kg
            offeredObject.offered_stock.available_quantity_in_kg += offeredObject.offered_sold_or_declined_quantity_kg
            offeredObject.offered_stock.save()
            return redirect('userpendingoffers')
        elif request.POST.get('changeOfferRedirect') == "1":
            # this redirects to a change offer form
            return redirect('changeoffer', offer_id=offeredObject.id, mess='f')
        elif request.POST.get('return') == "1":
            return redirect('userpendingoffers')


@login_required
def changeoffer(request, offer_id, mess):
    """
    This is used when an existing offer needs to be changed.
    """
    # the message is used when, during the process of filling the form to change the offer - in the eventuality
    # the new offered quantity is more than originally offered and in the meantime somebody offers a portion or integral
    # the remaining quantity, so the new quantity is less that intended to offer
    # mesajul e folosit daca cumva in timp ce oferta e schimbata, cineva ofera acelasi produs si cantitatea ramasa e mai mica decat se vrea oferit
    if mess == 'f':
        message = ''
    else:
        message = 'It seems like someone beat you to it, and there is not enough stock left to increase the offered'
        message += ' quantity. I have adjusted the maximum quantity to display the correct maximum quantity available .'
    myOfferToChange = OffersLog.objects.filter(id=offer_id).get()
    customers = Customers.objects.filter(salesperson_owning_account=request.user)
    # here I want the whole quantity, available pus what was originally offered
    kgAvailableWithTheOnesAddedInTheOffer = myOfferToChange.offered_sold_or_declined_quantity_kg + myOfferToChange.offered_stock.available_quantity_in_kg
    if request.method == 'GET':
        dateOfOfferString = str(myOfferToChange.date_of_offer)
        return render(request, 'aged/changeoffer.html',
                      {'offer': myOfferToChange,
                       'customers': customers,
                       'wholeQuantity': kgAvailableWithTheOnesAddedInTheOffer,
                       'dateOfOfferString': dateOfOfferString,
                       'message': message})
    elif request.method == 'POST':
        # check that the actual quantity (offered + free) is still available (nobody else offered the quantity while
        # form was filled)
        if kgAvailableWithTheOnesAddedInTheOffer >= int(request.POST.get('quantity')):
            # get the quantities into variables
            vecheaOfertaKg = myOfferToChange.offered_sold_or_declined_quantity_kg
            nouaOfertaKg = int(request.POST.get('quantity'))
            totalSubOfertaKg = myOfferToChange.offered_stock.under_offer_quantity_in_kg
            totalDisponibilKg = myOfferToChange.offered_stock.available_quantity_in_kg
            # AvailableStock adjust under offer quantity and available quantity
            # subtract the old offered qty from total offered qty (nullifying the previous transaction),
            # and then add the new offer value (which can be bigger or smaller than the original one)
            myOfferToChange.offered_stock.under_offer_quantity_in_kg = (totalSubOfertaKg - vecheaOfertaKg) + nouaOfertaKg
            # add to available quantity the previously offered qty (practically nullifying the transaction),
            # then subtract the new offered quantity
            myOfferToChange.offered_stock.available_quantity_in_kg = (totalDisponibilKg + vecheaOfertaKg) - nouaOfertaKg

            # Add the other values from the form
            myOfferToChange.customer_that_received_offer = Customers.objects.filter(id=request.POST.get('customer')).get()
            myOfferToChange.offered_sold_or_declined_quantity_kg = request.POST.get('quantity')
            myOfferToChange.discount_offered_percents = request.POST.get('discount_in_percent')
            myOfferToChange.price_per_kg_offered = request.POST.get('price')
            myOfferToChange.date_of_offer = request.POST.get('date_of_offer')
            myOfferToChange.expiration_date_of_offer = datetime.datetime.strptime(request.POST.get('date_of_offer'), '%Y-%m-%d').date() + datetime.timedelta(days=7)

            # Save modifications
            myOfferToChange.offered_stock.save()
            myOfferToChange.save()

            return redirect('userawesomeoffer', offerId=offer_id)
        else:
            # if quantity is too low, is adjusted and the form is returned
            return redirect('changeoffer', offer_id=myOfferToChange.id, mess='t')

# Opens the page where superusers can see the reports of who sold what, what is under offer, declined, etc
@user_passes_test(lambda u: u.is_superuser)
def superuserreports(request):
    # if you chose a certain value in one of the filters (such as a certain salesperson)
    # you will be served a page where the value will be prefilled (ie. if you filter by Sarah the filter will stay on Sarah )
    # that is what the dict does
    preselectValues = dict()
    preselectValues['salesperson'] = 'All'
    preselectValues['state'] = 'All'
    preselectValues['start'] = ''
    preselectValues['end'] = ''
    # data standard e cu 60 de zile in urma + 30 de zile in viitor pt cei care au pregatit oferte pt saptamana viitoare
    aziPlus30 = str(datetime.datetime.today().date() + datetime.timedelta(days=30))
    firstDateOfOffersSpan = str(datetime.datetime.today().date() - datetime.timedelta(days=60))
    obj = OffersLog.objects.filter(date_of_offer__range=[firstDateOfOffersSpan, aziPlus30]).all()

    # creez doua seturi ca sa elimin duplicatele de nume (ie daca Sarah are mai multe oferte, numele ei sa apara o data)
    # al doilea set e statusul posibil al ofertelor bazat pe populatia din baza de date (ie, daca nu exista nimeni cu sold, sold nu apare printre optiuni)
    allUsersWithOffers = set()
    allOfferStatus = set()
    # populez seturile
    for ob in obj:
        allUsersWithOffers.add(ob.sales_rep_that_made_the_offer.username)
        allOfferStatus.add(ob.offer_status)

    # seturile nu sunt ordonate si nu contin varianta 'All', asa ca le fac lista, sortez si adaug 'All'
    allUsersWithOffers = list(allUsersWithOffers)
    allUsersWithOffers.sort()
    allUsersWithOffers.insert(0, 'All')

    allOfferStatus = list(allOfferStatus)
    allOfferStatus.sort()
    allOfferStatus.insert(0, 'All')

    if request.method == 'POST':
        stateOfOffers = request.POST.get('offerStatus')
        preselectValues['state'] = stateOfOffers

        nameOfUser = request.POST.get('nameOfUser')
        preselectValues['salesperson'] = nameOfUser

        start = request.POST.get('startDate')
        end = request.POST.get('endDate')

        # no start or end
        if start == '' and end =='':
            # ultimele doua luni doar
            start = firstDateOfOffersSpan
            end = str(datetime.datetime.today().date() + datetime.timedelta(days=30))
        # start, no end
        elif start != '' and end == '':
            end = str(datetime.datetime.today().date() + datetime.timedelta(days=30))
        # end no start
        elif start == '' and end != '':
            start = firstDateOfOffersSpan
        # start and end
        elif start != '' and end != '':
            pass

        preselectValues['start'] = start
        preselectValues['end'] = end

        if nameOfUser != 'All':
            idOfUser = User.objects.filter(username=nameOfUser).get().id
            obj = OffersLog.objects.filter(date_of_offer__range=[start, end], sales_rep_that_made_the_offer=idOfUser).all()
            if stateOfOffers != 'All':
                obj = OffersLog.objects.filter(date_of_offer__range=[start, end], sales_rep_that_made_the_offer=idOfUser, offer_status=stateOfOffers).all()

        # search for a particular user
        elif nameOfUser == 'All':
            obj = OffersLog.objects.filter(date_of_offer__range=[start, end]).all()
            if stateOfOffers != 'All':
                obj = OffersLog.objects.filter(date_of_offer__range=[start, end], offer_status=stateOfOffers).all()

    return render(request, 'aged/superuserreports.html', {'objects': obj, 'allUsersWithOffers': allUsersWithOffers, 'allOfferStatus':allOfferStatus, 'preselectValues':preselectValues})

@login_required
def stock_help(request):
    return render(request, 'aged/help.html')


@login_required
@user_passes_test(lambda u: u.get_username() == 'Testbot')
def task1(request):
    """
    Requires a superuser called Testbot
    Removes expired PRODUCTS from all stock table
    Sets offers that contain expired PRODUCTS stock_expired field to True
    Removes expired OFFERS and moves quantity back in available stock

    This task runs automatically once a day, by calling a specific url
    Running the code creates a database entry with current date, that is checked everytime the code is called
    The task runs at 4 o'clock in the morning, so the filter __lt in the database looks for products that expired
    yesterday

    *(not implemented) Process historical data and archives older requests
    *(not implemented) emails daily backups as csvs
    """

    # the code runs once a day - check if it ran today
    today_date = datetime.date.today()
    already_done_today = False
    data_in_db = AFostVerificatAzi.objects.all()
    for offer_containing_expired_stock in data_in_db:
        if offer_containing_expired_stock.expiredOferedStock == today_date:
            already_done_today = True

    if already_done_today == False:
        # Delete expired products from available stock + mark the offers as expired
        expired_stock_in_available_stock_list = AvailableStock.objects.filter(expiration_date__lt=today_date).all() # caveat - codul ruleaza la 4 dimineata, asa ca nu sterg produsul in ziua in care expira, ci in dimineata zilei urmatoare
        for expired_stock in expired_stock_in_available_stock_list:
            # retrieve all the offers that contain the expired stock
            list_of_offers_containing_expired_stock = OffersLog.objects.filter(offered_stock=expired_stock).all()
            for offer_containing_expired_stock in list_of_offers_containing_expired_stock:
                # mark offer as containing an expired product
                offer_containing_expired_stock.stock_expired = True
                offer_containing_expired_stock.save()
            expired_stock.delete()

        # # Find OFFERS that expire today and change their status to expired
        # # Return the quantity to available stock
        # expiredOfferStockToReturn = OffersLog.objects.filter(expiration_date_of_offer__lt=today_date).all()
        # for stock in expiredOfferStockToReturn:
        #     # doar ca sa ma asigur ca nu operez din gresealade doua ori pe acelasi stock, verific sa nu fie 'Offer expired'
        #     if stock.offer_status != 'Offer Expired':
        #         kgBlockedInOffer = stock.offered_sold_or_declined_quantity_kg
        #
        #         # verifica daca stocul nu a expirat si a fost sters (this should not happen in the wild)
        #         if stock.offered_stock != None: # daca stocul e expirat, e None
        #             # returnuie cantitatea din oferta expirata in stockul original
        #             # in stocul original sunt mai multe fielduri care arata unde e stocul
        #             # (o parte din stock poate fi disponibila, o alta e under offer, o alta e sold)
        #             # bucata asta de cod cauta sa returnuie in stocul disponibil (NU in logul cu oferte)
        #             # cantitatea oferita
        #             availabelStockObject = stock.offered_stock
        #             availabelStockObject.under_offer_quantity_in_kg -= kgBlockedInOffer
        #             availabelStockObject.available_quantity_in_kg += kgBlockedInOffer
        #             availabelStockObject.save()
        #         else: # daca stocule e expirat
        #             stock.stock_expired = True
        #         # modifica statusul si data outcomeului in Offers log
        #         stock.offer_status = 'Offer Expired'
        #         stock.date_of_outcome = today_date - datetime.timedelta(days=1) # practic stocul a explicat ieri seara, dar eu il verific a doua zi dimineata
        #         stock.save()
        #
        #
        #
        #
        # # TASK 3 - sterge din offers log toate ofertele mai vechi de un an (365 zile), doar ca codul ruleaza a doua zi dimineata
        # dataDeAcumUnAn = today_date - datetime.timedelta(days=366)
        # oferteMaiVechiDe365Zile = OffersLog.objects.filter(date_of_offer__lte=dataDeAcumUnAn).all()
        # if len(oferteMaiVechiDe365Zile)>0: # daca exista oferte mai vechi
        #     for oferta in oferteMaiVechiDe365Zile:
        #         oferta.delete()

        # save the date in the database to mark that the operations have been done today
        dt = AFostVerificatAzi(expiredOferedStock=today_date)
        dt.save()
    return render(request, 'aged/teste.html')
