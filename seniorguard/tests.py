from django.test import SimpleTestCase

from django.conf import settings


class ChannelLayerSettingsTests(SimpleTestCase):
    def test_channel_layer_uses_inmemory_backend(self):
        self.assertEqual(
            settings.CHANNEL_LAYERS["default"]["BACKEND"],
            "channels.layers.InMemoryChannelLayer",
        )
