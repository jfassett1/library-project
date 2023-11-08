import pandas as pd
import random as rand
surnames = pd.read_csv("data/engwales_surnames.csv",encoding='unicode_escape')["Name"]
# first = pd.read_csv("data/male.txt")
firstnames = open("data/male.txt").read().split()
firstnames += open("data/female.txt").read().split()
firstnames

def build_names(first:list,last:list,n):
    lst = []
    for _ in range(n):
        f_int = rand.randrange(len(first))
        l_int = rand.randrange(len(last))
        lst.append((first[f_int],last[l_int]))
    return lst

def build_ids(names):
    emails = []
    for i in range(len(names)):
        flag = 0
        first,last = names[i]
        iterator = 1
        while flag == 0:
            email = f"{first[0]}{last}{iterator}".lower().replace(" ","")
            if email in emails:
                iterator +=1
            else:
                emails.append(email)
                break
    return emails
emails = []

def mainbuild(n=0):
    namelist = build_names(firstnames,surnames,n)
    ids = build_ids(namelist)
    first = [name[0] for name in namelist]
    last = [name[1] for name in namelist]
    endings = ["@gmail.com","@hotmail.com",
    "@gmail.com",
    "@yahoo.com",
    "@outlook.com",
    "@mail.com",
    "@icloud.com",
    "@aol.com",
    "@protonmail.com"]

    emails = [id + endings[rand.randint(0,len(endings)-1)] for id in ids]
    return pd.DataFrame({"First":first,
                         "Last":last,
                         "ID":ids,
                         "Emails":emails})
    
df = mainbuild(100)


# for i in df.itertuples():
#     print(tuple(i)[1:])
print(tuple(map(lambda x: tuple(x)[1:], df.itertuples())))
