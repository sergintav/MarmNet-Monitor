"""
MarmNet Monitor
Yazan: Semih Ergintav
Sürüm: 1.0
"""

import json
import time
import threading
import subprocess
import concurrent.futures
from flask import Flask, render_template_string, jsonify
import argparse

app = Flask(__name__)

# ---------------- Komut satırından parametreler ----------------
parser = argparse.ArgumentParser(description="MarmNet Monitor")
parser.add_argument("--interval", type=int, default=30, help="Sayfa yenileme aralığı (saniye)")
parser.add_argument("--stations", type=str, default="stations.txt", help="İstasyon bilgilerini içeren text dosya")
parser.add_argument("--port", type=int, default=50001, help="Flask sunucu portu")
args = parser.parse_args()

REFRESH_INTERVAL = args.interval
STATIONS_FILE = args.stations
FLASK_PORT = args.port

# ---------------- Dosyadan istasyonları okuma ----------------
def load_stations(filename):
    stations = []
    try:
        with open(filename, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split()
                if len(parts) != 4:
                    continue
                name, ip, lat, lon = parts
                stations.append({
                    "name": name.strip(),
                    "ip": ip.strip(),
                    "lat": float(lat),
                    "lon": float(lon),
                    "ping_time": None,
                    "status_text": "Offline",
                    "time": "-",
                    "color": "#888888"  # Başlangıç rengi
                })
    except Exception as e:
        print(f"Dosya okunamadı: {e}")
    return stations

stations = load_stations(STATIONS_FILE)

# ---------------- Ping ve renk belirleme ----------------
def ping(ip):
    try:
        param = "-n" if subprocess.os.name == "nt" else "-c"
        result = subprocess.run(
            ["ping", param, "1", ip],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        if result.returncode == 0:
            for line in result.stdout.split("\n"):
                if "time=" in line.lower():
                    time_part = line.lower().split("time=")[1].split()[0]
                    try:
                        return float(time_part.replace("ms",""))
                    except:
                        return None
        return None
    except Exception:
        return None

def get_color_and_status(ping_time):
    if ping_time is None:
        return "#888888", "Offline"
    if ping_time <= 50:
        return "#22c55e", f"Mükemmel ({ping_time}ms)"
    elif ping_time <= 100:
        return "#eab308", f"İyi ({ping_time}ms)"
    elif ping_time <= 200:
        return "#f97316", f"Orta ({ping_time}ms)"
    else:
        return "#ef4444", f"Yavaş ({ping_time}ms)"

def update_stations():
    while True:
        # ThreadPoolExecutor ile paralel ping
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            # Tüm istasyonlar için ping işlemlerini başlat
            future_to_station = {executor.submit(ping, st["ip"]): st for st in stations}
            
            # Sonuçları topla
            for future in concurrent.futures.as_completed(future_to_station):
                st = future_to_station[future]
                try:
                    delay = future.result()
                    st["ping_time"] = delay
                    st["time"] = time.strftime("%Y-%m-%d %H:%M:%S")
                    st["color"], st["status_text"] = get_color_and_status(delay)
                except Exception:
                    # Hata durumunda offline yap
                    st["ping_time"] = None
                    st["time"] = time.strftime("%Y-%m-%d %H:%M:%S")
                    st["color"], st["status_text"] = get_color_and_status(None)
        
        time.sleep(REFRESH_INTERVAL)

threading.Thread(target=update_stations, daemon=True).start()

# ---------------- API endpoint zaten mevcut ----------------

# ---------------- HTML Template ----------------
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>MarmNet Monitor</title>
<style>
body { font-family: Arial, sans-serif; background: #f8f9fa; margin:0; padding:0;}
h1 { text-align:center; font-size:22px; margin:10px 0;}
.tables { display:flex; justify-content:center; gap:20px; margin:10px auto; width:95%; }
table { border-collapse: collapse; font-size:14px; background:white; box-shadow:0 2px 8px rgba(0,0,0,0.1); width:50%; }
th, td { border: 1px solid #ccc; padding:6px 8px; text-align:center; }
th { background:#34495e; color:white; }
.status-indicator { display:inline-block; width:12px; height:12px; border-radius:50%; margin-right:5px;}
#map { height:400px; margin:10px auto; width:95%; position:relative; }
.station-name { font-weight:bold; }
.leaflet-tooltip { font-size:8pt !important; font-weight:bold !important; white-space: nowrap; background:transparent !important; border:none !important; box-shadow:none !important; color: inherit !important;}
.leaflet-tooltip:before, .leaflet-tooltip:after { display:none !important; }
.coords { background: rgba(255,255,255,0.9); padding: 4px 8px; border-radius:4px; font-size:12px; border:1px solid #ccc; }
.developer-info {
    position: absolute;
    top: 5px;
    right: 20px;
    font-size: 0.8em;
    color: #555;
    z-index: 1000;
    background: rgba(255,255,255,0.7);
    padding: 2px 6px;
    border-radius: 4px;
}

/* Renk Lejandı Stilleri */
.legend {
    position: absolute;
    bottom: 10px;
    right: 20px;
    z-index: 1000;
    background: rgba(255,255,255,0.9);
    padding: 10px;
    border-radius: 6px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    font-size: 12px;
    border: 1px solid #ccc;
}

/* İstatistik Paneli Stilleri */
.stats-panel {
    position: absolute;
    top: 10px;
    right: 20px;
    z-index: 1000;
    background: rgba(255,255,255,0.9);
    padding: 8px 12px;
    border-radius: 6px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    font-size: 12px;
    border: 1px solid #ccc;
}
.stats-panel h4 {
    margin: 0 0 6px 0;
    font-size: 13px;
    color: #333;
}
.stat-item {
    margin-bottom: 3px;
    color: #555;
}
.legend h4 {
    margin: 0 0 8px 0;
    font-size: 13px;
    color: #333;
}
.legend-item {
    display: flex;
    align-items: center;
    margin-bottom: 4px;
}
.legend-color {
    width: 16px;
    height: 16px;
    border-radius: 50%;
    margin-right: 6px;
    border: 1px solid rgba(0,0,0,0.2);
}
.legend-text {
    font-size: 11px;
    color: #555;
}
</style>
<link rel="stylesheet" href="https://unpkg.com/leaflet/dist/leaflet.css"/>
</head>
<body>
<h1>MarmNet Monitor</h1>
<div class="developer-info">v1.0 - Semih Ergintav</div>

<div id="map">
    <!-- İstatistik Paneli -->
    <div class="stats-panel">
        <h4>İstasyon İstatistikleri</h4>
        <div class="stat-item">Toplam: <span id="total-count">0</span></div>
        <div class="stat-item">Aktif: <span id="active-count">0</span></div>
        <div class="stat-item">Pasif: <span id="offline-count">0</span></div>
    </div>
    
    <!-- Renk Lejandı -->
    <div class="legend">
        <h4>Ping Durumu</h4>
        <div class="legend-item">
            <div class="legend-color" style="background-color: #22c55e;"></div>
            <span class="legend-text">Mükemmel (0-50ms)</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background-color: #eab308;"></div>
            <span class="legend-text">İyi (50-100ms)</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background-color: #f97316;"></div>
            <span class="legend-text">Orta (100-200ms)</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background-color: #ef4444;"></div>
            <span class="legend-text">Yavaş (200ms+)</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background-color: #888888;"></div>
            <span class="legend-text">Offline</span>
        </div>
    </div>
</div>

<div class="tables">
    <table id="table1">
        <thead>
            <tr><th>İstasyon Adı</th><th>IP</th><th>Son Bağlantı</th><th>Son Durum</th></tr>
        </thead>
        <tbody></tbody>
    </table>

    <table id="table2">
        <thead>
            <tr><th>İstasyon Adı</th><th>IP</th><th>Son Bağlantı</th><th>Son Durum</th></tr>
        </thead>
        <tbody></tbody>
    </table>
</div>

<script src="https://unpkg.com/leaflet/dist/leaflet.js"></script>
<script>
let stations = {{ stations_json | safe }};
let markers = {};

// Harita
var map = L.map('map').setView([41.0, 29.0], 7);
L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/">OSM</a> &copy; <a href="https://carto.com/">CARTO</a>',
    subdomains: 'abcd',
    maxZoom: 19
}).addTo(map);

// Mouse koordinat gösterici
var coordDiv = L.control({position: 'bottomleft'});
coordDiv.onAdd = function (map) {
    this._div = L.DomUtil.create('div', 'coords');
    this.update();
    return this._div;
};
coordDiv.update = function (latlng) {
    this._div.innerHTML = latlng ? 
        "Lat: " + latlng.lat.toFixed(4) + " | Lon: " + latlng.lng.toFixed(4) :
        "Koordinat için mouse ile üzerine gelin";
};
coordDiv.addTo(map);
map.on('mousemove', function(e) { coordDiv.update(e.latlng); });

// İlk marker'ları oluştur
function createInitialMarkers() {
    stations.forEach((st, index) => {
        var circle = L.circleMarker([st.lat, st.lon], {
            radius:6,
            fillColor: st.color,
            color: st.color,
            weight:1,
            opacity:1,
            fillOpacity:1
        }).addTo(map);

        circle.bindTooltip(
            st.name,
            {
                permanent: true,
                direction: 'top',
                offset: [0, 0],
                className: 'custom-tooltip'
            }
        );
        const tooltipEl = circle.getTooltip().getElement();
        tooltipEl.style.color = st.color;
        tooltipEl.style.fontSize = '8pt';
        tooltipEl.style.whiteSpace = 'nowrap';
        
        // Marker'ı sakla
        markers[st.ip] = circle;
    });
}

// Marker'ları güncelle
function updateMarkers(newStations) {
    newStations.forEach(st => {
        const marker = markers[st.ip];
        if (marker) {
            // Rengi güncelle
            marker.setStyle({
                fillColor: st.color,
                color: st.color
            });
            
            // Tooltip rengini güncelle
            const tooltipEl = marker.getTooltip().getElement();
            if (tooltipEl) {
                tooltipEl.style.color = st.color;
            }
        }
    });
}

// Tabloyu doldur ve tıklayınca haritada odaklan
function fillTables(stationsData = stations){
    const mid = Math.ceil(stationsData.length/2);
    const tbl1 = document.querySelector("#table1 tbody");
    const tbl2 = document.querySelector("#table2 tbody");
    tbl1.innerHTML=""; tbl2.innerHTML="";
    
    // İstatistikleri hesapla
    const totalCount = stationsData.length;
    const activeCount = stationsData.filter(st => st.ping_time !== null).length;
    const offlineCount = totalCount - activeCount;
    
    // İstatistik panelini güncelle
    document.getElementById('total-count').textContent = totalCount;
    document.getElementById('active-count').textContent = activeCount;
    document.getElementById('offline-count').textContent = offlineCount;
    
    stationsData.forEach((st,i)=>{
        const row = document.createElement("tr");
        row.style.cursor = "pointer";
        row.innerHTML = `
            <td><span class="status-indicator" style="background-color:${st.color};"></span>${st.name}</td>
            <td>${st.ip}</td>
            <td>${st.time}</td>
            <td>${st.status_text}</td>
        `;
        row.onclick = function() { map.flyTo([st.lat, st.lon], 12); };
        if(i<mid){ tbl1.appendChild(row); } else { tbl2.appendChild(row); }
    });
}

// AJAX ile veri güncelleme
function updateData() {
    fetch('/api/stations')
        .then(response => response.json())
        .then(data => {
            stations = data;
            updateMarkers(data);
            fillTables(data);
        })
        .catch(error => {
            console.error('Veri güncelleme hatası:', error);
        });
}

// Sayfa yüklendiğinde
createInitialMarkers();
fillTables();

// Her X saniyede bir güncelle (sayfa yenileme olmadan)
setInterval(updateData, {{ refresh_interval * 1000 }});
</script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(
        HTML_TEMPLATE,
        stations_json=json.dumps(stations),
        refresh_interval=REFRESH_INTERVAL
    )

@app.route("/api/stations")
def api_stations():
    return jsonify(stations)

# ---------------- Flask başlat ----------------
if __name__ == "__main__":
    print(f"MarmNet Monitor başlatılıyor...")
    print(f"Port: {FLASK_PORT}")
    print(f"İstasyon dosyası: {STATIONS_FILE}")
    print(f"Yenileme süresi: {REFRESH_INTERVAL} saniye")
    print(f"Toplam {len(stations)} istasyon yüklendi")
    app.run(host="0.0.0.0", port=FLASK_PORT, debug=False)
    