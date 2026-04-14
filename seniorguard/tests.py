from django.test import SimpleTestCase

from univesp_tcc.settings import _build_channel_layers


class ChannelLayerSettingsTests(SimpleTestCase):
    def test_build_channel_layers_uses_inmemory_without_redis_url(self):
        channel_layers = _build_channel_layers(None)

        self.assertEqual(
            channel_layers["default"]["BACKEND"],
            "channels.layers.InMemoryChannelLayer",
        )

    def test_build_channel_layers_parses_rediss_url_without_ssl_kwarg(self):
        redis_url = (
            "rediss://default:fraLHevYbeYPb8aqrop8DZ0yQYT7c1fb"
            "@redis-15464.c322.us-east-1-2.ec2.cloud.redislabs.com:15464"
        )

        channel_layers = _build_channel_layers(redis_url)
        host_config = channel_layers["default"]["CONFIG"]["hosts"][0]

        self.assertEqual(
            channel_layers["default"]["BACKEND"],
            "channels_redis.core.RedisChannelLayer",
        )
        self.assertEqual(
            host_config["address"],
            "rediss://redis-15464.c322.us-east-1-2.ec2.cloud.redislabs.com:15464",
        )
        self.assertEqual(host_config["username"], "default")
        self.assertEqual(host_config["password"], "fraLHevYbeYPb8aqrop8DZ0yQYT7c1fb")
        self.assertNotIn("ssl", host_config)
