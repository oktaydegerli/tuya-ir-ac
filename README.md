# Tuya IR remote

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=oktaydegerli&repository=tuya-ir-ac&category=integration)

## HACS Setup
- Add `https://github.com/oktaydegerli/tuya-ir-ac` as a Custom Repository
- Install `tuya-ir-ac` from the HACS Integrations tab
- Restart Home Assistant
- add to the `configuration.yaml` file the following configuration:

```yaml
climate:
  - platform: tuya_ir_ac
    acs:
      - name: AC
        tuya_ir_device_id: "<your Tuya IR device ID>" # it is recommended to use secrets here
        tuya_device_local_key: "<your Tuya device local key>" # it is recommended to use secrets here
        tuya_device_ip: '192.168.1.2'
        tuya_device_version: '3.3'
        tuya_ac_type: 1
```
- Restart Home Assistant
- Done
