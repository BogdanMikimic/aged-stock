from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from .models import *
from django.contrib.auth.decorators import user_passes_test
from django.core.files.storage import FileSystemStorage # deals with file stored on drive
from django.http import HttpResponse # returns files to download
from .lab import Aged_stock
from .lab.writePdfOffer import PdfOfferCreator
from .lab.AgedMailSender import MailSender
import datetime
import textwrap
from .lab.Sales_people_and_their_accounts2 import only_one_tab_check, \
    check_spreadsheet_contains_data, \
    return_data_frame_without_empty_rows_and_cols,\
    check_headers,\
    check_salespeople_in_database,\
    create_customer_care_accounts, \
    create_customer_accounts,\
    do_not_use_in_production_automatic_accounts_creation

# Homepage. Returnuie pagina de user sau superuser, depinde cine o acceseaza
# In ambele cazuri pagina contine doar linkuri spre alte sectiuni
@login_required
def homepage(request):
    if request.user.is_superuser:
        return render(request, 'aged/superuserhome.html')
    else:
        return render(request, 'aged/userhome.html')


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



    return render(request, 'aged/superuserreports.html', {'objects':obj, 'allUsersWithOffers':allUsersWithOffers, 'allOfferStatus':allOfferStatus, 'preselectValues':preselectValues})


# asta e pagina care arata tabelul cu toate produsele avalialable si under offer
@login_required
def userseallstock(request):
    # push materials to template to use with custom tags in HTML and JS for filtering
    allMaterials = MaterialType.objects.all()
    materialCsv = str()
    # create a CSV like list of materials to feed to a hidden tag and use it in js
    for number, mat in enumerate(allMaterials):
        if number+1 < 11:
            materialCsv +=f'{mat.material_type},'
        else:
            materialCsv +=f'{mat.material_type}'

    # retreive all stock that was offered or sold
    # do not show expired stock
    touchedStock = OffersLog.objects.filter(stock_expired=False)
    # retreive all available stock
    freeStockAll = AvailableStock.objects.all().order_by('expiration_date')
    return render(request, 'aged/userseallstock.html', {'freeStockAll' : freeStockAll, 'touchedStock' : touchedStock, 'materiale' : allMaterials, 'materialCsv' : materialCsv})


# pagina in care userul face oferta, care e trecuta in baza de date
@login_required
def usersmakeoffer(request, itm_id):
    stock_item = AvailableStock.objects.filter(id = itm_id).get()
    customers = Customers.objects.filter(salesperson_owning_account=request.user.id).order_by('customer_name')
    theSpecificStock = AvailableStock.objects.filter(id = itm_id).get()

    if request.method == 'GET':
        return render(request, 'aged/usersmakeoffer.html', {'stock_item':stock_item, 'customers':customers})

    elif request.method == 'POST':
        # check if the quantity is still available, if so log the offer
        # if not, redirect user
        if int(theSpecificStock.available_quantity_in_kg) >= int(request.POST.get('quantity')):

            dataOfertaStr = request.POST.get('date_of_offer')
            dateOfOffer = datetime.datetime.fromisoformat(dataOfertaStr).date()
            #expiration date este offer date + 7 zile
            expireDateOfOffer = dateOfOffer + datetime.timedelta(days=7)

            log_entry = OffersLog(
                        sales_rep_that_made_the_offer = User.objects.filter(username=request.user.get_username()).get(),
                        offered_stock = theSpecificStock,
                        offered_product = theSpecificStock.available_product,
                        customer_that_received_offer = Customers.objects.filter(id=int(request.POST.get('customer'))).get(),
                        offered_sold_or_declined_quantity_kg = request.POST.get('quantity'),
                        offer_status = 'Offered',
                        discount_offered_percents = request.POST.get('discount_in_percent'),
                        price_per_kg_offered = request.POST.get('price'),
                        date_of_offer = dateOfOffer,
                        #expiration date este offer date + 7 zile
                        expiration_date_of_offer = expireDateOfOffer
                        )

            log_entry.save()
            # BUG - copiaza under offer peste ce e scris deja ca si cantitate
            logOfferId = OffersLog.objects.latest('id').id
            stock_item.under_offer_quantity_in_kg += int(request.POST.get('quantity'))
            stock_item.available_quantity_in_kg -= int(request.POST.get('quantity'))
            stock_item.save()

            return redirect('userawesomeoffer', offerId = logOfferId)

        #if the quantity is no longer available because someone else took it
        else:
            return redirect('notenoughstock', stockId=stock_item.id)


