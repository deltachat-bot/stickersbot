class TestPlugin:
    def test_filter(self, mocker) -> None:
        msg = mocker.get_one_reply(filename="image.png")
        assert msg.filename
        assert msg.is_sticker()

        msg = mocker.get_one_reply(
            "https://signal.art/addstickers/#pack_id=59d3387717104e38a67f838e7ad0208c&pack_key=56af35841874d6fe82fa2085e8e5ed74dba5d187af007d3b4d8a3711dd722ad7"
        )
        assert msg.filename.endswith("zip")

        msg = mocker.get_one_reply("cat")
        assert msg.has_html()

        assert mocker.get_replies("❌")  # random behavior
