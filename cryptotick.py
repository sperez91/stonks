
from time import sleep
import argparse
from PIL import Image, ImageDraw, ImageFont
from sys import path
from IT8951 import constants
import os, random
import textwrap
import qrcode
import feedparser
import requests
import textwrap
import unicodedata
import re
import logging
import os
dirname = os.path.dirname(__file__)
configfile = os.path.join(os.path.dirname(os.path.realpath(__file__)),'config.yaml')


def print_system_info(display):
    epd = display.epd

    print('System info:')
    print('  display size: {}x{}'.format(epd.width, epd.height))
    print('  img buffer address: {:X}'.format(epd.img_buf_address))
    print('  firmware version: {}'.format(epd.firmware_version))
    print('  LUT version: {}'.format(epd.lut_version))
    print()

def beanaproblem(message):
#   A visual cue that the wheels have fallen off
    thebean = Image.open(os.path.join(picdir,'thebean.bmp'))
    epd = epd2in7.EPD()
    epd.Init_4Gray()
    image = Image.new('L', (epd.height, epd.width), 255)    # 255: clear the image with white
    draw = ImageDraw.Draw(image)
    image.paste(thebean, (60,15))
    draw.text((15,150),message, font=font_date,fill = 0)
    image = ImageOps.mirror(image)
    epd.display_4Gray(epd.getbuffer_4Gray(image))
#   Reload last good config.yaml
    with open(configfile) as f:
        config = yaml.load(f, Loader=yaml.FullLoader)

def getData(config):
    """
    The function to update the ePaper display. There are two versions of the layout. One for portrait aspect ratio, one for landscape.
    """
    logging.info("Getting Data")
    days_ago=int(config['ticker']['sparklinedays'])   
    endtime = int(time.time())
    starttime = endtime - 60*60*24*days_ago
    starttimeseconds = starttime
    endtimeseconds = endtime     
    # Get the price 

    if config['ticker']['exchange']=='default' or fiat!='usd':
        geckourl = "https://api.coingecko.com/api/v3/coins/markets?vs_currency="+fiat+"&ids="+whichcoin
        logging.info(geckourl)
        rawlivecoin = requests.get(geckourl).json()
        logging.info(rawlivecoin[0])   
        liveprice = rawlivecoin[0]
        pricenow= float(liveprice['current_price'])
    else:
        geckourl= "https://api.coingecko.com/api/v3/exchanges/"+config['ticker']['exchange']+"/tickers?coin_ids="+whichcoin+"&include_exchange_logo=false"
        logging.info(geckourl)
        rawlivecoin = requests.get(geckourl).json()
        liveprice= rawlivecoin['tickers'][0]
        if  liveprice['target']!='USD':
            logging.info("The exhange is not listing in USD, misconfigured - shutting down script")
            message="Misconfiguration Problem"
            beanaproblem(message)
            sys.exit()
        pricenow= float(liveprice['last'])
    logging.info("Got Live Data From CoinGecko")
    geckourlhistorical = "https://api.coingecko.com/api/v3/coins/"+whichcoin+"/market_chart/range?vs_currency="+fiat+"&from="+str(starttimeseconds)+"&to="+str(endtimeseconds)
    logging.info(geckourlhistorical)
    rawtimeseries = requests.get(geckourlhistorical).json()
    logging.info("Got price for the last "+str(days_ago)+" days from CoinGecko")
    timeseriesarray = rawtimeseries['prices']
    timeseriesstack = []
    length=len (timeseriesarray)
    i=0
    while i < length:
        timeseriesstack.append(float (timeseriesarray[i][1]))
        i+=1

    timeseriesstack.append(pricenow)
    return timeseriesstack

def makeSpark(pricestack):
    # Draw and save the sparkline that represents historical data

    # Subtract the mean from the sparkline to make the mean appear on the plot (it's really the x axis)    
    x = pricestack-np.mean(pricestack)

    fig, ax = plt.subplots(1,1,figsize=(10,3))
    plt.plot(x, color='k', linewidth=6)
    plt.plot(len(x)-1, x[-1], color='r', marker='o')

    # Remove the Y axis
    for k,v in ax.spines.items():
        v.set_visible(False)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.axhline(c='k', linewidth=4, linestyle=(0, (5, 2, 1, 2)))

    # Save the resulting bmp file to the images directory
    plt.savefig(os.path.join(picdir,'spark.png'), dpi=17)
    imgspk = Image.open(os.path.join(picdir,'spark.png'))
    file_out = os.path.join(picdir,'spark.bmp')
    imgspk.save(file_out) 
    plt.clf() # Close plot to prevent memory error


