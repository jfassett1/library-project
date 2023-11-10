from collections import defaultdict
import pandas as pd
import random
import os
from faker import Faker

current_path = os.path.dirname(__file__)
# parent_folder = os.path.abspath(os.path.join(current_path, os.pardir))
data_folder = os.path.join(os.pardir, "../data/")
EMAIL_PROVIDERS = ["@gmail.com","@hotmail.com",
    "@gmail.com",
    "@yahoo.com",
    "@outlook.com",
    "@mail.com",
    "@icloud.com",
    "@aol.com",
    "@protonmail.com"]

surnames = pd.read_csv(f"{data_folder}engwales_surnames.csv",encoding='unicode_escape')["Name"]
surnames = surnames[surnames.str.isalpha()]

# first = pd.read_csv("data/male.txt")
firstnames = open(f"{data_folder}male.txt").read().split()
firstnames += open(f"{data_folder}female.txt").read().split()

def build_emails(names:list)->list[tuple[str, str]]:
    collision = defaultdict(lambda: defaultdict(int))
    emails = []
    # only increment based on email provider
    for name_id, provider in map(lambda x: (f"{x[0][0]}{x[1]}".lower().replace(" ",""), random.choice(EMAIL_PROVIDERS)), names):
        collision[provider][name_id] += 1
        emails.append((name_id+str(collision[provider][name_id]),provider))
    return emails

def mainbuild(n:int=0)->pd.DataFrame:
    namelist:list[tuple[str, str]] = [(random.choice(firstnames), random.choice(surnames)) for _ in range(n)]
    emails:list[tuple[str, str]] = build_emails(namelist)

    return pd.DataFrame({
                         "Names": [" ".join(name) for name in namelist],
                         "ID":[id_0 for id_0, _ in emails],
                         "Emails":["".join(email) for email in emails]})

# df = mainbuild(100)


# for i in df.itertuples():
#     print(tuple(i)[1:])
# print(tuple(map(lambda x: tuple(x)[1:], df.itertuples())))
