from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from .models import *
from django.contrib.auth.decorators import user_passes_test
from django.core.files.storage import FileSystemStorage # deals with file stored on drive
from django.http import HttpResponse # returns files to download
import datetime


# Aged stock xlsx file processing functions
from .lab.Aged_stock import check_if_file_was_already_uploaded,\
      put_brand_into_db,\
      put_material_type_into_db,\
      put_stock_location_in_database,\
      put_products_in_the_database,\
      put_available_stock_in_the_database

# Salespeople, accounts xlsx file processing functions
from .lab.Sales_people_and_their_accounts2 import only_one_tab_check, \
    check_spreadsheet_contains_data, \
    return_data_frame_without_empty_rows_and_cols,\
    check_headers,\
    check_salespeople_in_database,\
    create_customer_care_accounts, \
    create_customer_accounts

# automated task related functions
from .lab.tasks import code_already_run_today, \
      delete_expired_stock_and_mark_offered_as_stock_expired, \
      find_offers_that_expire_today_and_return_the_quantity_to_available_stock

# pdf maker for the offer
from .lab.writePdfOffer import PdfOfferCreator


@login_required
def homepage(request):
    if request.user.is_superuser:
        return render(request, 'aged/superuser_home.html')
    else:
        return render(request, 'aged/user_home.html')


# --------- uploading xlsx files in the database
@user_passes_test(lambda u: u.get_username() == 'Mikimic')
def upload_files(request):
    return render(request, 'aged/upload_files.html')


# this it is only available to me (file to upload salespeople, customer care people and company names .xlsx file)
@login_required
@user_passes_test(lambda u: u.get_username() == 'Mikimic')
def upload_file_with_sales_people(request):
    """
    Parses the xlsx and notifies if User accounts have to be created or deleted
    Creates, deletes customer care accounts
    Creates/retires customer accounts
    """
    if request.method == 'GET':
        return render(request, 'aged/sales_people_upload.html')
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
            return render(request, 'aged/sales_people_upload.html', {'upload_status': upload_status})

        # check spreadsheet not blank
        if not check_spreadsheet_contains_data(file_name_with_path):
            file_object.delete(file_name)
            upload_status = 'The file has no data. Fix file and re-upload'
            return render(request, 'aged/sales_people_upload.html', {'upload_status': upload_status})

        # check that the spreadsheet contains the expected headers
        dataframe = return_data_frame_without_empty_rows_and_cols(file_name_with_path)
        expected_headers = ['Customer Name', 'Customer Number', 'Sales Rep', 'Customer Care Agent']
        if not check_headers(expected_headers, dataframe):
            file_object.delete(file_name)
            upload_status = f'The file has the wrong headers. The expected headers are: {" ".join(expected_headers)}. Fix file and re-upload'
            return render(request, 'aged/sales_people_upload.html', {'upload_status': upload_status})

        # delete the xlsx file from database
        file_object.delete(file_name)

        # check that all users are in the database and that deleting or creating some is not required
        if check_salespeople_in_database(dataframe):
            acc_to_create_or_delete = check_salespeople_in_database(dataframe)
            message_create = ''
            accounts_to_create = list()
            message_delete = ''
            accounts_to_delete = list()

            if len(acc_to_create_or_delete[0]) > 0:
                message_create = 'Customers are linked to sales people, so salespeople accounts need to be created first.'
                message_create += ' The following accounts need to be created:'
                accounts_to_create = acc_to_create_or_delete[0]
            else:
                message_create = 'No sales people account to create'

            if len(acc_to_create_or_delete[1]) > 0:
                message_delete = 'There are a few sales people accounts to delete:'
                accounts_to_delete = acc_to_create_or_delete[1]

            # do_not_use_in_production_automatic_accounts_creation(dataframe)

            return render(request, 'aged/sales_people_upload.html',
                           {'message_create': message_create,
                                   'message_delete': message_delete,
                                   'accounts_to_create': accounts_to_create,
                                   'accounts_to_delete': accounts_to_delete,
                                  })
        else:
            create_customer_care_accounts(dataframe)
            create_customer_accounts(dataframe)
            message = 'All accounts updated'
            return render(request, 'aged/sales_people_upload.html', {'message': message})


