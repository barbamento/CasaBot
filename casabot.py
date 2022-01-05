from Barbagram.barbagram import button,telegram,keyboard,message
import pandas as pd
import numpy as np
import os
import polling2

class casabot:
    def __init__(self):
        TOKEN=self.read_secrets()["TOKEN"]
        self.bot=telegram(TOKEN)
        self.path={"shopping list":os.path.join(".","shopping_list")}
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
        while idling:
            incoming_message=polling2.poll(self.bot.getUpdates,args=([offset]),step=1,timeout=0)
            if incoming_message["result"]!=[]:
                offset=message(incoming_message).update_id+1
                first_message=message(incoming_message)
                if first_message.text=="shopping list":
                    idling=False
                else:
                    initial_kb=keyboard(["shopping list"]).to_keyboard()
                    self.bot.sendMessage(chat_id=first_message.chat_id,text="What do you want to do?",reply_markup=initial_kb)
        idling=True
        while idling:
            incoming_message=polling2.poll(self.bot.getUpdates,args=([offset]),step=1,timeout=0)
            if first_message.text=="shopping list":
                self.shopping_list(first_message)
                idling=False

    def shopping_list(self,first_message):
        choices=["add element to shopping list","clear the shopping list","go back"]
        kb=keyboard(choices)
        self.bot.sendMessage(chat_id=first_message.chat_id,text="What do you want to do now?",reply_markup=kb.to_keyboard(orientation="vertical"))
        waiting_answer=True
        offset=first_message.update_id+1
        while waiting_answer:
            answer=polling2.poll(self.bot.getUpdates,args=([offset]),step=1,timeout=0)
            if answer["result"]!=[]:
                answer=message(answer)
                offset=answer.update_id+1
                if answer.text in choices:
                    waiting_answer=False
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
                shopper=self.load_shopping_list()
                answer=message(answer)
                offset=answer.update_id+1
                if answer.text=="exit":
                    receveing_input=False
                else:
                    shopper.loc[answer.text,:]=[answer.chat_id]
                    shopper.to_csv(os.path.join(self.path["shopping list"],"shopping_list.csv"))
        self.shopping_list(answer)

    def remove_item(self,old_answer):
        receveing_input=True
        shopper=self.load_shopping_list()
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
            shopper.to_csv(os.path.join(self.path["shopping list"],"shopping_list.csv"))
            self.remove_item(answer)

    def load_shopping_list(self):
        if not os.path.exists(self.path["shopping list"]):
            os.makedirs(self.path["shopping list"])
        try:
            shopper=pd.read_csv(os.path.join(self.path["shopping list"],"shopping_list.csv"),index_col=0)
        except:
            shopper=pd.DataFrame(columns=["added by"])
            shopper.to_csv(os.path.join(self.path["shopping list"],"shopping_list.csv"))
        return shopper

if __name__=="__main__":
    casa=casabot()