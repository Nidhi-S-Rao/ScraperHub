from flask import Flask, jsonify,render_template,request,redirect, url_for
from bs4 import BeautifulSoup
import requests
import csv
import json
from flask import Flask, send_file
import openpyxl
from io import BytesIO
import matplotlib.pyplot as plt
import io
import base64
import re


app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/render', methods=['POST'])
def render():
    url = request.form.get('url')
    print(url)
    return render_template('render.html', url=url)

def scrape_single_page(url, tag_classes):
    response = requests.get(url)
    response.raise_for_status()  
    soup = BeautifulSoup(response.text, 'html.parser')
    scrape_elements = {tag_class: soup.select(f'{tag_class}') for tag_class in tag_classes}
    num = min(len(elements) for elements in scrape_elements.values())
    scraped_content_list = []
    for i in range(num):
        data = {}
        for tag_class in tag_classes:
            element = scrape_elements[tag_class][i]
            data[tag_class] = element.get_text(strip=True)
        scraped_content_list.append(data)
    return scraped_content_list

@app.route('/scrape', methods=['POST'])
def scrape():
    user_input = request.form.get('user_input')
    url = request.form.get('url')
    
    tag_classes = user_input.split(',')
    
   
    scraped_data = scrape_single_page(url, tag_classes)
    number=request.form.get('page')
    print(number)
    if number is not '':
        page=int(number)
        for page_number in range(2, page+1):  
            print(page_number)
            next_page_url = f"{url}?page={page_number}"  
            scraped_data += scrape_single_page(next_page_url, tag_classes)
    
    return render_template('scrape.html', scraped_data=scraped_data, user_input=user_input)