@login_required
@user_passes_test(lambda u: u.get_username() == 'Mikimic')
def upload_file_with_aged_stock(request):
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
        return render(request, 'aged/aged_stock_upload.html')
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
            return render(request, 'aged/aged_stock_upload.html', {'message': message})

        # check if file contains data
        if not check_spreadsheet_contains_data(f'media/{file_name}'):
            message = 'The file does not contain any data.'
            file_object.delete(file_name)
            return render(request, 'aged/aged_stock_upload.html', {'message': message})

        # return the dataframe
        dataframe = return_data_frame_without_empty_rows_and_cols(f'media/{file_name}')
        # check headers
        requested_headers = ['Plnt', 'Stor loc', 'Material', 'Brand', 'Matl Group', 'Batch', 'Quantity', 'Unrestricted',
                             'Expiration date', 'Description']
        if not check_headers(requested_headers, dataframe):
            message = f'The file requires the following headers: {", ".join(requested_headers)}'
            file_object.delete(file_name)
            return render(request, 'aged/aged_stock_upload.html', {'message': message})

        # check if file was already uploaded
        if check_if_file_was_already_uploaded(f'media/{file_name}'):
            message = 'This file was already uploaded'
            file_object.delete(file_name)
            return render(request, 'aged/aged_stock_upload.html', {'message': message})

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
        return render(request, 'aged/aged_stock_upload.html', {'message': message})


# --------------- users/superusers check available stock
@login_required
def all_available_stock(request):
    """"
    Shows all available stock page
    Retrieve all stock that was offered or sold
    Does not show expired stock
    HTML page can redirect to making offers page/form
    """
    # retrieve offers that are "offered" or "sold", and which are not expired
    touched_stock = OffersLog.objects.filter(stock_expired=False)
    # retrieve all available stock
    all_available_stock = AvailableStock.objects.all().order_by('expiration_date')
    # push all materials to template to use with custom tags in HTML and JS for filtering
    # each material that is available in free and touched stock, is pushed to the table
    material = set()
    materials = set()
    for itm in touched_stock:
        material.add(itm.offered_product.product_material_type.material_type)
        materials.add(itm.offered_product.product_material_type)
    for itm in all_available_stock:
        material.add(itm.available_product.product_material_type.material_type)
        materials.add(itm.available_product.product_material_type)
    material_csv = ",".join(material)
    return render(request, 'aged/all_available_stock.html',
                  {'all_available_stock': all_available_stock,
                   'touched_stock': touched_stock,
                   'materials': materials,
                   'materials_as_csv': material_csv})


# --------------- user/superuser makes offer
@login_required
def make_offer(request, itm_id):
    """
    Returns a form for making offers, custom set up with the material which is offered from previous page,
    and with the user's own customers.
    If someone else sells all/some available quantity,and not enough quantity remains the user is redirected to
    the "not enough quantity page
    Otherwise he is redirected to the successful offer completion page
    """
    stock_item = AvailableStock.objects.filter(id=itm_id).get()
    customers = Customers.objects.filter(salesperson_owning_account=request.user.id).order_by('customer_name')
    the_specific_stock = AvailableStock.objects.filter(id=itm_id).get()

    if request.method == 'GET':
        return render(request, 'aged/make_offer.html', {'stock_item': stock_item, 'customers': customers})

    elif request.method == 'POST':
        # check if the quantity is still available, if so log the offer
        # if not, redirect user
        if int(the_specific_stock.available_quantity_in_kg) >= int(request.POST.get('quantity')):

            offer_date_as_str = request.POST.get('date_of_offer')
            date_of_offer = datetime.datetime.fromisoformat(offer_date_as_str).date()
            # expiration date is offer date + 7 days
            expire_date_of_offer = date_of_offer + datetime.timedelta(days=7)
            # creates the offer
            log_entry = OffersLog(
                        sales_rep_that_made_the_offer=User.objects.filter(username=request.user.get_username()).get(),
                        offered_stock=the_specific_stock,
                        offered_product=the_specific_stock.available_product,
                        customer_that_received_offer=Customers.objects.filter(id=int(request.POST.get('customer'))).get(),
                        offered_sold_or_declined_quantity_kg=request.POST.get('quantity'),
                        offer_status='Offered',
                        discount_offered_percents=request.POST.get('discount_in_percent'),
                        price_per_kg_offered=request.POST.get('price'),
                        date_of_offer=date_of_offer,
                        expiration_date_of_offer=expire_date_of_offer
                        )

            log_entry.save()
            stock_item.under_offer_quantity_in_kg += int(request.POST.get('quantity'))
            stock_item.available_quantity_in_kg -= int(request.POST.get('quantity'))
            stock_item.save()

            return redirect('offer_completed', offer_id=log_entry.id)

        # if the quantity is no longer available because someone else took it
        else:
            return redirect('not_enough_stock', stock_id=stock_item.id)