@login_required
def userawesomeoffer (request, offerId):
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
    stock_item = AvailableStock.objects.filter(id=stockId).get()
    return render(request, 'aged/notenoghstockavailable.html', {'stock_item': stock_item})


@login_required
def userpendingoffers(request):
    # hide all touched stock older than 60 days (2 months), but show offers in the future (if someone decides to make the offer available from tomorrow)
    azi = datetime.datetime.today()
    sixtyDaysAgo = (azi - datetime.timedelta(days=60)).date()
    pending = OffersLog.objects.filter(date_of_offer__gte=sixtyDaysAgo, sales_rep_that_made_the_offer=request.user).all().order_by('offer_status')
    return render(request, 'aged/userpendingoffers.html', {'pending': pending})


# this it is only available to me (main file to upload spreadsheets)
@user_passes_test(lambda u: u.get_username() == 'Mikimic')
def fileupload(request):
    return render(request, 'aged/fileupload.html')


# this it is only available to me (file to upload salespeople, customer care people and company names .xlsx file)
@login_required
@user_passes_test(lambda u: u.get_username() == 'Mikimic')
def salespeopleupload(request):
    # dupa ce uploadez si citesc ce e in excel verific ce e in baza de date.
    # Singurele lucruri care trebe facute de mana sunt conturile userilor
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
            # pass
            create_customer_care_accounts(dataframe)
            create_customer_accounts(dataframe)
            return render(request, 'aged/salespeopleupload.html')


