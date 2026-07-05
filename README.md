# PulseLoop Sleep — Home Assistant integration

A HACS-installable integration that turns the sleep webhooks from the
[PulseLoop](https://github.com/linuxct/pulseloop-android) Android app into persistent Home Assistant
entities. PulseLoop detects — from smart‑ring data + phone signals — when you **fell asleep** (live,
heuristic) and when you **woke up** (when the night syncs from the ring), and POSTs a webhook here.

Once set up you get:

| Entity | What it is |
|--------|------------|
| `binary_sensor.user_asleep` | `on` = fell asleep, `off` = awake (device class *occupancy*). Attributes: `hr_bpm`, `resting_hr_bpm`, `reason`, `is_nap`, `detected_at`, `session_id`. |
| `sensor.sleep_status` | Text: **"The user fell asleep"** / **"The user woke up"**. |
| `sensor.sleep_changed` | Timestamp of the last transition. |

## Install (HACS)

1. HACS → ⋮ (top right) → **Custom repositories** → add `https://github.com/linuxct/pulseloop-ha`,
   category **Integration**.
2. Search **PulseLoop Sleep** in HACS → **Download**.
3. **Restart Home Assistant.**
4. **Settings → Devices & Services → Add Integration → PulseLoop Sleep.** The dialog shows a generated
   **webhook URL** — copy it.

### Manual install (without HACS)
Copy `custom_components/pulseloop/` into your HA `config/custom_components/` folder and restart, then
do step 4 above.

## Connect the app

In the PulseLoop app: **Settings → Data sharing → Home Assistant** → enable → paste the webhook URL →
**Test webhook**. That's it — the app then POSTs automatically on sleep onset and wake.

The webhook is **local-only** by default, so your phone must reach Home Assistant on your network
(use the LAN IP/hostname; cleartext `http://` is fine). If your phone leaves the LAN at night, expose
the webhook via Home Assistant Cloud (Nabu Casa) and use that URL instead.

## Example automation

Trigger off the entity (not the webhook — this integration already owns it):

```yaml
alias: PulseLoop sleep reactions
triggers:
  - trigger: state
    entity_id: binary_sensor.user_asleep
    to: "on"
    id: asleep
  - trigger: state
    entity_id: binary_sensor.user_asleep
    to: "off"
    id: awake
actions:
  - choose:
      - conditions: [{ condition: trigger, id: asleep }]
        sequence:
          - action: light.turn_off
            target: { entity_id: light.bedroom }
      - conditions: [{ condition: trigger, id: awake }]
        sequence:
          - action: light.turn_on
            target: { entity_id: light.bedroom }
```

## Test without the ring

POST a sample event to your webhook URL:

```bash
curl -X POST -H 'Content-Type: application/json' \
  -d '{"event":"asleep","detected_at_iso":"2026-07-05T23:14:00Z","hr_bpm":52,"resting_hr_bpm":58,"is_nap":false}' \
  "http://homeassistant.local:8123/api/webhook/<your-id>"
```

`binary_sensor.user_asleep` turns **on** and `sensor.sleep_status` reads **"The user fell asleep."**
(The app's own **Test webhook** button sends `event:"test"`, which intentionally leaves the state
unchanged — watch the binary sensor's *attributes* update to `event: test` to confirm receipt.)

## Notes

- **Wake timing:** the `awake` event fires when the ring's night **syncs**, so the sensor stays `on`
  from onset until that sync — not the instant you physically wake. To clear it sooner, OR‑in another
  signal (phone unlocked, bedroom motion) in your automation.
- **Payload fields:** `event` (`asleep`/`awake`/`test`), `detected_at_ms`, `detected_at_iso`, `is_nap`,
  `reason`, `hr_bpm`, `resting_hr_bpm`, `session_id`.

## License

MIT — see [LICENSE](LICENSE).