def decode_unicode_values(data):
    if isinstance(data, dict):
        return {key: decode_unicode_values(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [decode_unicode_values(item) for item in data]
    elif isinstance(data, str):
        return data.encode('utf-8').decode('unicode_escape')
    else:
        return data
    

def decode_unicode_value(data):
    if isinstance(data, dict):
        return {key: decode_unicode_values(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [decode_unicode_values(item) for item in data]
    elif isinstance(data, str):
        return data.encode('latin1').decode('unicode_escape')
    else:
        return data


@app.route('/scrape_CSV', methods=['POST'])
def scrape_data_CSV():
    value = request.form.get('action')
    user_input = request.form.get('user_input')
    user_input_list = user_input.split(',')

   
    print("Action:", value)
    print("User Input:", user_input)
    scraped_content_list = request.form.get('scraped_content_list')
    print("Scraped Content List:", scraped_content_list)
    
    try:
        tags_list = json.loads(scraped_content_list)
    except json.JSONDecodeError as e:
        return f"JSON decoding error: {str(e)}", 400
    print(type(tags_list))
    # Decode Unicode values
    tags_list = decode_unicode_values(tags_list)

    if value == 'csv':
        filename = 'download.csv'
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=user_input_list)
            w.writeheader()
            for element in tags_list:
                w.writerow(element)
        return send_file(filename, as_attachment=True, download_name=filename, mimetype='text/csv')
    #change download_name to attachment_filename if any error 
    
    elif value == 'json':
        filename = 'download.json'
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(tags_list, f, indent=4, ensure_ascii=False)
        return send_file(filename, as_attachment=True, download_name=filename, mimetype='application/json')
    #change download_name to attachment_filename if any error 

    
    elif value == 'excel':
        filename = 'download.xlsx'
        workbook = openpyxl.Workbook()
        worksheet = workbook.active
        header = list(tags_list[0].keys())
        worksheet.append(header)
        for item in tags_list:
            row = [item[field] for field in header]
            worksheet.append(row)
        output = BytesIO()
        workbook.save(output)
        output.seek(0)
        return send_file(output, as_attachment=True, download_name=filename, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        #change download_name to attachment_filename if any error 

    elif (value=='visualization'):
           return render_template('visualization.html',scraped_data=tags_list,user_input=user_input,dropdown=user_input_list)


@app.route('/visualize', methods=['POST'])
def scrapeVisualize():
    user_input = request.form.get('user_input')
    print("User Input:", user_input)
    
    value = request.form.get('trigger')
    print("Chart Type:", value)
    
    scraped_content_list = request.form.get('scraped_data')
    print("Scraped Content List:", scraped_content_list)
    try:
        tags_list = json.loads(scraped_content_list)
    except json.JSONDecodeError as e:
        return f"JSON decoding error: {str(e)}", 400
    if not isinstance(tags_list, list):
        return "Error: Scraped content is not in the correct format", 400
    
    if value == 'pie':
        legend = request.form.get('legend')
        counts = {}
        for item in tags_list:
            name = item.get(legend)
            print("Name----------------------------------",name)
            if name in counts:
                counts[name] += 1
            else:
                counts[name] = 1
        
        plt.figure(figsize=(22,22))
        plt.pie(counts.values(), labels=counts.keys(), autopct='%1.1f%%', startangle=90, textprops={'fontsize': 14, 'fontweight': 'bold'})
        plt.title("Pie chart", fontsize=20, fontweight='bold')
        
        # Save plot to a BytesIO object
        img_io = io.BytesIO()
        plt.savefig(img_io, format='png')
        img_io.seek(0)
        img_data = base64.b64encode(img_io.getvalue()).decode('utf-8')
        plt.close() 
    elif value == 'donut':
        legend = request.form.get('legend')
        counts = {}
        for item in tags_list:
            name = item.get(legend)
            print("Name----------------------------------",name)
            if name in counts:
                counts[name] += 1
            else:
                counts[name] = 1
        
        plt.figure(figsize=(22,22))
        plt.pie(counts.values(), labels=counts.keys(), autopct='%1.1f%%', startangle=90, textprops={'fontsize': 14, 'fontweight': 'bold'}, wedgeprops={'width': 0.6})
        plt.title("Donut chart", fontsize=20, fontweight='bold')
        
        # Save plot to a BytesIO object
        img_io = io.BytesIO()
        plt.savefig(img_io, format='png')
        img_io.seek(0)
        img_data = base64.b64encode(img_io.getvalue()).decode('utf-8')
        plt.close() 
    elif value == 'column':
        print('------------------------------COLUMN')
        y_axis = request.form.get('y_axis')
        x_axis = request.form.get('x_axis')
        print('x_axis, y_axis--------------------------------------------', x_axis, y_axis)
        
        counts = {}
        for item in tags_list:
            x_value = item.get(x_axis)
            y_value = item.get(y_axis)
            if y_value is None:
            
                if x_value in counts:
                    counts[x_value] += 1
                else:
                    counts[x_value] = 1
            else:
                y_value = item.get(y_axis)
                if y_value is not None:
                    y_value = y_value.replace('\u20b9', '').replace(',', '')
                    y_value = re.sub(r'[^\d]', '', y_value)
                    if x_value in counts:
                        counts[x_value] += int(y_value)
                    else:
                        counts[x_value] = int(y_value)
        
        plt.figure(figsize=(30, 30))
        plt.bar(counts.keys(), counts.values(), color='brown')
        plt.xlabel(x_axis, fontsize=25, fontweight='bold')
        if y_axis is None:
            plt.ylabel("Count", fontsize=25, fontweight='bold')
        else:
            plt.ylabel(y_axis, fontsize=25, fontweight='bold')
        plt.title(f"Count by {x_axis}", fontsize=25, fontweight='bold')
        plt.xticks(rotation=45, ha='right') 
        
        # Save plot to a BytesIO object
        img_io = io.BytesIO()
        plt.savefig(img_io, format='png')
        img_io.seek(0)
        img_data = base64.b64encode(img_io.getvalue()).decode('utf-8')
        plt.close()


        
    
    return render_template('visualize.html', 
                           tags=user_input, 
                           scraped_data=tags_list, 
                           chart=value,
                           img_data=img_data)

if __name__ == '__main__':
    #app.run(debug=True)
    app.run(debug=True,host='0.0.0.0',port=5000)
