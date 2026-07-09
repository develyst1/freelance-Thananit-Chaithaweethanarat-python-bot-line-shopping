import time
from datetime import datetime

from requests import options

from bin.lib.ApiLineShopping import ApiiLineShopping
from bin.lib.ToolsLineShopping import ToolsLineShopping


# =========================
# CONFIG
# =========================
token = "eyJhbGciOiJIUzI1NiJ9.xmdZo9YLO30SgJhL6l6oJ175V7ZEM1FtRziTyhWdj5LArVjmtpvnYmK98ihgd0OB7QOJpGa2y6aMDaYFBo6xHn6QNhEykzfRKKmvRppeMAAM12inSgJgPVH6dLX6UnZD3m3pGCzPFILjobgpBKJX5qhEYORJta77KTSLFCm99Oc.7nWCBzJVldqr4Wiyfecsjty7CWh2aZvc7rnPgLj-PnA"

shop_name = "@wishgroup_officia"
id_product = 1008184470
size = ""
quantity = 1

start_bot_at = None

use_time_mode = True

allowed_time_ranges = [
    ("9:59:59", "23:59:59")
]

poll_interval_seconds = 1
auto_checkout_and_order = True

checkout_disable_auto_apply = False
checkout_is_gift = False

payment_app_switch_id = None
is_android = False
is_liff = False
remark_buyer = ""
point = None
ignore_point = None
promotion_id = ""
cart_id = ""
gift_info = None
seller_product_discount_coupon = None
seller_shipping_discount_coupon = None
subsidised_product_discount_coupon = None
bank_transfer = None


def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def parse_datetime(value):
    if not value:
        return None

    value = str(value).strip()
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            pass
    raise ValueError("รูปแบบ start_bot_at ต้องเป็น YYYY-MM-DD HH:MM[:SS]")


def parse_time_str(value):
    value = str(value).strip()
    formats = ["%H:%M:%S", "%H:%M"]
    for fmt in formats:
        try:
            return datetime.strptime(value, fmt).time()
        except ValueError:
            pass
    raise ValueError(f"รูปแบบเวลาไม่ถูกต้อง: {value}")


def wait_until_start(start_at):
    start_dt = parse_datetime(start_at)
    if start_dt is None:
        return

    while True:
        now = datetime.now()
        if now >= start_dt:
            print(f"[{now_str()}] ถึงเวลาเริ่มบอทแล้ว")
            return

        remaining = int((start_dt - now).total_seconds())
        print(f"[{now_str()}] รอเวลาเริ่มบอทอีก {remaining} วินาที")
        time.sleep(min(1, max(remaining, 1)))


def is_in_allowed_time_ranges(time_ranges, current_dt=None):
    current_dt = current_dt or datetime.now()
    current_time = current_dt.time()

    for start_str, end_str in time_ranges:
        start_t = parse_time_str(start_str)
        end_t = parse_time_str(end_str)

        if start_t <= end_t:
            if start_t <= current_time <= end_t:
                return True
        else:
            if current_time >= start_t or current_time <= end_t:
                return True

    return False


def wait_for_allowed_time_mode(enabled, time_ranges, sleep_seconds=1):
    if not enabled:
        return

    while True:
        if is_in_allowed_time_ranges(time_ranges):
            return

        print(f"[{now_str()}] ยังไม่อยู่ในช่วงเวลาที่อนุญาตให้ทำงาน")
        time.sleep(sleep_seconds)


def get_stock_text(stock_result):
    variant = stock_result.get("variant") or {}
    stock = variant.get("available")
    return str(stock)


def get_size_label(stock_result, fallback_size=""):
    variant = stock_result.get("variant") or {}
    variant_name = variant.get("variant_option_value1")

    if variant_name not in [None, ""]:
        return str(variant_name)

    if fallback_size not in [None, ""]:
        return str(fallback_size)

    return "NO_SIZE"