# this it is only available to me (file to upload aged stock .xlsx file)
@login_required
@user_passes_test(lambda u: u.get_username()=='Mikimic')
def agedstockupload(request):
    if request.method == 'GET':
        return render(request, 'aged/agedstockupload.html')
    elif request.method == 'POST':
        # upload file, read content, delete file - retrun content as dict
        file_name = 'stock.xlsx'
        file_2 = request.FILES['file_2']
        obiect_fisier = FileSystemStorage()
        obiect_fisier.save(file_name, file_2)
        # Check if file was already uploaded
        dbDataCreatFileListDict = CheckIfFileWasAlreadyUploaded.objects.values()
        dbDataCreatFileList = list()
        for dictionar in dbDataCreatFileListDict:
            dbDataCreatFileList.append(dictionar['data_creare_fisier'])
        from openpyxl import load_workbook
        wb = load_workbook(f'media/{file_name}')
        dataCreatFisier = str(wb.properties.created)
        if dataCreatFisier in dbDataCreatFileList:
            message = 'already uploaded'
            obiect_fisier.delete(file_name)
            # return render(request, 'aged/agedstockupload.html', {'message':message})
        else:
            newDate = CheckIfFileWasAlreadyUploaded(data_creare_fisier=dataCreatFisier)
            newDate.save()
            aged_stock_as_lista_de_dict = Aged_stock.AgedStock(f'media/{file_name}').runAll()
            obiect_fisier.delete(file_name)
            # brand, material group (adica tipul de material, gen ciocolata, nuci, etc) si stock location sunt in tabele separate fiecare
            # de asta verific daca ele exista deja in baza de date
            # pentru asta creez niste liste separate, caut ce valori unice (care nu se repeta) am in excel
            # scot listele si din baza de date si verific intre ele ce nu exista
            # toate astea sunt legate de un "Product"

            # liste pt excel
            brands_list_din_xcel = list()
            material_group_list_din_xcel = list()
            stock_location_din_xcel = list()
            # liste pt baza de date
            brands_list_din_db = list()
            material_group_list_din_db = list()
            stock_location_list_din_db = list()

            # retrievuie datele din baza de date si adauga-le intr-o lista
            db_brands_list_dict = Brands.objects.values()
            for br in db_brands_list_dict:
                brands_list_din_db.append(br['brand'])

            db_material_group_list_dict = MaterialType.objects.values()
            for mg in db_material_group_list_dict:
                material_group_list_din_db.append(mg['material_type'])

            db_location_list_dict = LocationsForStocks.objects.values()
            for loc in db_location_list_dict:
                stock_location_list_din_db.append(loc['location_of_stocks'])

            # verifica entry-urile unice (elimina ce se repeta) si verifica daca nu sunt deja in baza de date
            # (verifica doar daca exista brandul in tabelul Brands, grupul de materiale in tabelul MaterialType si locatia in LocationsForStocks)
            for itm in aged_stock_as_lista_de_dict:
                if itm['Brand'] not in brands_list_din_xcel and itm['Brand'] not in brands_list_din_db:
                    brands_list_din_xcel.append(itm['Brand'])
                if itm['Matl Group'] not in material_group_list_din_xcel and itm['Matl Group'] not in material_group_list_din_db:
                    material_group_list_din_xcel.append(itm['Matl Group'])
                if itm['Stor loc'] not in stock_location_din_xcel and itm['Stor loc'] not in stock_location_list_din_db:
                    stock_location_din_xcel.append(itm['Stor loc'])
            # daca am branduri, tipul de material si locatia care nu sunt in baza de data, adauga-le in baza de date
            if len(brands_list_din_xcel)>0:
                for bra in brands_list_din_xcel:
                    brandul = Brands(brand=bra)
                    brandul.save()

            if len(material_group_list_din_xcel)>0:
                for mat in material_group_list_din_xcel:
                    materialul = MaterialType(material_type=mat)
                    materialul.save()

            if len(stock_location_din_xcel)>0:
                for loca in stock_location_din_xcel:
                    locatiunea = LocationsForStocks(location_of_stocks=loca)
                    locatiunea.save()

            # urca toate in baza de date de product
            for prod in aged_stock_as_lista_de_dict:
                if Products.objects.filter(cod_material = prod['Material']).exists() == False:
                    new_prod = Products(
                               cod_material = prod['Material'],
                               description = prod['Description'],
                               product_brand = Brands.objects.filter(brand=prod['Brand']).get(),
                               product_material_type = MaterialType.objects.filter(material_type=prod['Matl Group']).get()
                    )
                    new_prod.save()
            # curata lista
            azi = datetime.date.today()
            data_exp_stoc_bd = AvailableStock.objects.values()
            identification_values_of_stock = list()
            # (la "if" mai jos) (redundant - am un task care curata zilnic prod expirate) verifica ce stocuri sunt expirate din stocurile existente in baza de date, si sterge-le. However functioneaza doar a doua oara cand urc produse in baza de date, pt ca verifica in database, nu in ce urc pt ca nu e de asteptat sa fie urcate stocuri expirate in baza de date
            # (la "elif" mai jos) sterge toate stocurile neatinse (not under offer, nor sold)- verifica daca cantitatea initala == cantitatea actuala
            # (la "else") - la else sunt stocurile neexpirate si "atinse" (under offer sau sold) pe care le pastrez, dar acum trebuie sa le sterg din lista
            # generata din exel (adica daca cumva acelasi produs re-apare in excelul nou)
            for stock0 in data_exp_stoc_bd:
                if azi >= stock0['expiration_date']:
                    expiredStockId = stock0['id']
                    AvailableStock.objects.get(id = stock0['id']).delete()
                elif stock0['original_quantity_in_kg'] == stock0['available_quantity_in_kg']:
                    AvailableStock.objects.get(id = stock0['id']).delete()
                else:
                    idOfField = [f'{Products.objects.get(id = stock0["available_product_id"])}', stock0["expiration_date"], stock0["batch"]]
                    for dictSet in aged_stock_as_lista_de_dict:
                        if idOfField[0] in list(dictSet.values()):
                            if idOfField[1] in list(dictSet.values()):
                                if idOfField[2] in list(dictSet.values()):
                                    aged_stock_as_lista_de_dict.pop(aged_stock_as_lista_de_dict.index(dictSet))

            # urca toate in baza de date Available stock
            for stock in aged_stock_as_lista_de_dict:
                new_stock = AvailableStock (
                            available_product = Products.objects.filter(cod_material = stock['Material']).get(),
                            stock_location = LocationsForStocks.objects.filter(location_of_stocks = stock['Stor loc']).get(),
                            expiration_date = stock['Expiration date'],
                            batch = stock['Batch'],
                            original_quantity_in_kg = stock['Quantity'],
                            available_quantity_in_kg = stock['Quantity']
                            )
                new_stock.save()
                message = 'uploaded succesfully'

        return render(request, 'aged/agedstockupload.html', {'message':message})


