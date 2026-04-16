#!/usr/bin/env python3
"""Mock vision client — connects to striker's TCP receiver and sends drop points.

Striker's TcpReceiver listens on port 9876 as a TCP server. This script acts
as a TCP client that connects to it and sends JSON drop point coordinates.

Usage:
    python mock_vision_server.py [--host 127.0.0.1] [--port 9876] [--interval 2.0]
        [--lat 30.265 --lon 120.095] [--random] [--no-drop-point]
"""
from __future__ import annotations

import argparse
import json
import random
import socket
import structlog
import sys
import time


def main() -> None:
    parser = argparse.ArgumentParser(description="Mock vision TCP client")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9876)
    parser.add_argument("--interval", type=float, default=2.0)
    parser.add_argument("--lat", type=float, default=None, help="Fixed drop point latitude")
    parser.add_argument("--lon", type=float, default=None, help="Fixed drop point longitude")
    parser.add_argument("--random", action="store_true", help="Random coordinates in field boundary")
    parser.add_argument("--no-drop-point", action="store_true", help="Never send data")
    args = parser.parse_args()

    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(20),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
    log = structlog.get_logger()

    while True:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect((args.host, args.port))
            log.info("Connected to striker vision receiver", host=args.host, port=args.port)

            while True:
                if args.no_drop_point:
                    time.sleep(args.interval)
                    continue

                if args.random:
                    lat = random.uniform(30.2610, 30.2690)
                    lon = random.uniform(120.0910, 120.0990)
                elif args.lat is not None and args.lon is not None:
                    lat, lon = args.lat, args.lon
                else:
                    # Default: center of SITL field
                    lat, lon = 30.265, 120.095

                msg = json.dumps({"lat": lat, "lon": lon}) + "\n"
                sock.sendall(msg.encode("utf-8"))
                log.info("Sent drop point", lat=lat, lon=lon)
                time.sleep(args.interval)
        except (ConnectionRefusedError, BrokenPipeError, ConnectionResetError, OSError) as e:
            log.warning("Connection lost, retrying in 3s", error=str(e))
            time.sleep(3.0)
        finally:
            sock.close()


if __name__ == "__main__":
    main()