@login_required
def offer_completed(request, offer_id):
    """
    This confirms the successful offer and gives the opportunity to download offer as pdf
    """
    my_id = offer_id
    if request.method == 'GET':
        return render(request, 'aged/offer_completed.html')

    # make offer pdf
    elif request.method == 'POST':
        specific_offer_object = OffersLog.objects.filter(id=my_id).get()

        sales_person_name = specific_offer_object.sales_rep_that_made_the_offer.username
        customer_service_rep_name = specific_offer_object.customer_that_received_offer.allocated_customer_service_rep.customer_service_rep
        customer_name = specific_offer_object.customer_that_received_offer.customer_name
        date_of_offer = specific_offer_object.date_of_offer
        expire_date_of_offer = specific_offer_object.expiration_date_of_offer
        offered_product = specific_offer_object.offered_product.cod_material
        batch = specific_offer_object.offered_stock.batch
        offered_quantity = specific_offer_object.offered_sold_or_declined_quantity_kg
        offered_price_per_kilo = specific_offer_object.price_per_kg_offered
        product_type = specific_offer_object.offered_product.product_material_type.material_type
        product_brand = specific_offer_object.offered_product.product_brand.brand
        stock_expiration_date = specific_offer_object.offered_stock.expiration_date
        pdf_title = f'{offered_product}-FOR-{customer_name}'

        pdf = PdfOfferCreator(pdf_title,
                              sales_person_name,
                              customer_service_rep_name,
                              customer_name,
                              date_of_offer,
                              expire_date_of_offer,
                              offered_product,
                              batch,
                              offered_quantity,
                              offered_price_per_kilo,
                              product_type,
                              product_brand,
                              stock_expiration_date
                              )
        pdf.makePdf()
        # create response that serves the pdf
        response = HttpResponse(open(f'media/{pdf_title}.pdf', 'rb'), headers={
                            'Content-Type': 'application/pdf',
                            'Content-Disposition': f'attachment; filename="{pdf_title}.pdf"',
                            })
        # delete pdf
        my_file_object = FileSystemStorage()
        my_file_object.delete(f'{pdf_title}.pdf')
        return response


@login_required
def not_enough_stock(request, stock_id):
    """
    This returns a page with a few options (anchor tags) available to the person, such as
    remaking the offer for the remaining quantity, or navigating back to other pages
    """
    stock_item = AvailableStock.objects.filter(id=stock_id).get()
    return render(request, 'aged/not_enough_stock.html', {'stock_item': stock_item})


@login_required
def existing_offers(request):
    """
    Hides all touched stock older than 60 days (2 months), but show offers in the future
    (if someone decides to make the offer available from tomorrow, or for next week)
    """
    azi = datetime.datetime.today()
    sixty_days_ago = (azi - datetime.timedelta(days=60)).date()
    pending = OffersLog.objects.filter(date_of_offer__gte=sixty_days_ago, sales_rep_that_made_the_offer=request.user).all().order_by('offer_status')
    return render(request, 'aged/existing_offers.html', {'pending': pending})


@login_required
def change_offer_status(request, offer_id):
    # change the status of the offer
    offered_object = OffersLog.objects.filter(id=offer_id).get()
    if request.method == 'GET':
        return render(request, 'aged/change_offer_status.html', {'object': offered_object})
    elif request.method == 'POST':
        # stockObject =
        today_date = datetime.date.today()
        if request.POST.get('sold') == "1":
            # the "mark it sold" button was pushed - so modify in offers log
            offered_object.offer_status = 'Sold'
            offered_object.date_of_outcome = today_date
            offered_object.expiration_date_of_offer = None
            offered_object.save()
            # modify quantity in available stock
            offered_object.offered_stock.under_offer_quantity_in_kg -= offered_object.offered_sold_or_declined_quantity_kg
            offered_object.offered_stock.sold_quantity_in_kg += offered_object.offered_sold_or_declined_quantity_kg
            offered_object.offered_stock.save()
            return redirect('existing_offers')
        elif request.POST.get('declined') == "1":
            # the "mark it declined" button was pushed - so modify in offers log
            offered_object.offer_status = 'Declined'
            offered_object.date_of_outcome = today_date
            offered_object.expiration_date_of_offer = None
            offered_object.save()
            # modify quantity in available stock
            offered_object.offered_stock.under_offer_quantity_in_kg -= offered_object.offered_sold_or_declined_quantity_kg
            offered_object.offered_stock.available_quantity_in_kg += offered_object.offered_sold_or_declined_quantity_kg
            offered_object.offered_stock.save()
            return redirect('existing_offers')
        elif request.POST.get('changeOfferRedirect') == "1":
            # this redirects to a change offer form
            return redirect('modify_existing_offer', offer_id=offered_object.id, mess='f')
        elif request.POST.get('return') == "1":
            return redirect('existing_offers')


