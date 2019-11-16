# google_assistant_relay
Home Assistant custom component that sends text input to Google Assistant.

## Usage
```
service: google_assistant_relay.assist
data:
  query: "Turn on the light of livingroom" // light of livingroom from Google Home
```

## Prequisite
- Need 'credentials.json' file. Follow the [link](https://developers.google.com/assistant/sdk/guides/library/python/embed/install-sample) to obtain credentials.json.

## Installation
1. Download
    ```
    /custom_components/google_assistant_relay/
    ```
    into
    ```
    <config directory>/custom_components/google_assistant_relay/
    ```
2. Place 'credentials.json' in `<config directory>` (eg. `<config directory>/credentials.json` )

## Configuration
#### Example configuration.yaml:
```yaml
google_assistant_relay:
  credentials: credentials.json
  language: ko-KR
```
#### Configuration variables:

| key | required | default | description
| --- | --- | --- | ---
| **credentials** | yes | 'credentials.json' | relative path of credentials.json file from `<config directory>`
| **language** | no | `en-US` | language of a query

## Services
### google_assistant_relay.assist
| service data attribute | required | description
| --- | --- | ---
| **query** | yes | text input to Google Assistant
| **response_event** | no | an event that contains response text from Google Assistant


## Credit
- https://github.com/googlesamples/assistant-sdk-python/tree/master/google-assistant-sdk/googlesamples/assistant/grpc