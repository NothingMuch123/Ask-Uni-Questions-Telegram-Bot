from pymongo import MongoClient

class MongoDB:
    DB = None

    def Connect(connectionString):
        MongoDB.DB = MongoClient(connectionString)['Ask_Uni_Questions_Bot']

class PyMongoObject:
    def Load(self, dict):
        self.__dict__.update(self.RemoveID(dict))

    def ToDict(self, replaceID = True):
        return self.__dict__

    def FromDict(self, dict):
        self.Load(dict)
        return self

    def ReplaceID(self, dict, oldKey):
        self.AddID(dict, oldKey)
        return self.RemoveID(dict, oldKey)

    def AddID(self, dict, key):
        dict['_id'] = dict[key]
        return dict

    def RemoveID(self, dict):
        if '_id' in dict:
            del dict['_id']
        return dict


class Messages(PyMongoObject):
    Collection = None

    def __init__(self, id = None, username = None, question = None) -> None:
        self.id = id
        self.username = username
        self.questions = [question]
        self.answered = [""]
        self.banned = False

    def AddQuestion(self, question) -> None:
        self.questions.append(question)
        self.answered.append("")

    def Connect():
        Messages.Collection = MongoDB.DB["Messages"]


def Upsert(filter : dict, m : Messages):
    Messages.Collection.update_one(filter, {"$set":m.ToDict()}, upsert=True)


def WriteIntoDB(id, username, question : str) -> None:
    # Write into DB
    m = Messages.Collection.find_one({"id":id})
    mObj = None
    if m == None:
        mObj = Messages(id, username, question)
    elif not m["banned"]:
        mObj = Messages().FromDict(m)
        mObj.AddQuestion(question)
    else:
        return
    Upsert({"id":id}, mObj)