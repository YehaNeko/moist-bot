import json
import time
from uuid import uuid1
from bs4 import BeautifulSoup
# from pprint import pprint as pp

start = time.monotonic()
FILEPATH = r"C:\Users\Jovan\Downloads\PF Advanced Info - Google Drive.html"
URL = r"https://docs.google.com/spreadsheets/d/1nZZOpxAxpieMyC0e0VepfzpmIP89XHIDJPtsohw8U9g/htmlview"

MAX_PRINT_DEBUG = 20


def sheet_to_json(
    fp=FILEPATH,
    print_data: bool = False,
    output_to_file: bool = True,
) -> json:
    """Function for converting a Google sheet into json"""

    """ Opening and formatting """
    current_printed_times = 0

    # Main google sheet
    import requests
    f = requests.get(URL).text
    # with open(fp, "r", encoding="utf8") as f:
    #     f = f.read()

    soup = BeautifulSoup(f, "lxml")

    # We need to find dashed styles to determine
    # when an entry is no longer an attachment of the last known weapon
    styles_css = soup.find("style", type="text/css").text
    dashed_styles = {
            int(s_and_css[0].replace("s", ""))
            for style in styles_css.split("}.ritz .waffle .")
            if "DASHED" in (s_and_css := style.split("{"))[1]
        }

    sheets_viewport = soup.find("div", id="sheets-viewport")
    pages = sheets_viewport.find_all("tbody")[2:3]

    # Gets text contents and style class of each item of every page
    pages_contents = [
        [
            [column.text if column.text else "" for column in row.find_all("td")]
            for row in page.find_all("tr")
        ]
        for page in pages
    ]

    # Remove empty lists/rows
    pages_contents = list(
        map(lambda x: list(filter(lambda y: y if any(y) else None, x)), pages_contents)
    )

    # # Gets style class of each item in every page
    styles = [
        [
            {
                int(style_class) if (style_class := "".join(c for c in "".join(column["class"]) if c.isdigit())) else ""
                for column in row.find_all("td")
            }
            for row in page.find_all("tr")
        ]
        for page in pages
    ]

    """ 
    Sorting 
    """
    keys = [page[0] for page in pages_contents]

    data = {}
    for page_index, page in enumerate(pages_contents):
        sub_data = {}
        last_primary = "AK12"  # TODO: make not hardcoded...
        last_attachment = "No attachment"
        was_last_attachment = True

        for i, entry in enumerate(page):
            current_styles = styles[page_index][i]
            primary = entry[0]

            if i in [0, 1, 2, 3]:  # TODO: Temp?
                continue

            if primary:
                sub_dict = dict(zip(keys[page_index], entry))

                # Pop unnecessary entries
                sub_dict.pop(keys[page_index][0])
                sub_dict.pop(keys[page_index][1])  # TODO: is index 1 even correct?
            else:
                continue

            # sub_dict = {
            #     "ATTACHMENTS": [{
            #             last_attachment: {
            #                 "ATTACHMENTS": [
            #                     {primary: sub_dict}
            #                 ]
            #             }
            #     }]
            # }
            # sub_data.update({last_primary: sub_dict})

            # TODO: Somehow make this work
            if "-" not in primary and was_last_attachment:
                last_primary = primary
                was_last_attachment = False
                last_attachment = "No attachment"

                sub_dict.update({"ATTACHMENTS": {last_attachment: {"ATTACHMENTS": {}}}})
                sub_data.update({last_primary: sub_dict})
                continue

            # This indicates a subgroup of attachments
            elif ">" in primary:
                # sub_dict = {"ATTACHMENTS": [{last_attachment: sub_dict}]}
                # sub_data.update({last_primary: {"ATTACHMENTS": [{last_attachment: sub_dict}]}})
                last_attachment = primary
                sub_dict.update({"ATTACHMENTS": {}})
                sub_data[last_primary]["ATTACHMENTS"].update({last_attachment: sub_dict})

            # This indicates a normal attachment within a subgroup
            elif "-" in primary:
                sub_data[last_primary]["ATTACHMENTS"][last_attachment]["ATTACHMENTS"].update({primary: sub_dict})
                # try:
                #     for idx, elem in enumerate(sub_data[last_primary]["ATTACHMENTS"]):
                #         if elem.get(last_attachment, False):
                #             sub_data[last_primary]["ATTACHMENTS"][idx]["ATTACHMENTS"].append({primary: sub_dict})
                #             break
                # except KeyError:
                #     continue

            # This indicates the last attachment of the weapon
            if any(current_styles.intersection(dashed_styles)):
                was_last_attachment = True

                # Debug stuff
                if current_printed_times <= MAX_PRINT_DEBUG:
                    print(f"Last attachment found on: {primary}")
                    print(f"Last primary: {last_primary}")
                    print(f"Current index: {i}")
                    try:
                        print(f"Next attachment: {page[i+1][0]}")
                    except IndexError:
                        print(f"index error on {i+1}")

                    print("\n")
                    current_printed_times += 1

                # print(f"{current_styles.intersection(dashed_styles)}\n")
                # try:
                #     last_primary = pages_contents[page_index][i+1][0]
                #     print(pages_contents[page_index][i+1][0])
                # except IndexError:
                #     break

            # # if "primaries" is a weapon and not an attachment
            # if "-" not in primary and ">" not in primary and any(current_styles & dashed_styles):
            #     last_primary = primary
            #
            #     sub_dict.update({"ATTACHMENTS": []})
            #     sub_data.update({primary: sub_dict})
            #
            # # if "primaries" is an attachment
            # # we add it to the last known weapon
            # # ~~IMPORTANT~~ Add "> " attachment grouping
            # # Check sheet for no prefix attachments
            # else:
            #     attachment = {primary: sub_dict}
            #     sub_data[last_primary]["ATTACHMENTS"].append(attachment)

        data.update({page_index: sub_data})

    # print(json.dumps(data, indent=2))
    # quit()

    """ Optionals """
    if output_to_file:
        with open(f"output_advinfosheet{uuid1()}.json", "w") as f:
            json.dump(data, f, indent=2)

    # if __name__ != '__main__':
    #     return json.dumps(data, indent=2)
    #
    if print_data:
        print(json.dumps(data, indent=2))
        print(f"Finished in {round((time.monotonic() - start) * 1000)}ms")


if __name__ == "__main__":
    import os
    os.chdir(r"C:\Users\Jovan\Desktop")

    sheet_to_json(print_data=False, output_to_file=False)
