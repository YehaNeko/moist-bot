from pprint import pprint
from itertools import chain
import json


with open("sheet.txt", "r", encoding="utf8") as f:
    raw_sheet = list(
        chain.from_iterable([i.split("\n") for i in f.read().split("\t")])
    )


base_item = int(raw_sheet[0])
flattened_sheet = []
temp_list = []

for item in raw_sheet:
    try:
        item = int(item)
    except ValueError:
        pass

    if item != base_item + 1:
        temp_list.append(item) if item != "" else temp_list.append(None)
    else:
        flattened_sheet.append(temp_list)
        base_item = item
        temp_list = [base_item]


# TODO: use normal for loop with a break instead
flattened_sheet = [
    [item if index != 1 else lst.pop(index) for index, item in enumerate(lst)][:-2]
    for lst in flattened_sheet
]


keys = ["ROW", "WEAPONS", "KILLS", "ROBLOX", "DISCORD", "DISCORD ID", "PLATFORM", "NATIONALITY", "NOTES", "IN DISCORD", "LAST UPDATED", "UPDATED BY", "PROOF", "FORMER RECORD HOLDERS"]
sub_list = []
sub_dict = {}
sub_key = flattened_sheet[0][1]

for lst in flattened_sheet[1:]:
    if lst.count(None) == 12:
        sub_dict[sub_key] = sub_list
        sub_list = []   # clear
        sub_key = lst[1]

    else:
        data = dict(zip(keys, lst))
        sub_list.append(data)


with open("output.json", "w") as f:
    data = {"data": [sub_dict]}
    json.dump(data, f, indent=2)

pprint(sub_dict)
