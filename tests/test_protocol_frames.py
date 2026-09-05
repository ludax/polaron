"""Byte-level tests for the Polaron/Graupner frame primitives in protocol.py.

Ground truth: Graupner_Charger_Link_1.1.apk, com/graupner/chargerm/model/Operator
(and GrChecksum). See references/protocol-details.md in the skill repo.

These tests pin the WIRE FORMAT — the thing that must survive any cross-OS
port — and therefore assert exact bytes, not just "doesn't crash".
"""
import protocol as P


# ---------------------------------------------------------------------------
# checksum
# ---------------------------------------------------------------------------
def test_checksum_is_byte_sum_mod_256():
    # Operator.MakeChecksum == sum(bytes) & 0xFF
    assert P.checksum(b'') == 0
    assert P.checksum(bytes([0x10, 0x20])) == 0x30
    assert P.checksum(bytes([0xFF, 0x01])) == 0x00          # 256 -> 0
    assert P.checksum(bytes([0x10, 0x20, 0x30])) == 0x60
    # large value: 0xFF * 256 sums to a multiple of 256
    assert P.checksum(bytes([0xFF] * 256)) == 0
    # never exceeds 0xFF, never negative
    for i in range(256):
        assert 0 <= P.checksum(bytes([0x80, i])) <= 0xFF


def test_crc16_is_ccitt_false_utility():
    # GrChecksum.CRC16 (CCITT-FALSE, poly 0x1021, init 0xFFFF) — the utility,
    # NOT the frame checksum. Known vectors:
    assert P.crc16_ccitt_false(b'') == 0xFFFF          # init
    assert P.crc16_ccitt_false(b'123456789') == 0x29B1  # standard CCITT-FALSE check value
    assert P.crc16_ccitt_false(b'12') == 0x3DBA          # verified against independent reference
    # frame checksum and CRC16 must differ (so they can't be silently swapped)
    assert P.crc16_ccitt_false(b'\x10\x20') != P.checksum(b'\x10\x20')


# ---------------------------------------------------------------------------
# constants (unsigned wire form)
# ---------------------------------------------------------------------------
def test_action_constants_wire_values():
    # signed dex -> unsigned wire byte (value & 0xFF)
    assert P.ACTION_READ == (-96) & 0xFF == 160
    assert P.ACTION_WRITE == (-95) & 0xFF == 161
    assert P.ACTION_START == (-94) & 0xFF == 162
    assert P.ACTION_STOP == (-93) & 0xFF == 163
    assert P.ACTION_BATTERY_STATUS == (-92) & 0xFF == 164
    assert P.ACTION_PRIVATE == (-89) & 0xFF == 167


def test_command_constants_wire_values():
    assert P.CMD_INFO == (-128) & 0xFF == 128
    assert P.CMD_CHARGE == 16
    assert P.CMD_DISCHARGE == 32
    assert P.CMD_CYCLE == 48
    assert P.CMD_SETTINGS == 112
    assert P.CMD_PROFILE == 1
    assert P.CMD_STOP == (-18) & 0xFF == 238
    assert P.CMD_PRIVATE_READ == (-46) & 0xFF == 210
    assert P.CMD_PRIVATE_WRITE == (-47) & 0xFF == 209
    assert P.CMD_PRIVATE_START == (-48) & 0xFF == 208


def test_common_and_result_constants():
    assert P.COMMON_START == 12
    assert P.COMMON_END == 13
    assert P.REQUEST_RETRY_COUNT == 5
    # two documented result families in the APK (see PLAN.md nuance note):
    # RESPONSE family (what protocol.py exposes as RSP_*):
    assert P.RSP_ACK == 6
    assert P.RSP_DENY == 238 == (-18) & 0xFF
    assert P.RSP_NACK == 21


# ---------------------------------------------------------------------------
# frame building
# ---------------------------------------------------------------------------
def test_build_info_request_exact_bytes():
    f = P.ChargerClient().build_info_request()
    # [START][ACTION_READ][CMD_INFO][checksum][END]
    assert f == bytes([P.COMMON_START, P.ACTION_READ, P.CMD_INFO,
                       0x20,                       # checksum(160,128) = 288 & 0xFF = 32
                       P.COMMON_END])
    assert f[0] == P.COMMON_START
    assert f[-1] == P.COMMON_END
    assert f[-2] == P.checksum(f[1:-2])            # checksum covers body only


def test_build_info_request_custom_action_command():
    c = P.ChargerClient()
    f = c.build_info_request(action=P.ACTION_START, command=P.CMD_CHARGE)
    body = bytes([P.ACTION_START, P.CMD_CHARGE])
    assert f == bytes([P.COMMON_START]) + body + bytes([P.checksum(body), P.COMMON_END])


def test_build_write_with_payload():
    c = P.ChargerClient()
    payload = bytes([0x01, 0x02, 0x03])
    f = c.build_write(P.ACTION_WRITE, P.CMD_CHARGE, payload)
    body = bytes([P.ACTION_WRITE, P.CMD_CHARGE]) + payload
    assert f == bytes([P.COMMON_START]) + body + bytes([P.checksum(body), P.COMMON_END])
    assert f[1] == P.ACTION_WRITE
    assert f[2] == P.CMD_CHARGE
    assert f[3:6] == payload
    assert f[-2] == P.checksum(body)


def test_build_write_empty_payload_matches_two_byte_body():
    c = P.ChargerClient()
    f = c.build_write(P.ACTION_WRITE, P.CMD_STOP, b'')
    body = bytes([P.ACTION_WRITE, P.CMD_STOP])
    assert f == bytes([P.COMMON_START]) + body + bytes([P.checksum(body), P.COMMON_END])


def test_frames_are_valid_bytes_and_length():
    c = P.ChargerClient()
    for (act, cmd) in [(P.ACTION_READ, P.CMD_INFO),
                       (P.ACTION_START, P.CMD_CHARGE),
                       (P.ACTION_STOP, P.CMD_STOP),
                       (P.ACTION_WRITE, P.CMD_SETTINGS)]:
        f = c.build_write(act, cmd)
        assert isinstance(f, bytes)
        assert len(f) == 5                          # start+act+cmd+cksum+end
        assert 0 <= f[-2] <= 0xFF


# ---------------------------------------------------------------------------
# default endpoints
# ---------------------------------------------------------------------------
def test_default_endpoints():
    assert P.DEFAULT_HOST == '192.168.4.1'
    assert P.DEFAULT_PORT == 80
    assert P.HTTP_STATUS == 'http://192.168.4.1/status'
    c = P.ChargerClient()
    assert c._status_url() == 'http://192.168.4.1/status'
    assert c._status_url(host='10.0.0.9') == 'http://10.0.0.9/status'
