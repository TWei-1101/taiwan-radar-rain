# Taiwan Radar Rain

使用中央氣象署 QPESUMS `O-A0059-001` 雷達整合回波格點，判斷指定位置目前是否下雨、附近最大 dBZ、雨區距離、移動方向及預估抵達時間，並透過 MQTT Discovery 自動建立 Home Assistant 實體。

> 雷達回波不等於地面實際降雨。本工具適合做短時提醒，不應作為防災或人身安全的唯一資訊來源。

## 功能

- 直接解析 1.25 km dBZ 格點，不依賴圖片顏色
- 分別計算住家周圍 1、3、10 km 最大回波
- 用連續雷達幀估算雨區平移方向、速度與 10–60 分鐘 ETA
- Home Assistant MQTT Discovery
- 無需 CWA API Key；讀取中央氣象署公開歷史資料端點
- Docker Compose、單次執行、daemon 與離線 demo 模式

## 快速開始

```bash
cp .env.example .env
# 編輯 .env：填入住家經緯度與 MQTT 設定
docker compose up -d --build
docker compose logs -f
```

不使用 MQTT 時，將 `.env` 裡的 `MQTT_HOST` 留空即可，只會把 JSON 結果輸出到 log。

本機模擬測試：

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
radar-rain --demo
pytest
```

抓取一次真實資料：

```bash
HOME_LATITUDE=25.033 HOME_LONGITUDE=121.5654 radar-rain --once
```

## Home Assistant 實體

啟動後會自動建立：

- `binary_sensor.radar_raining`
- `binary_sensor.radar_rain_incoming`
- `sensor.radar_rain_status`
- `sensor.radar_rain_intensity`
- `sensor.radar_rain_eta`
- 1 / 3 / 10 km 最大 dBZ、雨區距離、方向與速度等感測器

實體 ID 可能因 Home Assistant 既有命名而略有不同；unique ID 固定以 `taiwan_radar_rain_` 開頭。

## 判斷方式

- 預設 `18 dBZ` 以上視為具降雨意義，可由 `RAIN_THRESHOLD_DBZ` 調整。
- 1 km 內超過門檻：`raining=true`。
- 對最近兩幀在住家周圍做相位相關，估算雨區位移。
- 將目前雨區依位移外推；60 分鐘內碰到住家 1 km 範圍即為 `rain_incoming=true`。
- 地形雜波、雷達波束高度與降水蒸發都可能造成誤判，建議搭配地面雨量站或雨滴感測器交叉驗證。

## 資料來源與授權

雷達資料：中央氣象署氣象資料開放平臺，`O-A0059-001 雷達整合回波資料`，資料更新頻率約 10 分鐘，依政府資料開放授權條款第 1 版使用。

程式碼採 MIT License。
