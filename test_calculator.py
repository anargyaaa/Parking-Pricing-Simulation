# Cek regresi cepat: python3 test_calculator.py
from calculator import ValidationError, calculate

FLAT = {
    "type": "FLAT", "count_type": "INCREMENT", "current_user": "casual",
    "time_in": "2026-07-20T08:00:00", "time_out": "2026-07-20T14:00:00",
    "grace_period": 5, "discount": 0,
    "price": 2000, "next_price": 0, "initial_time": 0, "stay_time": 0,
    "max_price": 0, "max_hour": 0, "overnight_price": 7000, "period_data": [],
    "overstay_parameter": "DURATION", "overstay_duration": 6,
    "overstay_affected_user": "ALL", "overstay_type": "",
}

CASES = [
    ("flat+inap-durasi", FLAT, {"parking_amount": 2000, "total_amount": 9000}),
    ("grace-4menit", dict(FLAT, time_out="2026-07-20T08:04:00"),
     {"is_grace_period": True, "total_amount": 0}),
    ("member-gratis-parkir", dict(FLAT, current_user="member"),
     {"parking_amount": 0, "total_amount": 7000}),
    ("range-TIME", dict(FLAT, overstay_parameter="TIME", overstay_start="00:00",
     overstay_end="06:00", time_in="2026-07-20T23:59:00",
     time_out="2026-07-21T01:00:00"), {"total_amount": 9000}),
    ("progressive-8j", dict(FLAT, type="PROGRESSIVE", next_price=1000,
     initial_time=1, stay_time=1, overnight_price=0, overstay_parameter="",
     time_out="2026-07-20T16:00:00"), {"parking_amount": 9000}),
    ("limited-cap", dict(FLAT, type="LIMITED_PROGRESSIVE", next_price=1000,
     initial_time=1, stay_time=1, max_price=4000, overnight_price=0,
     overstay_parameter=""), {"parking_amount": 4000}),
]

failures = 0
for name, payload, expect in CASES:
    res = calculate(payload)
    ok = all(res[k] == v for k, v in expect.items())
    failures += not ok
    print(f"{name}: {'PASS' if ok else f'FAIL -> {res}'}")

try:
    calculate(dict(FLAT, time_out="2026-07-20T07:00:00"))
    print("validasi-mundur: FAIL (tidak melempar error)")
    failures += 1
except ValidationError:
    print("validasi-mundur: PASS")

raise SystemExit(1 if failures else 0)
