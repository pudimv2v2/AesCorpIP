from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import json
import os
import requests
from datetime import datetime, timedelta
import socket
import platform

app = Flask(__name__)
CORS(app)  # Habilita CORS para todas as rotas

# Configuração do diretório de dados
DATA_DIR = 'data'
VISITORS_FILE = os.path.join(DATA_DIR, 'visitors.json')

# Criar diretório de dados se não existir
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

def get_device_info():
    try:
        user_agent = request.headers.get('User-Agent', '')
        if 'Windows' in user_agent:
            return 'Windows'
        elif 'Mac' in user_agent:
            return 'MacOS'
        elif 'Linux' in user_agent:
            return 'Linux'
        elif 'Android' in user_agent:
            return 'Android'
        elif 'iPhone' in user_agent or 'iPad' in user_agent:
            return 'iOS'
        else:
            return 'Desconhecido'
    except:
        return 'Desconhecido'

def get_location_data(ip):
    try:
        # Verifica se é um IP local
        if ip.startswith(('192.168.', '10.', '172.16.', '127.')):
            return {
                'ip': ip,
                'city': 'Rede Local',
                'region': 'Rede Local',
                'country': 'Brasil',
                'latitude': '0',
                'longitude': '0',
                'isp': 'Rede Local',
                'device': get_device_info()
            }

        # Tenta obter dados do IP
        response = requests.get(f'http://ip-api.com/json/{ip}', timeout=5)
        if response.status_code == 200:
            data = response.json()
            return {
                'ip': ip,
                'city': data.get('city', 'Desconhecido'),
                'region': data.get('regionName', 'Desconhecido'),
                'country': data.get('country', 'Desconhecido'),
                'latitude': data.get('lat', '0'),
                'longitude': data.get('lon', '0'),
                'isp': data.get('isp', 'Desconhecido'),
                'device': get_device_info()
            }
    except Exception as e:
        print(f"Erro ao obter localização: {str(e)}")
    
    return {
        'ip': ip,
        'city': 'Desconhecido',
        'region': 'Desconhecido',
        'country': 'Desconhecido',
        'latitude': '0',
        'longitude': '0',
        'isp': 'Desconhecido',
        'device': get_device_info()
    }

def save_visitor_data(name, ip):
    try:
        visitors = []
        if os.path.exists(VISITORS_FILE):
            try:
                with open(VISITORS_FILE, 'r', encoding='utf-8') as f:
                    visitors = json.load(f)
            except Exception as e:
                print(f"Erro ao ler arquivo de visitantes: {str(e)}")

        visitor = {
            'name': name,
            'ip': ip,
            'location': get_location_data(ip),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'is_online': True
        }
        
        visitors.append(visitor)
        
        with open(VISITORS_FILE, 'w', encoding='utf-8') as f:
            json.dump(visitors, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Erro ao salvar dados do visitante: {str(e)}")

def get_visitor_data():
    try:
        if os.path.exists(VISITORS_FILE):
            with open(VISITORS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"Erro ao obter dados dos visitantes: {str(e)}")
    return []

def clean_old_data():
    try:
        if os.path.exists(VISITORS_FILE):
            with open(VISITORS_FILE, 'r', encoding='utf-8') as f:
                visitors = json.load(f)
            
            current_time = datetime.now()
            visitors = [v for v in visitors if 
                       current_time - datetime.strptime(v['timestamp'], '%Y-%m-%d %H:%M:%S') <= timedelta(hours=24)]
            
            with open(VISITORS_FILE, 'w', encoding='utf-8') as f:
                json.dump(visitors, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Erro ao limpar dados antigos: {str(e)}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/track')
def track():
    name = request.args.get('n', 'Anônimo')
    ip = request.remote_addr
    save_visitor_data(name, ip)
    return render_template('track.html')

@app.route('/visitors')
def visitors():
    clean_old_data()
    visitors_data = get_visitor_data()
    return render_template('visitors.html', visitors=visitors_data)

@app.route('/api/visitors')
def api_visitors():
    return jsonify(get_visitor_data())

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 