def updateDisplay(config,pricestack):
    """   
    Takes the price data, the desired coin/fiat combo along with the config info for formatting
    if config is re-written following adustment we could avoid passing the last two arguments as
    they will just be the first two items of their string in config 
    """
    days_ago=int(config['ticker']['sparklinedays'])   
    symbolstring=currency.symbol(fiat.upper())
    if fiat=="jpy":
        symbolstring="¥"
    pricenow = pricestack[-1]
    currencythumbnail= 'currency/'+whichcoin+'.bmp'
    tokenfilename = os.path.join(picdir,currencythumbnail)
    sparkbitmap = Image.open(os.path.join(picdir,'spark.bmp'))
#   Check for token image, if there isn't one, get on off coingecko, resize it and pop it on a white background
    if os.path.isfile(tokenfilename):
        logging.info("Getting token Image from Image directory")
        tokenimage = Image.open(tokenfilename)
    else:
        logging.info("Getting token Image from Coingecko")
        tokenimageurl = "https://api.coingecko.com/api/v3/coins/"+whichcoin+"?tickers=false&market_data=false&community_data=false&developer_data=false&sparkline=false"
        rawimage = requests.get(tokenimageurl).json()
        tokenimage = Image.open(requests.get(rawimage['image']['large'], stream=True).raw)
        resize = 100,100
        tokenimage.thumbnail(resize, Image.ANTIALIAS)
        new_image = Image.new("RGBA", (120,120), "WHITE") # Create a white rgba background with a 10 pizel border
        new_image.paste(tokenimage, (10, 10), tokenimage)   
        tokenimage=new_image
        tokenimage.thumbnail((100,100),Image.ANTIALIAS)
        tokenimage.save(tokenfilename)


    pricechange = str("%+d" % round((pricestack[-1]-pricestack[0])/pricestack[-1]*100,2))+"%"
    if pricenow > 1000:
        pricenowstring =format(int(pricenow),",")
    else:
        pricenowstring =str(float('%.5g' % pricenow))

    if config['display']['orientation'] == 0 or config['display']['orientation'] == 180 :
        epd = epd2in7.EPD()
        epd.Init_4Gray()
        image = Image.new('L', (epd.width, epd.height), 255)    # 255: clear the image with white
        draw = ImageDraw.Draw(image)              
        draw.text((110,80),str(days_ago)+"day :",font =font_date,fill = 0)
        draw.text((110,95),pricechange,font =font_date,fill = 0)
        # Print price to 5 significant figures
        draw.text((15,200),symbolstring+pricenowstring,font =font,fill = 0)
        draw.text((10,10),str(time.strftime("%H:%M %a %d %b %Y")),font =font_date,fill = 0)
        image.paste(tokenimage, (10,25))
        image.paste(sparkbitmap,(10,125))
        if config['display']['orientation'] == 180 :
            image=image.rotate(180, expand=True)


    if config['display']['orientation'] == 90 or config['display']['orientation'] == 270 :
        epd = epd2in7.EPD()
        epd.Init_4Gray()
        image = Image.new('L', (epd.height, epd.width), 255)    # 255: clear the image with white
        draw = ImageDraw.Draw(image)   
        draw.text((110,90),str(days_ago)+"day : "+pricechange,font =font_date,fill = 0)
        # Print price to 5 significant figures
 #       draw.text((20,120),symbolstring,font =fonthiddenprice,fill = 0)
        draw.text((10,120),symbolstring+pricenowstring,font =fontHorizontal,fill = 0)
        image.paste(sparkbitmap,(80,40))
        image.paste(tokenimage, (0,10))
        draw.text((95,15),str(time.strftime("%H:%M %a %d %b %Y")),font =font_date,fill = 0)
        if config['display']['orientation'] == 270 :
            image=image.rotate(180, expand=True)
#       This is a hack to deal with the mirroring that goes on in 4Gray Horizontal
        image = ImageOps.mirror(image)

#   If the display is inverted, invert the image usinng ImageOps        
    if config['display']['inverted'] == True:
        image = ImageOps.invert(image)
#   Send the image to the screen        
    epd.display_4Gray(epd.getbuffer_4Gray(image))
    epd.sleep()

