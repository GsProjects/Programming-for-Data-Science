import csv
from collections import Counter

food = list(csv.DictReader(open('Temporary.csv')))
column = input('Enter the column you want to process or enter nothing to escape: ')
if column != '':
    temporary_data = {row[column] for row in food}
    print(temporary_data)
    print(len(temporary_data))

def remove_duplicate_locations(data):
    print('In remove_duplicate_locations')
    result = ammend_DBA(data)
    temp_data = []
    location = set()
    #  If location col empty populate with longitude and latitude
    for x in result:
        if x['Location'] == '':
            print('Empty locations')
            location.add(x['Latitude'])
            location.add(x['Longitude'])
            x['Location'] = location
            temp_data.append(x)
    #  Remove longitude and latitude columns
    new_data = []
    for item in temp_data:
        del item['Latitude']
        del item['Longitude']
        new_data.append(item)
    return new_data


def ammend_DBA(data):
    result = clean_text_data(data)
    new_data = []
    for item in result:
        dba_name = item['DBA Name'].split()
        aka_name = set(item['AKA Name'].split())
        common = [x for x in dba_name if x in aka_name]  # this comprehension will maintain the order of the common elements
        new_name = ''
        if len(common) != 0:  # if there is common elements
            for items in common:
                new_name = new_name + ' ' + items
            item['DBA Name'] = new_name
            item['AKA Name'] = new_name
        new_data.append(item)
    return new_data


def clean_text_data(data):
    print('In clean_text_data')
    result = ammend_city(data)
    new_data = []
    text_based_columns = ['DBA Name', 'AKA Name', 'Inspection Type']
    for x in result:
        for value in x:
            x[value] = x[value].lower()
            for item in text_based_columns:
                x[item] = x[item].lower()
                x[item] = x[item].replace("'", "")
                x[item] = x[item].replace(".", "")
                x[item] = x[item].replace(",", "")
                x[item] = x[item].replace("-", " ")
                x[item] = x[item].replace("/", " ")
        if x['AKA Name'] == '':
            x['AKA Name'] = x['DBA Name']
        new_data.append(x)
    return new_data


def ammend_city(data):
    print('In ammend_city')
    result = remove_state(data)
    new_data = []
    city = 'chicago'
    for x in result:
        if city in x['City'].lower():
            new_data.append(x)
        else:
            result.remove(x) #if city is not chicago delete the row

    for item in new_data:
        del item['City']

    return new_data


def remove_state(data):
    print('In remove_state')
    new_data = []
    for x in data:
        del x['State']
        new_data.append(x)
    return new_data


def write_data(data):
    with open('TemporaryOutput.csv', "w") as fh:
        out_csv = csv.DictWriter(fh,list(data[0].keys()))
        out_csv.writeheader()
        out_csv.writerows(data)


result = ammend_DBA(food)
'''temporary = {row[column] for row in result}
print(temporary)
print(len(temporary))'''
write_data(result)