def wait_until_product_available(api, tools, shop_name, id_product, size, quantity,
                                 poll_interval_seconds=2,
                                 use_time_mode=False,
                                 allowed_time_ranges=None):
    allowed_time_ranges = allowed_time_ranges or [("00:00:00", "23:59:59")]

    while True:
        wait_for_allowed_time_mode(
            enabled=use_time_mode,
            time_ranges=allowed_time_ranges,
            sleep_seconds=1,
        )

        try:
            data_product = api.info_product(shop_name, id_product)
            print(data_product)

            stock_result = tools.find_variant_by_size(data_product, size, quantity)

            if stock_result["ok"]:
                print(
                    f"[{now_str()}] มีสินค้าแล้ว | "
                    f"size={get_size_label(stock_result, size)} | "
                    f"stock={get_stock_text(stock_result)}"
                )
                return data_product, stock_result

            print(
                f"[{now_str()}] ยังไม่มีสินค้า | "
                f"size={get_size_label(stock_result, size)} | "
                f"message={stock_result['message']}"
            )

        except Exception as e:
            print(f"[{now_str()}] เช็คสินค้าไม่สำเร็จ: {e}")

        time.sleep(poll_interval_seconds)


api = ApiiLineShopping(token)
tools = ToolsLineShopping()

try:
    profile = api.profile()
    try:
        display_name = profile["displayName"]
        user_id = profile["userId"]
        print(f"displayName : {display_name}")
        print(f"userId : {user_id}")
    except Exception:
        print("Login ไม่สำเร็จ เก็บ Token มาใส่ใหม่")
        raise SystemExit

    wait_until_start(start_bot_at)

    data_product, stock_result = wait_until_product_available(
        api=api,
        tools=tools,
        shop_name=shop_name,
        id_product=id_product,
        size=size,
        quantity=quantity,
        poll_interval_seconds=poll_interval_seconds,
        use_time_mode=use_time_mode,
        allowed_time_ranges=allowed_time_ranges,
    )

    if not auto_checkout_and_order:
        print(f"[{now_str()}] เจอสินค้าแล้ว แต่ตั้งค่า auto_checkout_and_order = False")
        raise SystemExit

    checkout_result = tools.build_checkout_payload(
        data_product=data_product,
        size=size,
        quantity=quantity,
        disable_auto_apply=checkout_disable_auto_apply,
        is_gift=checkout_is_gift,
    )

    if not checkout_result["ok"]:
        print("สร้าง checkout payload ไม่สำเร็จ:", checkout_result["message"])
        raise SystemExit

    checkout_payload = checkout_result["payload"]
    print(f"[{now_str()}] checkout payload พร้อมแล้ว")

    check_out = api.checkout(json_data=checkout_payload)
    print(f"[{now_str()}] checkout สำเร็จ")

    create_order_result = tools.build_create_order_payload(
        check_out=check_out,
        data_product=data_product,
        size=size,
        quantity=quantity,
        payment_app_switch_id=payment_app_switch_id,
        is_android=is_android,
        is_liff=is_liff,
        remark_buyer=remark_buyer,
        point=point,
        ignore_point=ignore_point,
        promotion_id=promotion_id,
        cart_id=cart_id,
        gift_info=gift_info,
        seller_product_discount_coupon=seller_product_discount_coupon,
        seller_shipping_discount_coupon=seller_shipping_discount_coupon,
        subsidised_product_discount_coupon=subsidised_product_discount_coupon,
        bank_transfer=bank_transfer,
    )

    if not create_order_result["ok"]:
        print("สร้าง order payload ไม่สำเร็จ:", create_order_result["message"])
        raise SystemExit

    order_payload = create_order_result["payload"]
    print(f"[{now_str()}] create order payload พร้อมแล้ว")

    create_order = api.place_order(name_shop=shop_name, json_data=order_payload)
    print("place_order result:", create_order)

finally:
    try:
        api.close()
    except Exception:
        pass