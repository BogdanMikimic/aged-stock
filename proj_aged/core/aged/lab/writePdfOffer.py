#creates a pdf with an offer and saves in media
#object imported in views
class PdfOfferCreator:
    def __init__(self,
                 pdfTitle,
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
                 ):
        from fpdf import FPDF
        self.tilte = pdfTitle
        self.salesPersonName = salesPersonName
        self.customerServiceRepName = customerServiceRepName
        self.customerName = customerName
        # change dates from yyyy-mm-dd format to dd-mm-yyyy
        _tempDate = str(dateOfOffer).split('-')
        self.dateOfOffer = f'{_tempDate[2]}-{_tempDate[1]}-{_tempDate[0]}'
        _tempDate = str(expireDateOfOffer).split('-')
        self.expireDateOfOffer =  f'{_tempDate[2]}-{_tempDate[1]}-{_tempDate[0]}'
        _tempDate = str(stockExpirationDate).split('-')
        self.stockExpirationDate =  f'{_tempDate[2]}-{_tempDate[1]}-{_tempDate[0]}'

        self.offeredProduct = offeredProduct
        self.batch = batch
        self.offeredQuantity = offeredQuantity
        self.offeredPricePerKilo = offeredPricePerKilo
        self.productType = productType
        self.productBrand = productBrand

        self.txtAgedStockTitle = "AGED STOCK OFFER"

        self.txtReferal = f'''
Date of offer: {self.dateOfOffer}
Offer expiration date: {self.expireDateOfOffer}
To: {self.customerName}
'''
        self.txtOffer = f'''
Dear customer,

We would like to offer you {self.offeredQuantity}kg of our {self.offeredProduct} aged stock product:
Product type: {self.productType}
Product brand: {self.productBrand}
Batch: {self.batch}
Product expiration date: {self.stockExpirationDate}
Price/kg: £{self.offeredPricePerKilo}
TOTAL price: £{float(self.offeredQuantity)*float(self.offeredPricePerKilo)}

Customer care agent: {self.customerServiceRepName}

Kind regards,

{self.salesPersonName}
        '''
        class PDF(FPDF):
            def header(self):
                # Logo
                canvas_width = 210
                img ='media/logo.jpg'
                width_of_image = 100
                poz_pe_x = 10
                poz_pe_y = 10
                self.image(img, poz_pe_x , poz_pe_y, width_of_image)

            # write disclaimer in footer
            def footer(self):
                # draw a line at the bottom
                self.set_line_width = 3
                self.set_draw_color(r=50, g=50, b=50) # grey
                y1 = 280 # A4 height is 297 height, line 17 mm above bottom
                y2 = y1 # this is the inclination if I want to draw a diagonal line
                x1 = 0 # at the begining of doc on width
                x2 = 210 # all the way to the end -  A4 width is 210
                self.line(x1, y1, x2, y2)
                # move cursor down
                cursorX = 10 # margin is by default 10
                cursorY = 283 # A4 height is 297
                self.set_xy(cursorX, cursorY)
                # write disclaimer
                self.set_font('helvetica', '', 6)
                self.set_text_color(r=225, g=37, b=27)
                textWidth = 190
                textHeight = 3
                border = 0 #0 is none
                alignText = 'L' #left
                disclaimer = '''The above statements reflect our current assumptions to the best of our knowledge. However, unpredictable circumstances can arise to change the environment on which  the statements were based, therefore, none of the above statements are intended to create any legally binding obligations on the part of Cocoa Lux or introduce any changes to the existing contractual relationship between you and Cocoa Lux, nor shall Cocoa Lux under any circumstances be liable for any damages whatsoever in case of deviations, adjustments or changes to the above statements in the future.'''
                self.multi_cell(textWidth, textHeight, disclaimer, border, alignText)
        # create PDF object
        self.myPdf = PDF(unit='mm',format='a4', orientation="P")

    def makePdf(self):
        # setup page
        self.myPdf.add_page()

        # setup initial text
        self.myPdf.set_font('helvetica', '', 14)
        self.myPdf.set_text_color(r=50, g=50, b=50)
        textWidth = 190
        textHeight = 8
        border = 0  #0 is none
        alignText = 'L'  #left


        # move cursor down
        cursorX = 10  # margin is by default 10
        cursorY = 20  # A4 height is 297
        self.myPdf.set_xy(cursorX, cursorY)

        # write refferal text (to: and date:)
        self.myPdf.multi_cell(textWidth, textHeight, self.txtReferal, border, alignText)

        # move cursor down
        cursorX = 10  # margin is by default 10
        cursorY = 70  # A4 height is 297
        self.myPdf.set_xy(cursorX, cursorY)

        # setup TITLE text
        self.myPdf.set_font('helvetica', 'B', 16)
        self.myPdf.set_text_color(r=225, g=37, b=27)
        textWidth = 190
        textHeight = 12
        alignText = 'C'  # center


        # write title text (aged stock offer)
        self.myPdf.multi_cell(textWidth, textHeight, self.txtAgedStockTitle, border, alignText)

        # move cursor down
        cursorX = 10  # margin is by default 10
        cursorY = 90  # A4 height is 297
        self.myPdf.set_xy(cursorX, cursorY)

        # setup body text
        self.myPdf.set_font('helvetica', '', 14)
        self.myPdf.set_text_color(r=50, g=50, b=50)
        textWidth = 190
        textHeight = 8
        border = 0  #0 is none
        alignText = 'L'  #left


        # write body text (what chocolate, quantity, price, etc)
        self.myPdf.multi_cell(textWidth, textHeight, self.txtOffer, border, alignText)

        self.myPdf.output(f'media/{self.tilte}.pdf')
