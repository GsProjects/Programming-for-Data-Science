from bs4 import BeautifulSoup
from urllib.request import urlopen


def get_html():
    url = 'https://en.wikipedia.org/wiki/List_of_Presidents_of_the_United_States'
    html_content = urlopen(url)
    content = BeautifulSoup(html_content, "lxml")
    html_content.close()
    return content


def parse_html(content):
    tables = content.find_all('table', {'class': 'wikitable'})  # look for all tables with class wikitable
    president_table = tables[0]
    table_rows = president_table.find_all('tr')
    start_rows = 2  # first two rows contain headers
    new_index = 2
    for index, rows in enumerate(table_rows[start_rows:],start=2): #  index starts at 2 to skip first two rows
        if new_index < len(table_rows):
            row = table_rows[new_index]
            if len(row.td.attrs) > 0: #  if the td tag has one or more attributes
                if 'rowspan' in row.td.attrs: # if theres a rowspan
                    attribute = row.td.attrs['rowspan']
                    num_merged = int(attribute) + 1
                    merged_rows = [items for items in table_rows[new_index: new_index + num_merged]]
                    parse_rows(merged_rows)
                    merged_rows = []
                    new_index = new_index + num_merged - 1
                    num_merged = 0

                # NEED ELSE TO DEAL WITH TD tags that have a style attribute
                else: #  if not a rowspan attribute
                    parse_rows(row)
                    new_index += 1

            else:
                new_index += 1
                parse_rows(row)


def remove_tags(data):
    unwanted_tags = ['sup','br']
    for element in data([item for item in unwanted_tags]):
        element.decompose()
    return data


def parse_rows(rows):
    president_data =[]
    parsed_row=[]
    for items in rows:
        if len(items) > 1:
            #check if the td tag has an embedded rowspan

            table_data = items.findAll('td')
            president_data = [item for item in table_data]
    with open('Row.txt', 'a') as file:
        for item in president_data[1:]:  # skip first element as it is just a column number
            text = item.get_text()
            text = text.replace('\n',' ')
            text = text.replace('\n–\n',' ')
            parsed_row.append(text)
        file.write(str(parsed_row))
        file.write('################################################### \n')
        file.close()

    return True


result = get_html()
data = remove_tags(result)
parse_html(data)

