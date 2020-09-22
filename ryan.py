from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import pandas as pd
import numpy as np
import time
from datetime import date
import yagmail

previous_df = pd.read_csv('dataframe.csv', sep=';')

driver = webdriver.Chrome('/Users/chromedriver')

driver.get('https://www.ryanair.com/pl/pl/tanie-loty/')

time.sleep(2)

xpaths = {'city_from': '/html/body/div[2]/main/div/div[1]/div/form/div[1]/div[2]/div[2]/div/div[1]/input',
          'budget': '/html/body/div[2]/main/div/div[1]/div/form/farefinder-budget-input/div[2]/div[2]/div/div[2]',
          'amount': '/html/body/div[2]/main/div/div[1]/div/form/farefinder-budget-input/div[3]/div/div/div[2]/popup-content/core-option-selector/ul/li[6]/label',
          'return_option': '/html/body/div[2]/main/div/div[1]/div/form/div[3]/div[2]/div[2]/div[2]/div/div[1]/input',
          'whenever': '/html/body/div[2]/main/div/div[1]/div/form/div[3]/div[2]/div[3]/div/div/div[2]/popup-content/div[1]/div/div[5]'}

xpaths_list = list(xpaths.values())

for i in range(len(xpaths_list)):
        actionChains = ActionChains(driver)
        element = driver.find_element_by_xpath(xpaths_list[i])

        if i == 0:
                actionChains.double_click(element).perform()
                element.send_keys(Keys.DELETE, 'Kraków', Keys.ENTER)
        else:
                actionChains.click(element).perform()

airports = []
countries = []
months = []
prices = []

elements = [airports, countries, months]
objects = ['airport', 'country', 'ff-text-month']

time.sleep(1)

driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

flag = True
while flag:
        for i in range(len(elements)):
                web_object = driver.find_elements_by_class_name(objects[i])

                for a in web_object:
                        if i == 2:
                                elements[i].append(a.text[2:])
                        else:
                                elements[i].append(a.text)

        price_units = driver.find_elements_by_class_name('price-units')
        price_decimals = driver.find_elements_by_class_name('price-decimals')
        for price_unit, price_decimals in zip(price_units, price_decimals):
                prices.append(float(price_unit.text+price_decimals.text[:-3].replace(',', '.')))

        actionChains = ActionChains(driver)
        next_button = driver.find_element_by_xpath('/html/body/div[2]/main/div/div[2]/farefinder-widget/div/div[2]/div[2]/div/div/core-pagination/div/div[2]/a/core-icon')
        condition = next_button.find_element_by_xpath('..').get_attribute("class")

        if condition == 'core-link':
                actionChains.click(next_button).perform()
                time.sleep(2)
        else:
                flag = False

zipped_list = list(zip(airports, countries, months, prices))
columns = ['airport', 'country', 'new_month', 'new_price']

today = date.today()

df = pd.DataFrame(zipped_list, columns=columns)
df['next_date'] = today

merged_df = previous_df.merge(df, how='outer', on=['airport', 'country'])
merged_df['price_change'] = merged_df['new_price'] - merged_df['price']
merged_df['price_change'] = (merged_df['price_change'].replace(0.0, np.nan)).round(2)
merged_df = merged_df.dropna()
merged_df['price_change_percent'] = (((merged_df['new_price'] - merged_df['price'])/merged_df['price'])*100).round(2)
merged_df.to_csv('merged.csv', sep=';', index=False)

print(merged_df)

df_new = df.copy()
df_new.columns = previous_df.columns
#df_new.to_csv('dataframe.csv', sep=';', index=False)

emojis = {'Armenia': '🇦🇲',
          'Austria': '🇦🇹',
          'Belgia': '🇧🇪',
          'Bośnia i Hercegowina': '🇧🇦',
          'Bułgaria': '🇧🇬',
          'Chorwacja': '🇭🇷',
          'Cypr': '🇨🇾',
          'Czarnogóra': '🇲🇪',
          'Czechy': '🇨🇿',
          'Dania': '🇩🇰',
          'Estonia': '🇪🇪',
          'Finlandia': '🇫🇮',
          'Francja': '🇫🇷',
          'Georgia': '🇬🇪',
          'Grecja': '🇬🇷',
          'Hiszpania': '🇪🇸',
          'Holandia': '🇳🇱',
          'Irlandia': '🇮🇪',
          'Izrael': '🇮🇱',
          'Jordania': '🇯🇴',
          'Litwa': '🇱🇹',
          'Łotwa': '🇱🇻',
          'Luksemburg': '🇱🇺',
          'Malta': '🇲🇹',
          'Maroko': '🇲🇦',
          'Niemcy': '🇩🇪',
          'Norwegia': '🇳🇴',
          'Polska': '🇵🇱',
          'Portugalia': '🇵🇹',
          'Rosja': '🇷🇺',
          'Rumunia': '🇷🇴',
          'Serbia': '🇷🇸',
          'Słowacja': '🇸🇰',
          'Szwajcaria': '🇨🇭',
          'Szwecja': '🇸🇪',
          'Tunezja': '🇹🇳',
          'Turcja': '🇹🇷',
          'Ukraina': '🇺🇦',
          'Węgry': '🇭🇺',
          'Wielka Brytania': '🇬🇧',
          'Włochy': '🇮🇹'
          }

yag = yagmail.SMTP('ryanair.prices')

file = merged_df[['airport', 'country', 'new_month', 'new_price', 'price_change', 'price_change_percent']].sort_values(by='price_change_percent')

to = ['sebastian.krawczyk1116@gmail.com']
subject = f'Trendy cenowe Ryanair | {today}'
body = []

values = file.values.tolist()

for airport, country, month, price, price_change, price_change_percent in values:
    if price_change > 0:
        body.append(f'<p>{airport} {emojis[country]} | {month}<br>{price} zł (➕{price_change} zł | 📈{price_change_percent}%)</p>')
    else:
        body.append(f'<p>{airport} {emojis[country]} | {month}<br>{price} zł (➖{str(price_change)[1:]} zł | 📉{str(price_change_percent)[1:]}%)</p>')

content = ''.join(body)

yag.send(to=to, subject=subject, contents=content)


#my_json = df.to_json(orient='index', indent=1)
#print(my_json)

time.sleep(10)
driver.quit()