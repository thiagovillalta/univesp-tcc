from django.test import SimpleTestCase

from univesp_tcc.settings import build_channel_layers


class ChannelLayerSettingsTests(SimpleTestCase):
    def test_build_channel_layers_uses_inmemory_without_redis_url(self):
        channel_layers = build_channel_layers(None)

        self.assertEqual(
            channel_layers["default"]["BACKEND"],
            "channels.layers.InMemoryChannelLayer",
        )

    def test_build_channel_layers_parses_rediss_url_without_ssl_kwarg(self):
        redis_url = (
            "rediss://default:dummy-password"
            "@redis-host.example.com:15464"
        )

        channel_layers = build_channel_layers(redis_url)
        host_config = channel_layers["default"]["CONFIG"]["hosts"][0]

        self.assertEqual(
            channel_layers["default"]["BACKEND"],
            "channels_redis.core.RedisChannelLayer",
        )
        self.assertEqual(
            host_config["address"],
            "rediss://redis-host.example.com:15464",
        )
        self.assertEqual(host_config["username"], "default")
        self.assertEqual(host_config["password"], "dummy-password")
        self.assertNotIn("ssl", host_config)

    def test_build_channel_layers_uses_default_port_when_missing(self):
        channel_layers = build_channel_layers("rediss://default:@redis-host.example.com")
        host_config = channel_layers["default"]["CONFIG"]["hosts"][0]

        self.assertEqual(host_config["address"], "rediss://redis-host.example.com:6380")
        self.assertEqual(host_config["username"], "default")
        self.assertEqual(host_config["password"], "")

    def test_build_channel_layers_handles_url_without_credentials(self):
        channel_layers = build_channel_layers("rediss://redis-host.example.com")
        host_config = channel_layers["default"]["CONFIG"]["hosts"][0]

        self.assertEqual(host_config["address"], "rediss://redis-host.example.com:6380")
        self.assertNotIn("username", host_config)
        self.assertNotIn("password", host_config)
