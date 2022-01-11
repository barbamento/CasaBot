from time import time
from Barbagram.barbagram import button,telegram,keyboard,message
from numpy.lib.arraysetops import isin
import pandas as pd
import numpy as np
import os
import polling2
import datetime
import pytesseract
from PIL import Image
import requests
from io import BytesIO
import re

class casabot:
    def __init__(self):
        TOKEN=self.read_secrets()["TOKEN"]
        self.bot=telegram(TOKEN)
        self.path={"shopping_list":os.path.join(".","shopping_list"),
                "bills":os.path.join(".","bills")}
        self.start_bot()

    def read_secrets(self):
        """
        read all the tokens and apy key located in the secrets folder.
        Every api needs to be in a separate txt file and with some name rules:

        Mandatory:

            TOKEN       telegram token
            cmc_key     coinmarketcap key

        Optional:
            
            api_secret  secret api key from binance
            api_key     api key from binance

        Returns:
            Dict,
        contains all the secret key.
        """
        paths=[f for f in os.listdir("./secrets") if f[-4:]==".txt"]
        api=[]
        for f in paths:
            with open(os.path.join("./secrets/",f), "r") as text_file:
                api.append(text_file.read())
        return dict(zip([f[:-4] for f in paths],api))

    def start_bot(self):
        stored_messages=self.bot.getUpdates()
        if stored_messages["result"]==[]:
            offset=None
        else:
            offset=stored_messages["result"][-1]["update_id"]
        idling=True
        choices=["shopping list","reminders","bills"]
        while idling:
            incoming_message,time=polling2.poll(self.getUpdates_orTime,args=([offset]),step=1,timeout=0)
            if incoming_message["result"]!=[]:
                offset=message(incoming_message).update_id+1
                first_message=message(incoming_message)
                if first_message.type=="message" and first_message.text in choices:
                    idling=False
                else:
                    initial_kb=keyboard(choices).to_keyboard()
                    self.bot.sendMessage(chat_id=first_message.chat_id,text="What do you want to do?",reply_markup=initial_kb)
        if first_message.text=="shopping list":
            self.shopping_list(first_message)
        elif first_message.text=="reminders":
            self.reminders(first_message)
        elif first_message.text==choices[2]:
            self.bills(first_message)

    def getUpdates_orTime(self,offset=None):
        return self.bot.getUpdates(offset=offset),datetime.datetime


    def shopping_list(self,first_message):
        choices=["show shopping list","add element to shopping list","clear the shopping list","go back"]
        kb=keyboard(choices)
        self.bot.sendMessage(chat_id=first_message.chat_id,text="What do you want to do now?",reply_markup=kb.to_keyboard(orientation="vertical"))
        waiting_answer=True
        offset=first_message.update_id+1
        while waiting_answer:
            answer=polling2.poll(self.bot.getUpdates,args=([offset]),step=1,timeout=0)
            if answer["result"]!=[]:
                answer=message(answer)
                offset=answer.update_id+1
                if answer.text in ["add element to shopping list","clear the shopping list","go back"]:
                    waiting_answer=False
                elif answer.text=="show shopping list":
                    shopper=self.load(name="shopping_list").index.to_list()
                    shopper=str(shopper)[2:-2].replace("', '","\n")
                    self.bot.sendMessage(chat_id=answer.chat_id,text=shopper)
        if answer.text=="add element to shopping list":
            self.add_item(answer)
        elif answer.text=="clear the shopping list":
            self.bot.sendMessage(chat_id=answer.chat_id,text="From the following list choose which element you want to eliminate",reply_markup=keyboard(["exit"]).to_keyboard())
            self.remove_item(answer)
        elif answer.text=="go back":
            self.start_bot()

    def add_item(self,old_answer):
        receveing_input=True
        self.bot.sendMessage(chat_id=old_answer.chat_id,text="add item to the shopping list",reply_markup=keyboard(["exit"]).to_keyboard())
        offset=old_answer.update_id+1
        while receveing_input:
            answer=polling2.poll(self.bot.getUpdates,args=([offset]),step=1,timeout=0)
            if answer["result"]!=[]:
                shopper=self.load(name="shopping_list")
                answer=message(answer)
                offset=answer.update_id+1
                if answer.text=="exit":
                    receveing_input=False
                else:
                    for i in answer.text.split("\n"):
                        shopper.loc[i,:]=[answer.chat_id]
                    self.bot.sendMessage(chat_id=old_answer.chat_id,text="ok")
                    shopper.to_csv(os.path.join(self.path["shopping_list"],"shopping_list.csv"))
        self.shopping_list(answer)

    def remove_item(self,old_answer):
        receveing_input=True
        shopper=self.load(name="shopping_list")
        kb_shopper=keyboard(shopper.index.to_list()).to_inline(callback_data=shopper.index.to_list(),orientation="vertical")
        self.bot.sendMessage(chat_id=old_answer.chat_id,text="choose the item to remove",reply_markup=kb_shopper)
        offset=old_answer.update_id+1
        while receveing_input:
            answer=polling2.poll(self.bot.getUpdates,args=([offset]),step=1,timeout=0)
            if answer["result"]!=[]:
                answer=message(answer)
                offset=answer.update_id+1
                if answer.text=="exit" or answer.text in shopper.index.to_list():
                    receveing_input=False
        if answer.text=="exit":
            self.shopping_list(answer)
        elif answer.text in shopper.index.to_list():
            shopper=shopper.drop(answer.text)
            shopper.to_csv(os.path.join(self.path["shopping_list"],"shopping_list.csv"))
            self.remove_item(answer)

    def load(self,name):
        if not os.path.exists(self.path[name]):
            os.makedirs(self.path[name])
        try:
            shopper=pd.read_csv(os.path.join(self.path[name],str(name)+".csv"),index_col=0)
        except:
            if name=="shopping_list":
                columns=["added by"]
            if name=="bills":
                columns=["cathegory","price","date","added by"]
            shopper=pd.DataFrame(columns=columns)
            shopper.to_csv(os.path.join(self.path[name],str(name)+".csv"))
        return shopper



    def reminders(self,message):
        
        
        self.start_bot()


    def bills(self,first_message):
        choices=["add new bill","see current situation","fix the problems","go back"]
        kb=keyboard(choices)
        self.bot.sendMessage(chat_id=first_message.chat_id,text="What do you want to do now?",reply_markup=kb.to_keyboard(orientation="vertical"))
        waiting_answer=True
        offset=first_message.update_id+1
        while waiting_answer:
            answer=polling2.poll(self.bot.getUpdates,args=([offset]),step=1,timeout=0)
            if answer["result"]!=[]:
                answer=message(answer)
                offset=answer.update_id+1
                if answer.text=="see current situation":
                    shopper=self.load(name="bills")
                    text=[str(i)+" : "+str(shopper.loc[i,:]) for i in shopper.index]
                    self.bot.sendMessage(chat_id=answer.chat_id,text="\n".join(text))
                elif answer.text in choices:
                    waiting_answer=False
        if answer.text=="add new bill":
            self.analize_bill(answer)
        elif answer.text=="fix the problems":
            self.fix_bills(answer)
        elif answer.text=="go back":
            self.start_bot()
    
    def fix_bills(self,answer):
        self.start_bot()

    def read_image(self,message):
        photo=self.bot.getFile(message.file_id)
        photo_path=photo["result"]["file_path"]
        url=self.bot.open_photo(photo_path)
        response = requests.get(url)
        img = Image.open(BytesIO(response.content))
        thresh = 125
        fn = lambda x : 255 if x > thresh else 0
        r = img.convert('L').point(fn, mode='1')
        r.save("./prova.png")
        return pytesseract.image_to_string(r,lang="ita",config="digits")

    def analize_bill(self,old_message):
        receveing_input=True
        self.bot.sendMessage(chat_id=old_message.chat_id,text="add bill to analize",reply_markup=keyboard(["exit"]).to_keyboard())
        offset=old_message.update_id+1
        while receveing_input:
            answer=polling2.poll(self.bot.getUpdates,args=([offset]),step=1,timeout=0)
            if answer["result"]!=[]:
                answer=message(answer)
                if answer.type=="photo":
                    offset=answer.update_id+1
                    bill=self.read_image(answer)
                    bill_rows=bill.split("\n")
                    try:
                        begin=[bill_rows.index(i) for i in bill_rows if "PREZZO" in i][-1]
                        end=[bill_rows.index(i) for i in bill_rows if "SUBTOTAL" in i][0]
                        processed_bill=bill_rows[begin+1:end]
                        receveing_input=False
                        redo=False
                    except:
                        receveing_input=False
                        redo=True
                elif answer.text=="exit":
                    receveing_input=False
        if redo:
            self.analize_bill(answer)
        elif answer.type=="photo":
            self.save_bill(processed_bill,answer)
        elif answer.text=="exit":
            self.start_bot()
        
    def save_bill(self,today_bill,old_message):
        all_bills=self.load(name="bills")
        date=datetime.date.today()
        offset=old_message.update_id+1
        for row in today_bill:
            name=re.sub("[^a-zA-Z ]",""," ".join(row.split(" ")[:-2])).strip()
            print(name)
            if not name in all_bills.index:
                print("welo")
                possible_tags=["vegetables","meat","sweets","alcol","other food","breackfast","house","cats","bill and taxes","leisure","other","skip"]
                kb_shopper=keyboard(possible_tags).to_inline(callback_data=possible_tags,orientation="vertical")
                self.bot.sendMessage(chat_id=old_message.chat_id,text="choose the tag of {}".format(name),reply_markup=kb_shopper)
                waiting=True
                while waiting:
                    answer=polling2.poll(self.bot.getUpdates,args=([offset]),step=1,timeout=0)
                    if answer["result"]!=[]:
                        answer=message(answer)
                        offset=answer.update_id+1
                        if answer.text in possible_tags:
                            waiting=False
                            cat=answer.text
            else:
                print(name)
                if isinstance(all_bills.loc[name,:]["cathegory"],str):
                    cat=all_bills.loc[name,:]["cathegory"]
                else:
                    cat=all_bills.loc[name,:]["cathegory"].to_list()[-1]
            price=row.split(" ")[-1]
            if cat!="skip":
                all_bills.loc[name,:]=[cat,price,date,old_message.chat_id]
                self.bot.sendMessage(chat_id=old_message.chat_id,text="Item added")
        kb_yn=keyboard(["yes","no"]).to_inline(callback_data=["yes","no"])
        self.bot.sendMessage(chat_id=old_message.chat_id,text="Do you want to save this bill?",reply_markup=kb_yn)
        waiting=True
        while waiting:
            answer=polling2.poll(self.bot.getUpdates,args=([offset]),step=1,timeout=0)
            if answer["result"]!=[]:
                answer=message(answer)
                offset=answer.update_id+1
                if answer.text in ["yes","no"]:
                    waiting=False
        self.bot.sendMessage(chat_id=old_message.chat_id,text="Shop list added")
        all_bills.to_csv(os.path.join(self.path["bills"],str("bills")+".csv"))
        self.start_bot()


if __name__=="__main__":
    casa=casabot()