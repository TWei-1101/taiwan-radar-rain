# Taiwan Radar Rain

## 必要條件

- Home Assistant OS 或 Supervised
- 已安裝並啟動 Mosquitto Broker
- Home Assistant 已設定 MQTT integration

## 設定

安裝後，在「設定」頁填入要監測位置的經緯度。座標只儲存在 Home Assistant，不會送到 GitHub。

```yaml
location_name: Home
latitude: 25.033
longitude: 121.5654
location_2_enabled: false
location_2_name: Office
location_3_enabled: false
location_3_name: Parents
rain_threshold_dbz: 18
incoming_radius_km: 40
interval_seconds: 600
history_frames: 3
log_level: info
```

若要監測第二、第三個位置，請開啟對應選項並填入座標，例如：

```yaml
location_2_enabled: true
location_2_name: Office
latitude_2: 25.0478
longitude_2: 121.5319
location_3_enabled: true
location_3_name: Parents
latitude_3: 24.9937
longitude_3: 121.3010
```

每組位置會在 MQTT integration 下建立獨立的 **Taiwan Radar Rain - 位置名稱** 裝置。所有位置共用一次中央氣象署雷達下載，再分別計算結果。

儲存設定後啟動 App。首次建置可能需要數分鐘。

## Home Assistant 實體

每個啟用的位置都會透過 MQTT Discovery 建立目前降雨、雨區接近、開始／停止降雨 ETA、1/3/10 km 最大 dBZ、雨區距離、移動方向與速度等實體。

預估停雨時間是將最近兩張雷達圖的移動趨勢外推 10～60 分鐘。若雨區移動不明顯、追蹤可信度不足，或預計一小時後仍在下雨，該實體會顯示未知。

若沒有出現實體，請先確認 Mosquitto Broker 與 MQTT integration 正常，再查看 App 的「紀錄」頁。

## 判斷限制

雷達回波不等於地面實際降雨，地形雜波、雷達波束高度與降水蒸發都可能造成誤差。本工具不可作為防災或人身安全的唯一資訊來源。
