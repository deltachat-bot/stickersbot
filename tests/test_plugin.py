from deltachat import const


class TestPlugin:
    def test_sticker_command(self, mocker) -> None:
        msg = mocker.get_one_reply("/sticker", filename="image.jpg")
        assert msg.filename
        assert msg._view_type == const.DC_MSG_STICKER

        quote = mocker.make_incoming_message(filename="image.png")
        msg = mocker.get_one_reply("/sticker", quote=quote)
        assert msg.filename
        assert msg._view_type == const.DC_MSG_STICKER

    def test_filter(self, mocker) -> None:
        msg = mocker.get_one_reply(filename="image.png")
        assert msg.filename
        assert msg._view_type == const.DC_MSG_STICKER

        msg = mocker.get_one_reply(
            "https://signal.art/addstickers/#pack_id=59d3387717104e38a67f838e7ad0208c&pack_key=56af35841874d6fe82fa2085e8e5ed74dba5d187af007d3b4d8a3711dd722ad7"
        )
        assert msg.filename.endswith("zip")
