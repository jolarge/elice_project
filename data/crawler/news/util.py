import pymongo

def connectDB():
    while True:
        try:
            print(1)
            conn = pymongo.MongoClient('mongodb://localhost', 27017, username = 'master', password = "mWERIzcBlF")
            newsDB = conn['newsDB']
            # nomal = conn['nomal']

            return newsDB
        except:
            pass