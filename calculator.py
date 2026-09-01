from datetime import datetime

from spnapiutilities.builders.parking_amount_builder import ParkingAmountBuilder
from spnapiutilities.core.price.price_model import PriceModel

VALID_TYPES = {"FLAT", "PROGRESSIVE", "LIMITED_PROGRESSIVE", "PERIOD"}
VALID_OVERSTAY_PARAMS = {"", "DURATION", "TIME"}
VALID_OVERSTAY_TYPES = {"", "PROGRESSIVE", "LIMITED_PROGRESSIVE"}
VALID_AFFECTED_USERS = {"ALL", "MEMBER", "NON_MEMBER"}


class ValidationError(ValueError):
    pass


def _num(value) -> int:
    return int(value) if value not in (None, "") else 0


def _to_ms(value, label: str) -> int:
    if not value:
        raise ValidationError(f"{label} wajib diisi")
    try:
        return int(datetime.fromisoformat(value).timestamp() * 1000)
    except ValueError:
        raise ValidationError(f"Format {label} tidak valid")


def validate(data: dict):
    time_in = _to_ms(data.get("time_in"), "Jam Masuk")
    time_out = _to_ms(data.get("time_out"), "Jam Keluar")
    if time_in > time_out:
        raise ValidationError("Jam Keluar tidak boleh sebelum Jam Masuk")

    price_type = data.get("type") or ""
    if price_type not in VALID_TYPES:
        raise ValidationError("Tipe tarif wajib dipilih (FLAT/PROGRESSIVE/LIMITED_PROGRESSIVE/PERIOD)")

    if price_type != "PERIOD" and _num(data.get("price")) <= 0:
        raise ValidationError("Harga tarif parkir wajib diisi")
    if price_type == "PERIOD" and not data.get("period_data"):
        raise ValidationError("Data periode (rentang harga) wajib diisi untuk tipe PERIOD")

    param = data.get("overstay_parameter") or ""
    if param not in VALID_OVERSTAY_PARAMS:
        raise ValidationError("Parameter overstay harus DURATION atau TIME")

    overstay_type = data.get("overstay_type") or ""
    if overstay_type not in VALID_OVERSTAY_TYPES:
        raise ValidationError("Tipe overstay harus PROGRESSIVE atau LIMITED_PROGRESSIVE")

    affected = data.get("overstay_affected_user") or "ALL"
    if affected not in VALID_AFFECTED_USERS:
        raise ValidationError("Affected user harus ALL/MEMBER/NON_MEMBER")

    # Overstay hanya dihitung jika ada tarif inap dan parameter dipilih
    has_overstay_price = _num(data.get("overnight_price")) > 0 or overstay_type != ""
    if param and has_overstay_price:
        if param == "DURATION" and _num(data.get("overstay_duration")) <= 0:
            raise ValidationError("Durasi overstay (jam) wajib diisi untuk parameter Duration")
        if param == "TIME" and (not data.get("overstay_start") or not data.get("overstay_end")):
            raise ValidationError("Jam mulai dan jam selesai overstay wajib diisi untuk parameter Range")

    return time_in, time_out


def calculate(data: dict) -> dict:
    time_in, time_out = validate(data)

    price_type = data["type"]
    membership_product = "MBR-001" if data.get("current_user") == "member" else ""

    price_model = PriceModel()
    price_model.set_id(None)
    price_model.set_is_membership(membership_product)
    price_model.set_time_in(time_in)
    price_model.set_time_out(time_out)
    price_model.set_total_hours()
    price_model.set_price(_num(data.get("price")))
    price_model.set_price_type(price_type)
    price_model.set_count_type(data.get("count_type") or "INCREMENT")
    price_model.set_grace_period(_num(data.get("grace_period")))
    price_model.set_start_price(_num(data.get("price")))
    price_model.set_next_price(_num(data.get("next_price")))
    price_model.set_max_price(_num(data.get("max_price")))
    price_model.set_next_hours(_num(data.get("stay_time")))
    price_model.set_start_hours(_num(data.get("initial_time")))
    price_model.set_max_hours(_num(data.get("max_hour")) or 24)
    price_model.set_overstay_price(_num(data.get("overnight_price")))
    price_model.set_overstay_affected_user(data.get("overstay_affected_user") or "ALL")
    price_model.set_overstay_start(data.get("overstay_start") or None)
    price_model.set_overstay_end(data.get("overstay_end") or None)
    # ponytail: lib membandingkan & membagi dgn overstay_duration tanpa guard (None->TypeError, 0->ZeroDivision);
    # validasi sudah memastikan >0 utk param DURATION, selain itu pakai sentinel agar cabang overstay tak aktif
    dur = _num(data.get("overstay_duration"))
    price_model.set_overstay_duration(dur if dur > 0 else 10**9)
    price_model.set_period_data(data.get("period_data"))
    price_model.set_overstay_parameter(data.get("overstay_parameter") or None)
    price_model.set_overstay_type(data.get("overstay_type") or None)
    price_model.set_overstay_progressive_time_start(_num(data.get("overstay_progressive_time_start")))
    price_model.set_overstay_progressive_time_next(_num(data.get("overstay_progressive_time_next")))
    price_model.set_overstay_start_price(_num(data.get("overstay_start_price")))
    price_model.set_overstay_next_price(_num(data.get("overstay_next_price")))
    price_model.set_overstay_max_price(_num(data.get("overstay_max_price")))
    price_model.set_overstay_max_hours(_num(data.get("overstay_max_hours")))
    price_model.set_overstay_product_member(data.get("overstay_product_member") or [])

    result = ParkingAmountBuilder(model=price_model).build()
    if not result:
        raise ValidationError("Perhitungan gagal, periksa kembali data yang dimasukkan")

    return {
        "total_hours": result["total_hours"],
        "is_grace_period": bool(result["grace_period"]),
        "parking_amount": result["parking"]["amount"],
        "overstay_amount": result["overnight_price"],
        "overnight_days": result["overnight_days"],
        "total_amount": result["total_amount"],
        "logs": result["logs"],
    }
