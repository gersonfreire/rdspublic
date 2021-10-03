import time
from webwhatsapi import WhatsAPIDriver
from webwhatsapi.objects.message import Message

driver = WhatsAPIDriver()
print("Waiting for QR")


driver.wait_for_login(timeout=300)

print("Bot started")

while True:
    time.sleep(3)
    print("Checking for more messages")
    for contact in driver.get_unread():
        for message in contact.messages:
            if isinstance(message, Message):  # Currently works for text messages only.
                contact.chat.send_message(message.content)

# https://github.com/mukulhase/WebWhatsapp-Wrapper/pull/797/commits/ada6982a3a20ba8eb6ef87b6324b2e5d8b5e3bb7
"""
'qrCode': "img[alt=\"Scan me!\"]",
'qrCode': "canvas[aria-label=\"Scan me!\"]",    
"""                