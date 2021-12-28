from pprint import pprint
from itertools import chain
import json

# raw_sheet = input("Input sheet:\n")
with open("sheet.txt", "r", encoding="utf8") as f:
    raw_sheet = list(
        filter(None, chain.from_iterable([i.split("\n") for i in f.read().split("\t")]))
    )

base_item = int(raw_sheet[0])
sorted_sheet = []
temp_list = []
for item in raw_sheet:
    try:
        item = int(item)
    except ValueError:
        pass

    if item != base_item + 1:
        temp_list.append(item)
    else:
        sorted_sheet.append(temp_list)
        base_item = item
        temp_list = [base_item]

keys = ["ROW", "WEAPONS", "KILLS", "ROBLOX", "DISCORD", "DISCORD ID", "PLATFORM", "NATIONALITY", "NOTES", "IN DISCORD", "LAST UPDATED", "UPDATED BY", "PROOF", "FORMER RECORD HOLDERS"]

list_of_dict = []
for lst in sorted_sheet:
    if len(lst) > 3:
        data = dict(zip(keys, lst))
        list_of_dict.append(data)
    else:
        continue

with open("output.json", "w") as f:
    data = {"data": list_of_dict}
    json.dump(data, f, indent=4)

pprint(list_of_dict)
