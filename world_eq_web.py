#!/usr/bin/env python3
import requests
from datetime import datetime, timedelta, timezone
import folium
import time
import webbrowser
import os
from branca.element import Template, MacroElement

# 日本標準時（JST）
JST = timezone(timedelta(hours=9))

# USGS API
API_URL = "https://earthquake.usgs.gov/fdsnws/event/1/query"
seen_ids = set()

# マグニチュードで色分け
def get_color_by_magnitude(mag):
    if mag >= 7.0:
        return 'darkred'
    elif mag >= 5.0:
        return 'orange'
    else:
        return 'blue'

# 地震データ取得
def get_earthquake_data():
    starttime = (datetime.utcnow() - timedelta(days=1)).isoformat()
    params = {
        'format': 'geojson',
        'starttime': starttime,
        'minmagnitude': 3.5,
        'orderby': 'time',
        'limit': 100
    }
    try:
        response = requests.get(API_URL, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"APIエラー: {response.status_code}")
            return None
    except Exception as e:
        print(f"接続エラー: {e}")
        return None

# 表示＋地図生成
def display_and_log_earthquake_data(data):
    global seen_ids
    if not data or 'features' not in data:
        print("地震データがありません。")
        return

    new_quakes = [eq for eq in data['features'] if eq['id'] not in seen_ids]
    if not new_quakes:
        print("新しい地震はありません。")
        return

    print(f"\n==== 新しい地震情報（{len(new_quakes)} 件） ====\n")
    quake_map = folium.Map(location=[0, 0], zoom_start=2)

    with open("earthquake_log.txt", "a", encoding="utf-8") as logfile:
        for eq in new_quakes:
            prop = eq['properties']
            geom = eq['geometry']
            coords = geom['coordinates']
            lat, lon, depth = coords[1], coords[0], coords[2]
            mag = prop['mag']
            quake_id = eq['id']
            seen_ids.add(quake_id)

            dt_jst = datetime.fromtimestamp(prop['time'] / 1000, JST)
            time_str = dt_jst.strftime('%Y-%m-%d %H:%M:%S JST')

            print(f"🕒 {time_str}")
            print(f"📍 場所: {prop['place']}")
            print(f"💥 マグニチュード: {mag}")
            print(f"🌐 緯度: {lat} / 経度: {lon}")
            print(f"📏 深さ: {depth} km")
            print("-" * 40)

            logfile.write(f"{time_str} | M{mag} | {prop['place']} | 緯度: {lat}, 経度: {lon}, 深さ: {depth}km\n")

            folium.CircleMarker(
                location=[lat, lon],
                radius=mag * 1.5,
                popup=f"{time_str}\n{prop['place']} (M{mag})",
                color=get_color_by_magnitude(mag),
                fill=True,
                fill_opacity=0.7
            ).add_to(quake_map)

    # ==== 凡例 ====
    legend_html = """
    <div style="
        position: fixed;
        bottom: 50px;
        left: 50px;
        width: 160px;
        height: 120px;
        background-color: white;
        border:2px solid grey;
        z-index:9999;
        font-size:14px;
        padding: 10px;
        box-shadow: 2px 2px 6px rgba(0,0,0,0.3);
    ">
        <b>凡例（M規模）</b><br>
        <i style="background:blue; width:10px; height:10px; float:left; margin-right:6px; display:inline-block;"></i> M3.5〜4.9<br>
        <i style="background:orange; width:10px; height:10px; float:left; margin-right:6px; display:inline-block;"></i> M5.0〜6.9<br>
        <i style="background:darkred; width:10px; height:10px; float:left; margin-right:6px; display:inline-block;"></i> M7.0以上<br>
    </div>
    """
    legend = MacroElement()
    legend._template = Template(f"""<html><body>{legend_html}</body></html>""")
    quake_map.get_root().add_child(legend)

    # 地図保存＆初回だけブラウザ起動
    map_filename = "earthquake_map.html"
    quake_map.save(map_filename)
    print(f"🗺️ 地図を {map_filename} に保存しました。")

    if not hasattr(display_and_log_earthquake_data, "map_opened"):
        webbrowser.open('file://' + os.path.realpath(map_filename))
        display_and_log_earthquake_data.map_opened = True

# メイン
def main():
    print("🌍 世界の地震をリアルタイム監視中（Ctrl+Cで停止）")
    try:
        while True:
            data = get_earthquake_data()
            if data:
                display_and_log_earthquake_data(data)
            else:
                print("データ取得に失敗しました。")
            time.sleep(30)
    except KeyboardInterrupt:
        print("\n🛑 終了しました。おつかれさま！")

if __name__ == "__main__":
    main()