@login_required
def modify_existing_offer(request, offer_id, mess):
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
    my_offer_to_change = OffersLog.objects.filter(id=offer_id).get()
    customers = Customers.objects.filter(salesperson_owning_account=request.user)
    # here I want the whole quantity, available pus what was originally offered
    kg_available_with_the_ones_added_in_the_offer = my_offer_to_change.offered_sold_or_declined_quantity_kg + my_offer_to_change.offered_stock.available_quantity_in_kg
    if request.method == 'GET':
        date_of_offer_string = str(my_offer_to_change.date_of_offer)
        return render(request, 'aged/modify_existing_offer.html',
                      {'offer': my_offer_to_change,
                       'customers': customers,
                       'whole_quantity': kg_available_with_the_ones_added_in_the_offer,
                       'date_of_offer_string': date_of_offer_string,
                       'message': message})
    elif request.method == 'POST':
        # check that the actual quantity (offered + free) is still available (nobody else offered the quantity while
        # form was filled)
        if kg_available_with_the_ones_added_in_the_offer >= int(request.POST.get('quantity')):
            # get the quantities into variables
            old_offer_kg = my_offer_to_change.offered_sold_or_declined_quantity_kg
            new_offer_kg = int(request.POST.get('quantity'))
            already_offered_kg = my_offer_to_change.offered_stock.under_offer_quantity_in_kg
            all_available_stock_of_that_product_kg = my_offer_to_change.offered_stock.available_quantity_in_kg
            # AvailableStock adjust under offer quantity and available quantity
            # subtract the old offered qty from total offered qty (nullifying the previous transaction),
            # and then add the new offer value (which can be bigger or smaller than the original one)
            my_offer_to_change.offered_stock.under_offer_quantity_in_kg = (already_offered_kg - old_offer_kg) + new_offer_kg
            # add to available quantity the previously offered qty (practically nullifying the transaction),
            # then subtract the new offered quantity
            my_offer_to_change.offered_stock.available_quantity_in_kg = (all_available_stock_of_that_product_kg + old_offer_kg) - new_offer_kg

            # Add the other values from the form
            my_offer_to_change.customer_that_received_offer = Customers.objects.filter(id=request.POST.get('customer')).get()
            my_offer_to_change.offered_sold_or_declined_quantity_kg = request.POST.get('quantity')
            my_offer_to_change.discount_offered_percents = request.POST.get('discount_in_percent')
            my_offer_to_change.price_per_kg_offered = request.POST.get('price')
            my_offer_to_change.date_of_offer = request.POST.get('date_of_offer')
            my_offer_to_change.expiration_date_of_offer = datetime.datetime.strptime(request.POST.get('date_of_offer'), '%Y-%m-%d').date() + datetime.timedelta(days=7)

            # Save modifications
            my_offer_to_change.offered_stock.save()
            my_offer_to_change.save()

            return redirect('offer_completed', offer_id=offer_id)
        else:
            # if quantity is too low, is adjusted and the form is returned
            return redirect('modify_existing_offer', offer_id=my_offer_to_change.id, mess='t')

