import sys

from pymavlink import mavutil, mavwp


def main():
    if len(sys.argv) < 2:
        sys.exit(1)
    filename = sys.argv[1]

    # Wait for heartbeat
    master = mavutil.mavlink_connection('udp:127.0.0.1:14550')
    master.wait_heartbeat()

    # Load waypoints
    wp = mavwp.MAVWPLoader()
    wp.load(filename)

    # Clear existing
    master.waypoint_clear_all_send()
    master.recv_match(type='MISSION_ACK', blocking=True, timeout=5)

    # Send count
    master.waypoint_count_send(wp.count())

    # Send items
    for _i in range(wp.count()):
        msg = master.recv_match(type='MISSION_REQUEST', blocking=True, timeout=5)
        if not msg:
            print("Timeout waiting for MISSION_REQUEST")
            sys.exit(1)

        p = wp.wp(msg.seq)
        master.mav.send(p)

    ack = master.recv_match(type='MISSION_ACK', blocking=True, timeout=5)
    print(f"Ack: {ack}")

if __name__ == "__main__":
    main()
