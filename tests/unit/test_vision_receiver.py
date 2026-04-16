"""Unit tests for vision receivers and models."""

from __future__ import annotations

import json

import pytest

from striker.vision.models import GpsDropPoint, validate_gps


class TestGpsDropPoint:
    def test_valid_drop_point(self) -> None:
        t = GpsDropPoint(lat=30.0, lon=120.0, confidence=0.9, timestamp=0.0)
        assert t.lat == 30.0
        assert t.lon == 120.0
        assert t.confidence == 0.9

    def test_rejects_lat_out_of_range(self) -> None:
        with pytest.raises(ValueError, match="Latitude"):
            GpsDropPoint(lat=200.0, lon=0.0, confidence=0.5, timestamp=0.0)

    def test_rejects_lon_out_of_range(self) -> None:
        with pytest.raises(ValueError, match="Longitude"):
            GpsDropPoint(lat=0.0, lon=361.0, confidence=0.5, timestamp=0.0)

    def test_rejects_confidence_out_of_range(self) -> None:
        with pytest.raises(ValueError, match="Confidence"):
            GpsDropPoint(lat=30.0, lon=120.0, confidence=1.5, timestamp=0.0)

    def test_accepts_boundary_values(self) -> None:
        GpsDropPoint(lat=-90.0, lon=-180.0, confidence=0.0, timestamp=0.0)
        GpsDropPoint(lat=90.0, lon=180.0, confidence=1.0, timestamp=0.0)

    def test_from_dict(self) -> None:
        data = {"lat": 30.0, "lon": 120.0, "confidence": 0.8}
        t = GpsDropPoint.from_dict(data)
        assert t.lat == 30.0
        assert t.confidence == 0.8


class TestTcpReceiver:
    @pytest.mark.asyncio
    async def test_parses_valid_json(self) -> None:
        from striker.vision.tcp_receiver import TcpReceiver

        receiver = TcpReceiver(host="127.0.0.1", port=0)  # port 0 = OS picks
        await receiver.start()
        # Get the actual port
        port = receiver._server.sockets[0].getsockname()[1]

        # Send a message
        reader, writer = await __import__("asyncio").open_connection("127.0.0.1", port)
        msg = json.dumps({"lat": 30.0, "lon": 120.0, "confidence": 0.9}) + "\n"
        writer.write(msg.encode())
        await writer.drain()
        await __import__("asyncio").sleep(0.1)

        target = receiver.get_latest()
        assert target is not None
        assert target.lat == 30.0

        writer.close()
        await writer.wait_closed()
        await receiver.stop()

    @pytest.mark.asyncio
    async def test_rejects_malformed_json(self) -> None:
        from striker.vision.tcp_receiver import TcpReceiver

        receiver = TcpReceiver(host="127.0.0.1", port=0)
        await receiver.start()
        port = receiver._server.sockets[0].getsockname()[1]

        reader, writer = await __import__("asyncio").open_connection("127.0.0.1", port)
        writer.write(b"not json\n")
        await writer.drain()
        await __import__("asyncio").sleep(0.1)

        assert receiver.get_latest() is None

        writer.close()
        await writer.wait_closed()
        await receiver.stop()


class TestUdpReceiver:
    @pytest.mark.asyncio
    async def test_parses_valid_json(self) -> None:
        from striker.vision.udp_receiver import UdpReceiver

        receiver = UdpReceiver(host="127.0.0.1", port=0)
        await receiver.start()
        port = receiver._transport.get_extra_info("sockname")[1]

        loop = __import__("asyncio").get_event_loop()
        transport, _ = await loop.create_datagram_endpoint(
            lambda: __import__("asyncio").DatagramProtocol(),
            remote_addr=("127.0.0.1", port),
        )
        msg = json.dumps({"lat": 30.0, "lon": 120.0, "confidence": 0.9}).encode()
        transport.sendto(msg)
        await __import__("asyncio").sleep(0.1)

        target = receiver.get_latest()
        assert target is not None
        assert target.lat == 30.0

        transport.close()
        await receiver.stop()
