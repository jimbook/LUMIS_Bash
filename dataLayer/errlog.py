from datetime import datetime
def logMessage(info:str):
    with open("log.txt","a+") as file:
        file.write("{}{}{}\n".format("="*10,"{}".format(datetime.now()),"="*10))
        file.write("{}\n".format(info))
