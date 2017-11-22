import bs4
from bs4 import BeautifulSoup
from urllib.request import urlopen
import calendar


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
                    num_merged = int(attribute)
                    merged_rows = [items for items in table_rows[new_index: new_index + num_merged]]
                    parse_rows(merged_rows)
                    merged_rows = []
                    new_index = new_index + num_merged
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
    president_rows = []
    president_data = []
    table_data = []
    for items in rows: #  for each td element in the list
        if len(items) >= 1:
            if type(items) is not bs4.element.NavigableString:
                if items.name =='td':
                    table_data.append(items) #  if the rowspan is one

                else:
                    #  if the president has multiple rows
                    table_data.extend(items.findAll('td')) #  get all the td elements in the row


    td_data = parse_td_data(table_data)
    separate_data(td_data)
    return True



def separate_data(president_rows):
    parsed_row =[]
    if len(president_rows) > 0:
        with open('Row.txt', 'a') as file:
            for item in president_rows:

                if type(item) is not bs4.element.NavigableString:
                    text = item.get_text()
                    text.strip('')
                    text = text.replace('\n',' ')
                    text = text.replace('\n–\n',' ')
                    text = text.replace("\xa0",'')
                    parsed_row.append(text)
            if len(parsed_row) > 0:
                if len(parsed_row) == 5:
                    file.write(str(parsed_row))
                    file.write('###################################################')
                    file.write(str(len(parsed_row)))
                    file.write('\n')
                    file.close()
                prep_data(parsed_row)
                '''file.write(str(parsed_row))
                file.write('###################################################')
                file.write(str(len(parsed_row)))
                file.write('\n')
                file.close()'''


def parse_td_data(data):
    print('')
    print('')
    print('')

    removal_values = [0,1,2,2]
    if len(data) > 8 :
        for items in removal_values:
            data.remove(data[items])

        for items in data:
            if len(items.get_text()) >= 15 and len(items.get_text()) <= 18: #  remove data from term column
                data.remove(items)

            if len(items.get_text()) >= 23 and len(items.get_text()) <= 24: #  special case for when the term data is longer than normal e.g Abraham Lincoln
                data.remove(items)

    elif len(data) <= 8:
        removal_values = [0, 1, 2]

        for items in removal_values:
            data.remove(data[items])

        for items in data:
            if len(items.get_text()) >= 15 and len(items.get_text()) <= 18:
                data.remove(items)

            if len(items.get_text()) >= 23 and len(items.get_text()) <= 24: #  special case for when the term data is longer than normal e.g Abraham Lincoln
                data.remove(items)

    return data


def prep_data(data):
    parties = ['Whig','Unaffiliated','Democratic','National Union','Democratic- Republican','Federalist', 'Republican']
    party = []
    information =[]
    president_name= ''
    president_age = ''
    presidential_status =''
    first_vp_data =''
    status = ['(Died', '(Resigned','(Succeeded']
    print('')
    print('')

    #  split the presidency dates
    presidency_dates = data[0].split('–') #  possible encoding error with the hyphen as the mac hyphen will not work in the split function

    #  split the president information
    president_info = parse_president_info(data)

    if len(data) >= 4:

        #  if they died in office
        presidency_info = presidency_information(presidency_dates)




        information.extend(presidency_info)
        information.extend(president_info) #  set to '' at top if nothing is found
        information.append(data[2]) #  appends the party name

        #information.append(president_name)
        #information.append(president_age)
        #information.append(data[2])
        #  if they succeeded to presidency
        first_vp_data = vp_info(data[3],presidency_info[0], presidency_info[1])
        information.extend(first_vp_data)
        #print(len(data))
        '''if len(data) > 4:
            vp_data = vp_info(data[4], presidency_info[0], presidency_info[1])
            information.extend(vp_data)
            print('DATA 4: ', data[4])'''

        if len(data) >= 5:
            vp_data = vp_info(data[4], presidency_info[0], presidency_info[1])
            information.extend(vp_data)
            print('vp_data: ', vp_data)
            print('DATA 5: ', data[4])

        if len(data) >= 6:
            vp_data = vp_info(data[5], presidency_info[0], presidency_info[1])
            information.extend(vp_data)
            print('vp_data: ', vp_data)
            print('DATA 6: ', data[5])

        if len(data) >= 7:
            vp_data = vp_info(data[6], presidency_info[0], presidency_info[1])
            information.extend(vp_data)
            print('vp_data: ', vp_data)
            print('DATA 7: ', data[6])



        #information.extend(first_vp_data)
        print(information)


    if len(data) > 4:
        if len( data[4]) == 16:
            data.remove(data[4]) #  exception case where the term date is not caught


        #print('DATA 4   :',data[4])
        if len(data) == 6: #  if they were associated with two parties use the last one
            party = [items for items in data[5].split() if items in parties]


