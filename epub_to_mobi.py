import os
import shutil
import base64
import mimetypes
import subprocess
from multiprocessing import Pool

from utils import connect_to_email

from googleapiclient.errors import HttpError

from email.message import EmailMessage

from constants import (CONVERT_COMMAND_LOCATION, EPUB_DIRECTORY, MOBI_DIRECTORY, TO_EMAIL, FROM_EMAIL)

def convert_epub_to_mobi():

    #Create the folder where converted books will go
    if not os.path.exists(MOBI_DIRECTORY):
        os.makedirs(MOBI_DIRECTORY)

    #Gather all files from directory that are .epub type 
    global epub_books 
    epub_books = [file for file in os.listdir(EPUB_DIRECTORY) if os.path.splitext(file)[1] =='.epub']

    #Generate pool so multiple conversions of epub to mobi can happen at one time
    pool = Pool(processes=10)
    pool.map(run_processes, epub_books)


          
def run_processes(book):
    #Runs the ebook-convert command from calibre to convert from epub to mobi
    book_name, type = os.path.splitext(book)
    subprocess.run([CONVERT_COMMAND_LOCATION, EPUB_DIRECTORY + book, MOBI_DIRECTORY + book_name + '.mobi'])


def send_email():
    #Connects to email service
    service = connect_to_email()
   
    try:

        #Creates email with all converted books as attachments
        email = EmailMessage()

        email['To'] = TO_EMAIL
        email['From'] = FROM_EMAIL
        email['Subject'] = 'Auto Send of Mobi to Kindle'

        email.set_content('Wow look at me go, programming to automate my life')

        books = [file for file in os.listdir(MOBI_DIRECTORY)]

        for book in books: 
            type_subtype, _ = mimetypes.guess_type(book)
            maintype, subtype = type_subtype.split('/')

            with open(MOBI_DIRECTORY + book, 'rb') as fp:
                book_data = fp.read()
            email.add_attachment(book_data, maintype, subtype, filename=book)


        encoded_message = base64.urlsafe_b64encode(email.as_bytes()).decode()

        message_body = {
            'raw': encoded_message
        }

        send_message = (service.users().messages().send
                        (userId="me", body=message_body).execute())
        print(F'Message Id: {send_message["id"]}')

        #If successfully sent, remove books
        if send_message["id"]:
            remove_old_books()

    except HttpError as error:
        print(f'An error occurred: {error}')


def remove_old_books():
    #Delete all converted books from the new directory we made
    if os.path.exists(MOBI_DIRECTORY):
       shutil.rmtree(MOBI_DIRECTORY)

    #In the original directory, delete all epub files 
    for book in epub_books:
        subprocess.run(['rm', EPUB_DIRECTORY + book])

if __name__ == '__main__':
    convert_epub_to_mobi()
    send_email()
