import logging
import google.auth.transport.grpc
import google.auth.transport.requests
import google.oauth2.credentials
import json

from google.assistant.embedded.v1alpha2 import (
    embedded_assistant_pb2,
    embedded_assistant_pb2_grpc
)

try:
    from . import (
        assistant_helpers,
    )
except (SystemError, ImportError):
    import assistant_helpers

DOMAIN = 'google_assistant_relay'
_LOGGER = logging.getLogger(__name__)

ASSISTANT_API_ENDPOINT = 'embeddedassistant.googleapis.com'
DEFAULT_GRPC_DEADLINE = 10
PLAYING = embedded_assistant_pb2.ScreenOutConfig.PLAYING

CREDENTIALS = "credentials"
DEVIDE_MODEL_ID = "device_model_id"
DEVIDE_ID = "device_id"
LANGUAGE = "language"
GRPC_DEADLINE = "grpc_deadline"

def setup(hass, config):
    credentials = config[DOMAIN].get(CREDENTIALS, "credentials.json")
    device_model_id = config[DOMAIN].get(DEVIDE_MODEL_ID, "test_device_model_id")
    device_id = config[DOMAIN].get(DEVIDE_ID, "test_device_id")
    language = config[DOMAIN].get(LANGUAGE, "en-US")
    grpc_deadline = config[DOMAIN].get(GRPC_DEADLINE, DEFAULT_GRPC_DEADLINE)

    textAssistant = GoogleTextAssistant(language, device_model_id, device_id, False, credentials, grpc_deadline)

    def assist(call):
        query = call.data.get("query")
        response_text, response_html = textAssistant.assist(text_query=query)
        _LOGGER.info('<@assistant> %s' % response_text)
        response_event = call.data.get("response_event")
        if response_event:
            hass.bus.fire(response_event, {"query": query, "response": response_text})

    hass.services.register(DOMAIN, 'assist', assist)
    return True

class GoogleTextAssistant(object):
    """Sample Assistant that supports text based conversations.

    Args:
      language_code: language for the conversation.
      device_model_id: identifier of the device model.
      device_id: identifier of the registered device instance.
      display: enable visual display of assistant response.
      channel: authorized gRPC channel for connection to the
        Google Assistant API.
      deadline_sec: gRPC deadline in seconds for Google Assistant API call.
    """

    def __init__(self, language_code, device_model_id, device_id,
                 display, credentials, deadline_sec):
        self.language_code = language_code
        self.device_model_id = device_model_id
        self.device_id = device_id
        self.conversation_state = None
        # Force reset of first conversation.
        self.is_new_conversation = True
        self.display = display
        # Load OAuth 2.0 credentials.
        try:
            with open(credentials, 'r') as f:
                self.credentials = google.oauth2.credentials.Credentials(token=None,
                                                                    **json.load(f))
        except Exception as e:
            _LOGGER.error('Error loading credentials: %s', e)
            _LOGGER.error('Run google-oauthlib-tool to initialize '
                          'new OAuth 2.0 credentials.')
            raise e
        self.deadline = deadline_sec

    def __enter__(self):
        return self

    def __exit__(self, etype, e, traceback):
        if e:
            return False

    def assist(self, text_query):
        """Send a text request to the Assistant and playback the response.
        """
        def iter_assist_requests():
            config = embedded_assistant_pb2.AssistConfig(
                audio_out_config=embedded_assistant_pb2.AudioOutConfig(
                    encoding='LINEAR16',
                    sample_rate_hertz=16000,
                    volume_percentage=0,
                ),
                dialog_state_in=embedded_assistant_pb2.DialogStateIn(
                    language_code=self.language_code,
                    conversation_state=self.conversation_state,
                    is_new_conversation=self.is_new_conversation,
                ),
                device_config=embedded_assistant_pb2.DeviceConfig(
                    device_id=self.device_id,
                    device_model_id=self.device_model_id,
                ),
                text_query=text_query,
            )
            # Continue current conversation with later requests.
            self.is_new_conversation = False
            if self.display:
                config.screen_out_config.screen_mode = PLAYING
            req = embedded_assistant_pb2.AssistRequest(config=config)
            assistant_helpers.log_assist_request_without_audio(req)
            yield req

        def get_assistant():
            # Create an authorized gRPC channel.
            http_request = google.auth.transport.requests.Request()
            self.credentials.refresh(http_request)
            grpc_channel = google.auth.transport.grpc.secure_authorized_channel(
                self.credentials, http_request, ASSISTANT_API_ENDPOINT)

            _LOGGER.debug('Connecting to %s', ASSISTANT_API_ENDPOINT)
            return embedded_assistant_pb2_grpc.EmbeddedAssistantStub(
                grpc_channel
            )

        text_response = None
        html_response = None
        assistant = get_assistant()
        for resp in assistant.Assist(iter_assist_requests(),
                                          self.deadline):
            assistant_helpers.log_assist_response_without_audio(resp)
            if resp.screen_out.data:
                html_response = resp.screen_out.data
            if resp.dialog_state_out.conversation_state:
                conversation_state = resp.dialog_state_out.conversation_state
                self.conversation_state = conversation_state
            if resp.dialog_state_out.supplemental_display_text:
                text_response = resp.dialog_state_out.supplemental_display_text
        return text_response, html_response