def currencystringtolist(currstring):
    # Takes the string for currencies in the config.yaml file and turns it into a list
    curr_list = currstring.split(",")
    curr_list = [x.strip(' ') for x in curr_list]
    return curr_list

def _place_text(img, text, x_offset=0, y_offset=0,fontsize=40,fontstring="Forum-Regular"):
    '''
    Put some centered text at a location on the image.
    '''

    draw = ImageDraw.Draw(img)

    try:
        filename = os.path.join(dirname, './fonts/'+fontstring+'.ttf')
        font = ImageFont.truetype(filename, fontsize)
    except OSError:
        font = ImageFont.truetype('/usr/share/fonts/TTF/DejaVuSans.ttf', fontsize)

    img_width, img_height = img.size
    text_width, _ = font.getsize(text)
    text_height = fontsize

    draw_x = (img_width - text_width)//2 + x_offset
    draw_y = (img_height - text_height)//2 + y_offset

    draw.text((draw_x, draw_y), text, font=font,fill=(0,0,0) )

def writewrappedlines(img,text,fontsize,y_text=-300,height=110, width=27,fontstring="Forum-Regular"):
    lines = textwrap.wrap(text, width)
    for line in lines:
        width= 0
        _place_text(img, line,0, y_text, fontsize,fontstring)
        y_text += height
    return img

def clear_display(display):
    print('Clearing display...')
    display.clear()


def nth_repl(s, sub, repl, n):
    find = s.find(sub)
    # If find is not -1 we have found at least one match for the substring
    i = find != -1
    # loop util we find the nth or we find no match
    while find != -1 and i != n:
        # find + 1 means we start searching from after the last match
        find = s.find(sub, find + 1)
        i += 1
    # If i is equal to n we found nth match so replace
    if i == n:
        return s[:find] + repl + s[find+len(sub):]
    return s

def by_size(words, size):
    return [word for word in words if len(word) <= size]


def display_image_8bpp(display, img):

    dims = (display.width, display.height)
    img.thumbnail(dims)
    paste_coords = [dims[i] - img.size[i] for i in (0,1)]  # align image with bottom of display
    img=img.rotate(180, expand=True)
    display.frame_buf.paste(img, paste_coords)
    display.draw_full(constants.DisplayModes.GC16)


def parse_args():
    p = argparse.ArgumentParser(description='Test EPD functionality')
    p.add_argument('-v', '--virtual', action='store_true',
                   help='display using a Tkinter window instead of the '
                        'actual e-paper device (for testing without a '
                        'physical device)')
    p.add_argument('-r', '--rotate', default=None, choices=['CW', 'CCW', 'flip'],
                   help='run the tests with the display rotated by the specified value')
    return p.parse_args()

def main():

    def fullupdate():
        """  
        The steps required for a full update of the display
        Earlier versions of the code didn't grab new data for some operations
        but the e-Paper is too slow to bother the coingecko API 
        """
        try:
            pricestack=getData(config)
            # generate sparkline
            makeSpark(pricestack)
            # update display
            updateDisplay(config, pricestack)
            lastgrab=time.time()
            time.sleep(.2)
        except Exception as e:
            message="Data pull/print problem"
            beanaproblem(str(e))
            time.sleep(10)
            lastgrab=lastcoinfetch
        return lastgrab

    args = parse_args()

    if not args.virtual:
        from IT8951.display import AutoEPDDisplay

        print('Initializing EPD...')

        # here, spi_hz controls the rate of data transfer to the device, so a higher
        # value means faster display refreshes. the documentation for the IT8951 device
        # says the max is 24 MHz (24000000), but my device seems to still work as high as
        # 80 MHz (80000000)
        display = AutoEPDDisplay(vcom=-2.69, rotate=args.rotate, spi_hz=24000000)

        print('VCOM set to', display.epd.get_vcom())

    else:
        from IT8951.display import VirtualEPDDisplay
        display = VirtualEPDDisplay(dims=(800, 600), rotate=args.rotate)
    

#   Get the configuration from config.yaml
    with open(configfile) as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    datapulled=False
    lastcoinfetch = time.time()
    while True:
        if internet():
            if (time.time() - lastcoinfetch > float(config['ticker']['updatefrequency'])) or (datapulled==False):
                lastcoinfetch=fullupdate()
                datapulled = True
                # Moved due to suspicion that button pressing was corrupting config file
                configwrite()                  

if __name__ == '__main__':
    main()