@login_required
def changeofferedstatus(request, offer_id):
    # check if product is expired!!!!!!!!!!!!!!!!!
    # change the status of the offer
    offeredObject = OffersLog.objects.filter(id=offer_id).get()
    if request.method == 'GET':
        return render(request, 'aged/changeofferedstatus.html', {'object':offeredObject})
    elif request.method == 'POST':
        # stockObject =
        azi = datetime.date.today()
        if request.POST.get('sold') == "1":
            # modific in offers log
            offeredObject.offer_status = 'Sold'
            offeredObject.date_of_outcome = azi
            offeredObject.expiration_date_of_offer = None
            offeredObject.save()
            # modific in available stock
            offeredObject.offered_stock.under_offer_quantity_in_kg -= offeredObject.offered_sold_or_declined_quantity_kg
            offeredObject.offered_stock.sold_quantity_in_kg += offeredObject.offered_sold_or_declined_quantity_kg
            offeredObject.offered_stock.save()
            return redirect('userpendingoffers')
        elif request.POST.get('declined') == "1":
            # modific in offered stoc
            offeredObject.offer_status = 'Declined'
            offeredObject.date_of_outcome = azi
            offeredObject.expiration_date_of_offer = None
            offeredObject.save()
            # modific in available stock
            offeredObject.offered_stock.under_offer_quantity_in_kg -= offeredObject.offered_sold_or_declined_quantity_kg
            offeredObject.offered_stock.available_quantity_in_kg += offeredObject.offered_sold_or_declined_quantity_kg
            offeredObject.offered_stock.save()
            return redirect('userpendingoffers')
        elif request.POST.get('changeOfferRedirect') == "1":
            return redirect('changeoffer', offer_id=offeredObject.id, mess='f')
        elif request.POST.get('return') == "1":
            return redirect('userpendingoffers')



@login_required
def changeoffer(request, offer_id, mess):
    # mesajul e folosit daca cumva in timp ce oferta e schimbata, cineva ofera acelasi produs si cantitatea ramasa e mai mica decat se vrea oferit
    if mess == 'f':
        message = ''
    else:
        message = 'Seems like someone beat you to it and there is not enogh stock left to do this offer. I have adjusted the maximum quantity to display the correct available quantity.'
    myOfferToChange = OffersLog.objects.filter(id=offer_id).get()
    customers = Customers.objects.filter(salesperson_owning_account = request.user)
    # aici vreau sa returnui in template nu cantitatea maxima existenta, ci cantitatea maxima plus ce e deja oferit
    kgAvailableWithTheOnesAddedInTheOffer = myOfferToChange.offered_sold_or_declined_quantity_kg + myOfferToChange.offered_stock.available_quantity_in_kg
    if request.method == 'GET':
        # nu ii place auto-fill-ul tagului imput de tip date sa primeasca obiect de gen date, are nevoie de string
        dateOfOfferString = str(myOfferToChange.date_of_offer)
        return render(request, 'aged/changeoffer.html', {'offer':myOfferToChange, 'customers':customers, 'wholeQuantity':kgAvailableWithTheOnesAddedInTheOffer, 'dateOfOfferString':dateOfOfferString, 'message':message })
    elif request.method == 'POST':
        # trebuie sa verific si daca este cantitate actuala suficienta si nu a luat-o cineva inainte
        if kgAvailableWithTheOnesAddedInTheOffer >= int(request.POST.get('quantity')):
            # imi scot ca variabile cantitatile cu care lucrez
            vecheaOfertaKg = myOfferToChange.offered_sold_or_declined_quantity_kg
            nouaOfertaKg = int(request.POST.get('quantity'))
            totalSubOfertaKg = myOfferToChange.offered_stock.under_offer_quantity_in_kg
            totalDisponibilKg = myOfferToChange.offered_stock.available_quantity_in_kg
            # modificari la AvailableStock (ajustari la under offer quantity si available qunatity)
            # scad din quantity under offer al stockului disponibil valoarea initiala (ca si cum oferta nu s-a facut vreodata), dupa care adaug oferta actuala
            myOfferToChange.offered_stock.under_offer_quantity_in_kg = (totalSubOfertaKg - vecheaOfertaKg) + nouaOfertaKg
            # adaug la available quantity a stockului cantitatea care era oferita (ca si cum oferta nu s-a intamplat), dupa care scad noua cantitate
            myOfferToChange.offered_stock.available_quantity_in_kg = (totalDisponibilKg + vecheaOfertaKg) - nouaOfertaKg

            # Adaug noile valori la oferta (modific oferta)
            myOfferToChange.customer_that_received_offer = Customers.objects.filter(id=request.POST.get('customer')).get()
            myOfferToChange.offered_sold_or_declined_quantity_kg = request.POST.get('quantity')
            myOfferToChange.discount_offered_percents = request.POST.get('discount_in_percent')
            myOfferToChange.price_per_kg_offered = request.POST.get('price')
            myOfferToChange.date_of_offer = request.POST.get('date_of_offer')
            myOfferToChange.expiration_date_of_offer = datetime.datetime.strptime(request.POST.get('date_of_offer'), '%Y-%m-%d').date() + datetime.timedelta(days=7)

            # Salvez modificarile in ambele tabele
            myOfferToChange.offered_stock.save()
            myOfferToChange.save()

            return redirect('userawesomeoffer', offerId=offer_id)
        else:
            return redirect('changeoffer', offer_id=myOfferToChange.id, mess='t')


