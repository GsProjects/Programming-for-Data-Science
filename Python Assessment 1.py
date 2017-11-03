import csv

food = list(csv.DictReader(open('Food_Inspections.csv')))


def fill_cells(data):  # replace empty cells with null value
    result = amend_duplicate_license_number(data)
    for x in result:
        for value in x.keys():
            if x[value] == '':
                x[value] = 'null'
            if len(x['Location']) == 2:  # if location is ('','')
                x['Location'] = 'unknown'
    return result


def amend_duplicate_license_number(data):  # license # 0 is duplicated for numerous premises, so change value to unknown
    result = amend_inspections(data)
    for items in result:
        if items['License #'] == '0':
            items['License #'] = 'unknown'
    return result


def amend_inspections(data):  # clean inspection type data
    result = amend_duplicate_names(data)
    for items in result:
        items['Inspection Type'] = items['Inspection Type'].replace('canvas', 'canvass')
        items['Inspection Type'] = items['Inspection Type'].replace('canvasss', 'canvass')
        items['Inspection Type'] = items['Inspection Type'].replace('out ofbusiness', 'out of business')
        items['Inspection Type'] = items['Inspection Type'].replace('canvasss for rib fest', 'canvass for rib fest')
        items['Inspection Type'] = items['Inspection Type'].replace('canvasss special event', 'canvass special event')
        items['Inspection Type'] = items['Inspection Type'].replace('fire complain', 'fire complaint')
        items['Inspection Type'] = items['Inspection Type'].replace('two people ate and got sick',
                                                                    'suspected food poisoning')
        items['Inspection Type'] = items['Inspection Type'].replace('finish complaint inspection from 5 18 10',
                                                                    'complaint')
    return result


def amend_duplicate_names(data):
    result = remove_duplicate_locations(data)
    for items in result:
        items['DBA Name'] = items['DBA Name'].replace('mc donalds', 'mcdonalds')
        items['DBA Name'] = items['DBA Name'].replace('mcdonalds restaurant', 'mcdonalds')
        items['DBA Name'] = items['DBA Name'].replace('subway sandwiches', 'subway')
        items['DBA Name'] = items['DBA Name'].replace('subway sandwich', 'subway')
        items['DBA Name'] = items['DBA Name'].replace('subway restaurant', 'subway')
        items['DBA Name'] = items['DBA Name'].replace('dunkin donuts   baskin robbins', 'dunkin donuts')
        items['DBA Name'] = items['DBA Name'].replace('dunkin donuts baskin robbins', 'dunkin donuts')
        items['DBA Name'] = items['DBA Name'].replace('kentucky fried chicken', 'kfc')
        items['DBA Name'] = items['DBA Name'].replace('7   eleven', '7 eleven')

    return result


def remove_duplicate_locations(data):  # populate empty locations, then remove longitude and latitude columns
    result = clean_text_data(data)
    temp_data = []
    #  If location col empty populate with longitude and latitude
    for x in result:
        if x['Location'] == '':
            location = (x['Latitude'], x['Longitude'])
            x['Location'] = location
            temp_data.append(x)
        else:
            temp_data.append(x)

    # Remove longitude and latitude columns
    new_data = []
    for item in temp_data:
        item.pop('Latitude')
        item.pop('Longitude')
        new_data.append(item)
    return new_data


def clean_text_data(data):  # remove punctuation and whitespace to remove some duplicates
    result = amend_city(data)
    text_based_columns = ['DBA Name', 'AKA Name', 'Inspection Type']
    for x in result:
        for item in text_based_columns:
            x[item] = x[item].replace("'", "")
            x[item] = x[item].replace(".", "")
            x[item] = x[item].replace(",", "")
            x[item] = x[item].replace("-", " ")
            x[item] = x[item].replace("/", " ")
            x[item] = x[item].lstrip(" ")
            x[item] = x[item].rstrip(" ")
    return result


def amend_city(data):  # if city value does not contain chicago substring remove the row, then remove the column
    result = remove_state(data)
    new_data = []
    city = 'chicago'
    for x in result:
        if city in x['City'].lower() or x['City'].lower() == '':
            new_data.append(x)
        elif x['City'].lower() == 'chcicago':
            x['City'] = city
        else:
            x['City'] = 'non-chicago address, attention required'
    return new_data


def remove_state(data):
    result = change_date_format(data)
    for x in result:
        x.pop('State')
    return result


def change_date_format(data):  # changes date from mm/dd/yy to dd/mm/yy
    result = fill_names(data)
    for x in result:
        if x['Inspection Date'] != '':
            x['Inspection Date'] = x['Inspection Date'].replace('-', '/')
            temporary_date = x['Inspection Date'].split('/')
            new_date = temporary_date[1] + '/' + temporary_date[0] + '/' + temporary_date[2]
            x['Inspection Date'] = new_date
        if '-' in x['Inspection Date']:  # if the dates are separated by a hyphen change to forward slash
            x['Inspection Date'] = x['Inspection Date'].replace('-', '/')
    return result


def fill_names(data):  # populate empty name cells if possible
    result = change_case(data)
    for x in result:
        if x['DBA Name'] == '':
            x['DBA Name'] = x['AKA Name']
        elif x['AKA Name'] == '':
            x['AKA Name'] = x['DBA Name']
    return data


def change_case(data):
    for item in data:
        for value in item:
            item[value] = item[value].lower()
    return data


def write_data(data):
    with open('Output.csv', "w") as fh:
        out_csv = csv.DictWriter(fh, list(data[0].keys()))
        out_csv.writeheader()
        out_csv.writerows(data)


result = fill_cells(food)
write_data(result)
print('Processing finished')