# Opens the page where superusers can see the reports of who sold what, what is under offer, declined, etc
@user_passes_test(lambda u: u.is_superuser)
def superuser_reports(request):
    """
    The function displays and manages superuser report and various filters
    """
    # you will be served a page where the value will be prefilled
    # (ie. if you filter by Sarah the filter will stay on Sarah)
    # that is what the dict does
    preselect_values = dict()
    preselect_values['salesperson'] = 'All'
    preselect_values['state'] = 'All'
    preselect_values['start'] = ''
    preselect_values['end'] = ''
    # the standard date is between 60 days in the past and 30 days in the future (if someone prepared an offer
    # for next week)
    today_plus_30_days_end_of_interval = str(datetime.datetime.today().date() + datetime.timedelta(days=30))
    today_minus_60_days_beginning_date_of_interval = str(datetime.datetime.today().date() - datetime.timedelta(days=60))
    list_of_offers_corresponding_to_the_interval = OffersLog.objects.filter(date_of_offer__range=[today_minus_60_days_beginning_date_of_interval, today_plus_30_days_end_of_interval]).all()

    # create a set to eliminate name duplications (ie if Sarah has multiple offers, her name should only appear once)
    # this is used in the drop-down where you can filter by name
    all_users_with_offers = set()
    # this is for offer status drop down - if no offer is sold for example, no sold offer option will appear in the
    # drop-down
    all_offer_status = set()
    # populez seturile
    for offer in list_of_offers_corresponding_to_the_interval:
        all_users_with_offers.add(offer.sales_rep_that_made_the_offer.username)
        all_offer_status.add(offer.offer_status)

    # seturile nu sunt ordonate si nu contin varianta 'All', asa ca le fac lista, sortez si adaug 'All'
    all_users_with_offers = list(all_users_with_offers)
    all_users_with_offers.sort()
    all_users_with_offers.insert(0, 'All')

    all_offer_status = list(all_offer_status)
    all_offer_status.sort()
    all_offer_status.insert(0, 'All')

    if request.method == 'POST':
        stateOfOffers = request.POST.get('offerStatus')
        preselect_values['state'] = stateOfOffers

        name_of_user = request.POST.get('nameOfUser')
        preselect_values['salesperson'] = name_of_user

        start = request.POST.get('startDate')
        end = request.POST.get('endDate')

        # no start or end date provided in the time filter
        if start == '' and end =='':
            # go to standard 60 days in the past and 30 in the future
            start = today_minus_60_days_beginning_date_of_interval
            end = str(datetime.datetime.today().date() + datetime.timedelta(days=30))
        # start, no end
        elif start != '' and end == '':
            end = str(datetime.datetime.today().date() + datetime.timedelta(days=30))
        # end no start
        elif start == '' and end != '':
            start = today_minus_60_days_beginning_date_of_interval
        # start and end
        elif start != '' and end != '':
            pass

        preselect_values['start'] = start
        preselect_values['end'] = end

        # shows a particular user in the time interval
        if name_of_user != 'All':
            id_of_user = User.objects.filter(username=name_of_user).get().id
            list_of_offers_corresponding_to_the_interval = OffersLog.objects.filter(date_of_offer__range=[start, end],
                                                                                    sales_rep_that_made_the_offer=id_of_user).all()
            if stateOfOffers != 'All':
                list_of_offers_corresponding_to_the_interval = OffersLog.objects.filter(date_of_offer__range=[start, end],
                                                                                        sales_rep_that_made_the_offer=id_of_user,
                                                                                        offer_status=stateOfOffers).all()

        # show all users in the item interval
        elif name_of_user == 'All':
            list_of_offers_corresponding_to_the_interval = OffersLog.objects.filter(date_of_offer__range=[start, end]).all()
            if stateOfOffers != 'All':
                list_of_offers_corresponding_to_the_interval = OffersLog.objects.filter(date_of_offer__range=[start, end],
                                                                                        offer_status=stateOfOffers).all()

    return render(request,
                  'aged/superuser_reports.html',
                  {'list_of_offers_corresponding_to_the_interval': list_of_offers_corresponding_to_the_interval,
                          'all_users_with_offers': all_users_with_offers,
                          'all_offer_status': all_offer_status,
                          'preselect_values': preselect_values})

@login_required
def stock_help(request):
    return render(request, 'aged/help.html')


@login_required
@user_passes_test(lambda u: u.get_username() == 'Testbot')
def run_tasks(request):
    """
    Requires a user called Testbot
    Removes expired stock
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

    if not code_already_run_today():
        # Delete expired products from available stock + mark the offers as containing expired stock
        delete_expired_stock_and_mark_offered_as_stock_expired()
        find_offers_that_expire_today_and_return_the_quantity_to_available_stock()

    return render(request, 'aged/teste.html')
