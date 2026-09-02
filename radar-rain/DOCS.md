# Taiwan Radar Rain

## 必要條件

- Home Assistant OS 或 Supervised
- 已安裝並啟動 Mosquitto Broker
- Home Assistant 已設定 MQTT integration

## 設定

安裝後，在「設定」頁填入要監測位置的經緯度。座標只儲存在 Home Assistant，不會送到 GitHub。

```yaml
latitude: 25.033
longitude: 121.5654
rain_threshold_dbz: 18
incoming_radius_km: 40
interval_seconds: 600
history_frames: 3
log_level: info
```

儲存設定後啟動 App。首次建置可能需要數分鐘。

## Home Assistant 實體

MQTT Discovery 會自動建立目前降雨、雨區接近、ETA、1/3/10 km 最大 dBZ、雨區距離、移動方向與速度等實體。

若沒有出現實體，請先確認 Mosquitto Broker 與 MQTT integration 正常，再查看 App 的「紀錄」頁。

## 判斷限制

雷達回波不等於地面實際降雨，地形雜波、雷達波束高度與降水蒸發都可能造成誤差。本工具不可作為防災或人身安全的唯一資訊來源。