def parse_president_info(data):
    president_info = []
    president_name = '' 
    new_data = []
    for index, items in enumerate(data[1].split()):
        if items == '(Lived:' or items == 'years)' or items == 'years' or items == 'old)' or items == 'Born':
            items = ''
        if len(items) > 1:  # remove the spaces left by the previous if statement
            if items[0] == '(':  # if the age is displayed as (93 only take everything after the (
                items = items[1:]
            president_info.append(items)

    president_info.remove(president_info[-2])  # remove the year the president was born and or died

    for items in president_info[:-1]:
        president_name += items + ' '

    president_age = president_info[-1]

    new_data.append(president_name)
    new_data.append(president_age)
    return new_data

def presidency_information(presidency_dates):

    new_data =[]
    status = ['(Died', '(Resigned', '(Succeeded']
    for items in status:
        for elements in presidency_dates[1].split():
            if items == elements:
                presidential_status = items[1:]  # remove the bracket

                presidency_dates[1] = presidency_dates[1][ :presidency_dates[1].index(items)]  # get the date up until the status

                new_data.append(presidency_dates[0])
                new_data.append(presidency_dates[1])
                new_data.append(presidential_status)
    if len(new_data) == 0:
        new_data = presidency_dates
        new_data.append('') # add an empty field to represent status...for easier insertion in db
    return new_data



def vp_info(data, start_vacancy, end_vacancy):

    status = ['(Died', '(Resigned', '(Succeeded']
    first_vp_data = ''
    new_data =[]

    first_vp_data = data
    if data == 'Office vacant': # if the vp is vacant for the entire presidency use presidency dates of vacancy dates
        new_data.append(data)
        new_data.append(start_vacancy)
        new_data.append(end_vacancy)
    elif len(data.split()) == 2: #  if theres only one vice president
        new_data.append(data)
    elif data[:13] == 'Office vacant': #  if its vacant for the balance of a term
        new_data.append(data[:13])
    else:
        for elements in first_vp_data.split():
               if elements == '–':
                   hyphen_index = first_vp_data.split().index(elements)
                   if first_vp_data.split()[ hyphen_index - 3] in calendar.month_name:
                       first_vp_name = first_vp_data.split()[ : hyphen_index - 3]
                       vp_name = ' '.join(first_vp_name)
                       if vp_name == 'Office vacant':
                           end_date = ' '.join(first_vp_data.split()[hyphen_index + 1: hyphen_index + 4])
                           start_date = first_vp_data.split()[hyphen_index - 3: hyphen_index]
                           start_date = ' '.join(start_date)

                           new_data.append(vp_name)
                           new_data.append(start_date)
                           new_data.append(end_date)
                       else:
                           new_data.append(vp_name)



                   elif first_vp_data.split()[ hyphen_index - 2] in calendar.month_name:
                       first_vp_name = first_vp_data.split()[: hyphen_index - 2]
                       vp_name = ' '.join(first_vp_name)
                       if vp_name == 'Office vacant':

                           end_date = ' '.join(first_vp_data.split()[hyphen_index + 1: hyphen_index + 4])
                           start_date = first_vp_data.split()[hyphen_index - 2: hyphen_index]
                           start_date.append(end_date.split()[2])
                           start_date = ' '.join(start_date)
                           #  if the year is missing because because they died or left in the same year then get the year from the end date

                           new_data.append(vp_name)
                           new_data.append(start_date)
                           new_data.append(end_date)
                       else:
                           new_data.append(vp_name)




    #print('NEW DATA:  ', new_data)
    return new_data


    # if its lenght is less than 20 return the vp name  DONE
    # if it contains office vacant and nothing else give return a list consistin of vacant and the presidency dates -> adjust function header
    # otherwise parse it and return the vp name







result = get_html()
data = remove_tags(result)
parse_html(data)