@login_required
def help(request):
    return render(request, 'aged/help.html')


# remove expired offers and expired products from all stock table, all offers older than 365 days from offers log and send daily backups
def task1(request):
    print('Am primit request la pagina tasks 1')
    # testeaza daca exista oferte expirate, face din nou cantitatea blocata ca available in stocuri
    # pagina e chemata automat in Python anywere - exista o functie care permite rularea automata
    # a unui fisier pe care il doresc in cazul meu fisierul se numeste fisier myTasks.py
    # si in fiserul asta creez un request spre pagina asta, ruland automat si codul
    # ca sa nu ruleze de mai multe ori am facut in models un aFostVerificatAzi care stocheaza data de azi

    # verifica daca codul nu a rulat deja azi
    azi = datetime.date.today()
    alreadyDoneToday = False
    dataInDb = AFostVerificatAzi.objects.all()
    for itm in dataInDb:
        if itm.expiredOferedStock == azi:
            alreadyDoneToday = True

    if alreadyDoneToday == False:
        # inregistrea operatiunea ca facuta azi
        dt = AFostVerificatAzi(expiredOferedStock = azi)
        dt.save()

        # TASK 1! cauta ofertele care expira azi si le schimba statusul la expirat + returnuie cantitatea alocata in stocul liber
        expiredOfferStockToReturn = OffersLog.objects.filter(expiration_date_of_offer__lt=azi).all() # caveat - codul ruleaza la 4 dimineata, asa ca nu sterg produsul in ziua in care expira, ci in dimineata zilei urmatoare
        for stock in expiredOfferStockToReturn:
            # doar ca sa ma asigur ca nu operez din gresealade doua ori pe acelasi stock, verific sa nu fie 'Offer expired'
            if stock.offer_status != 'Offer Expired':
                kgBlockedInOffer = stock.offered_sold_or_declined_quantity_kg

                # verifica daca stocul nu a expirat si a fost sters (this should not happen in the wild)
                if stock.offered_stock != None: # daca stocul e expirat, e None
                    # returnuie cantitatea din oferta expirata in stockul original
                    # in stocul original sunt mai multe fielduri care arata unde e stocul
                    # (o parte din stock poate fi disponibila, o alta e under offer, o alta e sold)
                    # bucata asta de cod cauta sa returnuie in stocul disponibil (NU in logul cu oferte)
                    # cantitatea oferita
                    availabelStockObject = stock.offered_stock
                    availabelStockObject.under_offer_quantity_in_kg -= kgBlockedInOffer
                    availabelStockObject.available_quantity_in_kg += kgBlockedInOffer
                    availabelStockObject.save()
                else: # daca stocule e expirat
                    stock.stock_expired = True
                # modifica statusul si data outcomeului in Offers log
                stock.offer_status = 'Offer Expired'
                stock.date_of_outcome = azi - datetime.timedelta(days=1) # practic stocul a explicat ieri seara, dar eu il verific a doua zi dimineata
                stock.save()


        # TASK 2 - sterge toate produsele expirate din oferte + marcheaza stocul ca expirat
        data_exp_stoc_bd = AvailableStock.objects.filter(expiration_date__lt=azi).all() # caveat - codul ruleaza la 4 dimineata, asa ca nu sterg produsul in ziua in care expira, ci in dimineata zilei urmatoare
        for stock0 in data_exp_stoc_bd:
            expiredStockId = stock0
            listaOferteCuStocExpirat = OffersLog.objects.filter(offered_stock = expiredStockId).all()
            for itm in listaOferteCuStocExpirat:
                itm.stock_expired = True
                itm.save()
            stock0.delete()

        # TASK 3 - sterge din offers log toate ofertele mai vechi de un an (365 zile), doar ca codul ruleaza a doua zi dimineata
        dataDeAcumUnAn = azi - datetime.timedelta(days=366)
        oferteMaiVechiDe365Zile = OffersLog.objects.filter(date_of_offer__lte=dataDeAcumUnAn).all()
        if len(oferteMaiVechiDe365Zile)>0: # daca exista oferte mai vechi
            for oferta in oferteMaiVechiDe365Zile:
                oferta.delete()

        # TASK 4 - trimite-mi zilnic un mail pe adresa mea cu un csv cu datele
        # builds 2 csvs - one with all time offers log, one with current stock with offers

        # build all time stock CSV
        logCsvTxt = 'Transaction ID|Sales rep|Offered stock(ID),Offered SKU|Customer|Offered sold or declined kg|Offer status|Discount %,Price/kg|Total Price|Offer Date|Offer expiration date|Date of outcome|Stock expired?\n'
        logDb = OffersLog.objects.all()
        countTransactions = len(logDb)
        for record in logDb:
            totalPrice = round((record.offered_sold_or_declined_quantity_kg * record.price_per_kg_offered), 2)
            if record.offered_stock == None: #stocul oferit nu mai exista
                offeredStock = 'Stock no longer exists'
            else:
                offeredStock = record.id # id of stock that was offered
            logCsvTxt += f'{record.id}|{record.sales_rep_that_made_the_offer.username}|{offeredStock}|{record.offered_product.cod_material}|{record.customer_that_received_offer.customer_name}|{record.offered_sold_or_declined_quantity_kg}|{record.offer_status}|{record.discount_offered_percents}|{record.price_per_kg_offered}|{totalPrice}|{record.date_of_offer}|{record.expiration_date_of_offer}|{record.date_of_outcome}|{record.stock_expired}\n'
        # write CSV
        csv1Name = f'Log({len(logDb)}transactions)-{azi}.csv'
        with open(f'media/{csv1Name}', 'wt') as logCSV:
            logCSV.write(logCsvTxt)

        # build current available stocks and offers csv

        # logic: goes trough all stocks, but if a stock has quantities under offer or sold
        # goes and checks on the log who has done transactions on that particular stock and
        # writes the same stock in multiple lines, one line for each salesperson that has
        # an active offer on the stock and one for each person that sold parts of the stock

        # step 1 - build CSV heading -made it multiple lines for readability
        stockCSVtxt = 'Stock ID|'
        stockCSVtxt += 'SKU|'
        stockCSVtxt += 'Description|'
        stockCSVtxt += 'Brand|'
        stockCSVtxt += 'Material type|'
        stockCSVtxt += 'Location|'
        stockCSVtxt += 'Expiration date|'
        stockCSVtxt += 'Batch|'
        stockCSVtxt += 'Original qty (kg)|'
        stockCSVtxt += 'Total under offer qty(kg)|'
        stockCSVtxt += 'Total sold qty(kg)|'
        stockCSVtxt += 'Available qty (kg)|'
        # this is the second part of the csv
        stockCSVtxt += 'Stock touched?|'
        stockCSVtxt += 'Person that has an active offer|'
        stockCSVtxt += 'Offered quantity (kg)|'
        stockCSVtxt += 'Person that sold some stock|'
        stockCSVtxt += 'Sold quantity (kg)|'
        stockCSVtxt += '\n'

        # step 2 - function that writes the first part of the CSV (all the data up to persons that made the offer)
        def writeFirstPartOfCSVLine(st):
            # requires the stock object as argument
            firstPartOfLine = ''
            firstPartOfLine += f'{st.id}|'
            firstPartOfLine += f'{st.available_product.cod_material}|'
            firstPartOfLine += f'{st.available_product.description}|'
            firstPartOfLine += f'{st.available_product.product_brand}|'
            firstPartOfLine += f'{st.available_product.product_material_type}|'
            firstPartOfLine += f'{st.stock_location}|'
            firstPartOfLine += f'{st.expiration_date}|'
            firstPartOfLine += f'{st.batch}|'
            firstPartOfLine += f'{st.original_quantity_in_kg}|'
            firstPartOfLine += f'{st.under_offer_quantity_in_kg}|'
            firstPartOfLine += f'{st.sold_quantity_in_kg}|'
            firstPartOfLine += f'{st.available_quantity_in_kg}|'
            return firstPartOfLine

        def writesSecondPartOfCSVLine(st):
            # checks if there are parts of the stock under offer or sold,
            # and for each part offered or sold is constructing a csv line with the identification
            # of the user that has the offer/sold and the offered/sold qty
            secondPartOfLine = ''
            # check if parts of the stock was offered or sold
            if st.under_offer_quantity_in_kg >0 or st.sold_quantity_in_kg >0:
                # retreives all people that made offers or sold that stock
                stockUnderOffer = OffersLog.objects.filter(offered_stock = st.id).all()
                for touchStock in stockUnderOffer:
                    if touchStock.offer_status == 'Offered': # check for offer
                        secondPartOfLine += writeFirstPartOfCSVLine(st)
                        secondPartOfLine += 'Yes|'
                        secondPartOfLine += f'{touchStock.sales_rep_that_made_the_offer.username}|'
                        secondPartOfLine += f'{touchStock.offered_sold_or_declined_quantity_kg}|'
                        secondPartOfLine += 'None|'
                        secondPartOfLine += 'None|'
                        secondPartOfLine += '\n'

                    elif touchStock.offer_status == 'Sold':
                        secondPartOfLine += writeFirstPartOfCSVLine(st)
                        secondPartOfLine += 'Yes|'
                        secondPartOfLine += 'None|'
                        secondPartOfLine += 'None|'
                        secondPartOfLine += f'{touchStock.sales_rep_that_made_the_offer.username}|'
                        secondPartOfLine += f'{touchStock.offered_sold_or_declined_quantity_kg}|'
                        secondPartOfLine += '\n'

            else:
                secondPartOfLine += writeFirstPartOfCSVLine(st)
                secondPartOfLine += 'No|'
                secondPartOfLine += 'None|'
                secondPartOfLine += 'None|'
                secondPartOfLine += 'None|'
                secondPartOfLine += 'None|'
                secondPartOfLine += '\n'
            return secondPartOfLine

        # retreive all stock from the database and call the functions that build the csv
        stockDb = AvailableStock.objects.all()
        for st in stockDb: #
            info =  writesSecondPartOfCSVLine(st)
            stockCSVtxt += info

        # write second csv
        csv2Name = f'ProductStockToDate-{azi}.csv'
        with open(f'media/{csv2Name}', 'wt') as stockCSV:
            stockCSV.write(stockCSVtxt)

        # attach CSV with log to email
        # attach CSV with stock to email
        # send email
        MailSender(recipient='bogdan_chira',
                   titlu=f'Aged Stock Reports {azi}',
                   continut=f'Aged Stock Reports{azi}',
                   numeAtasament1=csv1Name,
                   numeAtasament2=csv2Name)

        # delete csv files from server
        handlerFisereDrive = FileSystemStorage()
        handlerFisereDrive.delete(f'{csv1Name}')
        handlerFisereDrive.delete(f'{csv2Name}')

    return render(request, 'aged/teste.html')
