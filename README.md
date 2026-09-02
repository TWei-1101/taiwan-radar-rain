# Taiwan Radar Rain

使用中央氣象署 QPESUMS `O-A0059-001` 雷達整合回波格點，判斷指定位置目前是否下雨、附近最大 dBZ、雨區距離、移動方向，以及預估開始與停止降雨時間，並透過 MQTT Discovery 自動建立 Home Assistant 實體。

> 雷達回波不等於地面實際降雨。本工具適合做短時提醒，不應作為防災或人身安全的唯一資訊來源。

## 功能

- 直接解析 1.25 km dBZ 格點，不依賴圖片顏色
- 分別計算住家周圍 1、3、10 km 最大回波
- 單一程序可監測最多三組位置，共用同一次雷達資料下載
- 用連續雷達幀估算雨區平移方向、速度與未來 10–60 分鐘開始／停止降雨 ETA
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
- `sensor.radar_rain_stop_eta`
- 1 / 3 / 10 km 最大 dBZ、雨區距離、方向與速度等感測器

實體 ID 可能因 Home Assistant 既有命名而略有不同；unique ID 固定以 `taiwan_radar_rain_` 開頭。

## 多位置監測

Home Assistant App 支援三組位置。第一組沿用既有實體；第二、第三組可分別啟用、命名並填入經緯度。每個位置會建立獨立 MQTT 裝置與完整實體，三組分析共用同一批雷達資料。

## 判斷方式

- 預設 `18 dBZ` 以上視為具降雨意義，可由 `RAIN_THRESHOLD_DBZ` 調整。
- 1 km 內超過門檻：`raining=true`。
- 對最近兩幀在住家周圍做相位相關，估算雨區位移。
- 將目前雨區依位移外推；60 分鐘內碰到住家 1 km 範圍即為 `rain_incoming=true`。
- 若目前正在下雨，外推回波何時移出住家 1 km 範圍，產生預估停雨時間；追蹤不可靠或 60 分鐘內未移出時不提供 ETA。
- 地形雜波、雷達波束高度與降水蒸發都可能造成誤判，建議搭配地面雨量站或雨滴感測器交叉驗證。

## 資料來源與授權

雷達資料：中央氣象署氣象資料開放平臺，`O-A0059-001 雷達整合回波資料`，資料更新頻率約 10 分鐘，依政府資料開放授權條款第 1 版使用。

程式碼採 MIT License。

## Home Assistant App（Add-on）

本 repository 也可直接加入 Home Assistant App Store：

1. 開啟「設定 → 附加元件 → 附加元件商店」。
2. 右上角選單開啟「儲存庫」。
3. 加入 `https://github.com/TWei-1101/taiwan-radar-rain`。
4. 安裝 **Taiwan Radar Rain**。
5. 在設定頁填入監測位置的經緯度後啟動。

App 需要 Mosquitto Broker，會透過 Supervisor Services API 自動取得 MQTT 連線資訊，不必在設定頁輸入 MQTT 帳號或密碼。
