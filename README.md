# Tuya IR AC Remote

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=oktaydegerli&repository=tuya-ir-ac&category=integration)

## HACS Setup
- Add `https://github.com/oktaydegerli/tuya-ir-ac` as a Custom Repository
- Install `tuya-ir-ac` from the HACS Integrations tab
- Add to the `configuration.yaml` file the following configuration:
- Restart Home Assistant

```yaml
climate:
  - platform: tuya_ir_ac
    name: "<name of air conditioner>"
    tuya_ir_device_id: "<tuya ir device id>"
    tuya_device_local_key: "<tuya device local key>"
    tuya_device_ip: "<tuya device local ip address>"
    tuya_device_version: '3.3'
    tuya_device_model: 'MSZ-GE25VA' # MSZ-GE25VA or MSC-GE35VB
```
