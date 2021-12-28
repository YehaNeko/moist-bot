from pprint import pprint
from itertools import chain
import json
import time
start = time.monotonic()


def sheet_to_json(filepath="sheet.txt", print_data: bool = False, output_to_file: bool = True, index_offset: int = 2) -> json:
    """ Function for converting a google sheet into json """

    """ Opening and formatting """
    with open(filepath, "r", encoding="utf8") as f:
        raw_sheet = list(
            chain.from_iterable([i.split("\n") for i in f.read().split("\t")])
        )

    """ Sorting """
    base_item = int(raw_sheet[0])
    sorted_sheet = []
    temp_list = []

    for item in raw_sheet:
        try:
            item = int(item)
        except ValueError:
            pass

        if item == base_item + 1:
            sorted_sheet.append(temp_list)
            base_item = item
            temp_list = [base_item]
        else:
            temp_list.append(item) if item != "" else temp_list.append(None)

    sorted_sheet = [
        [lst.pop(index) if index == index_offset and item is None else item for index, item in enumerate(lst)][:-2]
        for lst in sorted_sheet
    ]

    """ Convert into json """
    keys = list(filter(None, sorted_sheet[0]))
    data = {}

    for lst in sorted_sheet[1:]:
        if lst.count(None) == 12:
            continue

        try:
            sub_key, *rest = lst[1].replace("-", "").replace(" ", "").upper().split("|")
            sub_dict = dict(zip(keys, lst))
            data.update({sub_key: sub_dict})
        except IndexError:
            pass

    data = {"data": data}

    """ Optionals """
    if output_to_file:
        with open("output2.json", "w") as f:
            json.dump(data, f, indent=2)

    if __name__ != '__main__':
        return json.dumps(data, indent=2)

    if print_data:
        pprint(data)
        print(f"Finished in {round((time.monotonic() - start) * 1000)}ms")


if __name__ == '__main__':
    sheet_to_json(print_data=False, output_to_file=True, index_offset=2)
