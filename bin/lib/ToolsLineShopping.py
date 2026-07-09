class ToolsLineShopping():
    def __init__(self):
        pass

    def normalize_variant_text(self, text):
        """
        ปรับข้อความสำหรับใช้เปรียบเทียบ size/variant
        - ไม่สนตัวพิมพ์เล็ก/ใหญ่
        - ตัดช่องว่างหัวท้าย
        - ลบช่องว่างระหว่างคำ
        """
        return str(text or "").strip().lower().replace(" ", "")

    def find_variant_by_size(self, data_product, size=None, quantity=1):
        """
        ค้นหา variant จาก size ที่ต้องการ และตรวจสอบ stock

        รองรับ 2 แบบ:
        - สินค้ามี variant
        - สินค้าไม่มี variant

        เงื่อนไข stock:
        - stock <= 0 ถือว่าหมด
        - stock ต้อง >= quantity จึงถือว่ามีพอ
        """
        product = (data_product or {}).get("data", {})
        has_variant = bool(product.get("has_variant", False))

        # =========================
        # กรณีไม่มี variant / ไม่มี size
        # =========================
        if not has_variant:
            stock_raw = product.get("available", 0)

            try:
                stock = int(stock_raw)
            except (TypeError, ValueError):
                stock = 0

            pseudo_variant = {
                "price": product.get("price"),
                "id": product.get("product_snapshot_id"),
                "variant_option_value1": None,
                "variant_option_value2": None,
                "img_url": product.get("img_url"),
                "available": stock,
                "instant_discount": product.get("instant_discount"),
                "discounted_price": product.get("discounted_price"),
                "product_snapshot_id": product.get("product_snapshot_id"),
            }

            if stock <= 0:
                return {
                    "ok": False,
                    "message": f"สินค้าไม่มี size และหมด stock, มี {stock}",
                    "variant": pseudo_variant
                }

            if stock >= quantity:
                return {
                    "ok": True,
                    "message": f"สินค้าไม่มี size และ stock เพียงพอ ({stock})",
                    "variant": pseudo_variant
                }

            return {
                "ok": False,
                "message": f"สินค้าไม่มี size แต่ stock ไม่พอ, มี {stock}, ต้องการ {quantity}",
                "variant": pseudo_variant
            }

        # =========================
        # กรณีมี variant / มี size
        # =========================
        variants = product.get("product_variants", [])

        if not variants:
            return {
                "ok": False,
                "message": "ไม่พบตัวเลือกสินค้า",
                "variant": None
            }

        if size is None or str(size).strip() == "":
            return {
                "ok": False,
                "message": "สินค้านี้มี size แต่ไม่ได้ส่ง size มา",
                "variant": None
            }

        target_size = self.normalize_variant_text(size)
        matched_variant = None

        for variant in variants:
            variant_name = self.normalize_variant_text(
                variant.get("variant_option_value1", "")
            )
            if variant_name == target_size:
                matched_variant = variant
                break

        if not matched_variant:
            return {
                "ok": False,
                "message": f"ไม่พบสินค้าที่ตรงกับ size = {size}",
                "variant": None
            }

        stock_raw = matched_variant.get("available", 0)

        try:
            stock = int(stock_raw)
        except (TypeError, ValueError):
            stock = 0

        if stock <= 0:
            return {
                "ok": False,
                "message": f"สินค้า {size} หมด stock, มี {stock}",
                "variant": matched_variant
            }

        if stock >= quantity:
            return {
                "ok": True,
                "message": f"พบสินค้า {size} และ stock เพียงพอ ({stock})",
                "variant": matched_variant
            }

        return {
            "ok": False,
            "message": f"สินค้า {size} stock ไม่พอ, มี {stock}, ต้องการ {quantity}",
            "variant": matched_variant
        }

    def get_variant_id_by_size(self, data_product, size=None, quantity=1):
        """
        คืนค่า variant_id ที่ใช้สั่งซื้อได้ทันที
        รองรับทั้งสินค้ามี size และไม่มี size
        """
        result = self.find_variant_by_size(data_product, size, quantity)

        if not result["ok"]:
            return {
                "ok": False,
                "message": result["message"],
                "variant_id": None,
                "variant": result.get("variant")
            }

        variant = result["variant"]
        return {
            "ok": True,
            "message": result["message"],
            "variant_id": variant.get("id"),
            "variant": variant
        }

    def build_checkout_payload(self, data_product, size=None, quantity=1,
                               disable_auto_apply=False, is_gift=False):
        """
        สร้าง payload สำหรับ checkout จากข้อมูลสินค้า
        รองรับทั้งสินค้ามี size และไม่มี size
        """
        product = (data_product or {}).get("data", {})
        product_id = product.get("id")
        shop_id = product.get("shop_id")

        if not product_id:
            return {
                "ok": False,
                "message": "ไม่พบ product_id ใน data_product",
                "payload": None,
                "variant": None
            }

        if not shop_id:
            return {
                "ok": False,
                "message": "ไม่พบ shop_id ใน data_product",
                "payload": None,
                "variant": None
            }

        result = self.find_variant_by_size(data_product, size, quantity)
        if not result["ok"]:
            return {
                "ok": False,
                "message": result["message"],
                "payload": None,
                "variant": result.get("variant")
            }

        variant = result["variant"]
        variant_id = variant.get("id")

        if not variant_id:
            return {
                "ok": False,
                "message": "ไม่พบ productVariantId / product_snapshot_id",
                "payload": None,
                "variant": variant
            }

        payload = {
            "shopId": shop_id,
            "products": [
                {
                    "productId": product_id,
                    "productVariantId": variant_id,
                    "quantity": quantity,
                },
            ],
            "disableAutoApply": disable_auto_apply,
            "isGift": is_gift,
        }

        return {
            "ok": True,
            "message": "สร้าง payload checkout สำเร็จ",
            "payload": payload,
            "variant": variant
        }

    def parse_checkout_result(self, check_out):
        """
        อ่านค่าที่สำคัญจาก response ของ api.checkout()
        """
        data = (check_out or {}).get("data", {})
        order = data.get("order", {})

        shipping_address_list = data.get("shippingAddressList", []) or []
        shipment_option_list = data.get("shipmentOptionList", []) or []
        payment_option_list = data.get("paymentOptionList", []) or []

        latest_shipping_address_id = data.get("latestShippingAddressId")
        suggested_shipping_id = data.get("suggestedShippingId")
        latest_payment = data.get("latestPayment")

        selected_address = None
        selected_address_id = None

        if latest_shipping_address_id is not None:
            for addr in shipping_address_list:
                if addr.get("id") == latest_shipping_address_id:
                    selected_address = addr
                    selected_address_id = addr.get("id")
                    break

        if selected_address is None and shipping_address_list:
            selected_address = shipping_address_list[0]
            selected_address_id = selected_address.get("id")

        selected_shipment = None
        selected_shipment_id = None

        if suggested_shipping_id is not None:
            for ship in shipment_option_list:
                if ship.get("id") == suggested_shipping_id:
                    selected_shipment = ship
                    selected_shipment_id = ship.get("id")
                    break

        if selected_shipment is None and shipment_option_list:
            selected_shipment = shipment_option_list[0]
            selected_shipment_id = selected_shipment.get("id")

        selected_payment = None
        selected_payment_name = None

        if latest_payment:
            for pay in payment_option_list:
                if pay.get("name") == latest_payment:
                    selected_payment = pay
                    selected_payment_name = pay.get("name")
                    break

        if selected_payment is None and payment_option_list:
            selected_payment = payment_option_list[0]
            selected_payment_name = selected_payment.get("name")

        return {
            "ok": True,
            "message": "อ่านข้อมูล checkout สำเร็จ",
            "data": {
                "order": order,
                "shipping_address_id": selected_address_id,
                "shipping_address": selected_address,
                "shipment_option_id": selected_shipment_id,
                "shipment_option": selected_shipment,
                "payment_name": selected_payment_name,
                "payment_option": selected_payment,
                "shop_id": (data.get("shopDetail") or {}).get("id"),
                "shop_name": (data.get("shopDetail") or {}).get("shopName"),
                "subtotal": order.get("subtotal"),
                "total": order.get("total"),
                "latest_payment": latest_payment,
                "suggested_shipping_id": suggested_shipping_id
            }
        }

    def get_checkout_summary(self, check_out):
        """
        สรุปข้อมูล checkout แบบพร้อมใช้งาน
        """
        result = self.parse_checkout_result(check_out)
        if not result["ok"]:
            return result

        data = result["data"]
        shipping_address = data.get("shipping_address") or {}
        shipment_option = data.get("shipment_option") or {}
        payment_option = data.get("payment_option") or {}

        summary = {
            "shop_name": data.get("shop_name"),
            "total": data.get("total"),
            "shipping_address_id": data.get("shipping_address_id"),
            "recipient_name": shipping_address.get("recipientName"),
            "phone_number": shipping_address.get("phoneNumber"),
            "full_address": " ".join([
                str(shipping_address.get("address") or ""),
                str(shipping_address.get("subDistrict") or ""),
                str(shipping_address.get("district") or ""),
                str(shipping_address.get("province") or ""),
                str(shipping_address.get("postalCode") or "")
            ]).strip(),
            "shipment_option_id": data.get("shipment_option_id"),
            "shipment_name": shipment_option.get("name"),
            "shipment_price": shipment_option.get("price"),
            "payment_name": data.get("payment_name"),
            "payment_display_name": payment_option.get("displayName"),
        }

        return {
            "ok": True,
            "message": "สรุป checkout สำเร็จ",
            "summary": summary
        }

    def build_selected_checkout_options(self, check_out):
        """
        ดึงค่าที่ระบบเลือกให้แล้ว เพื่อนำไปใช้ต่อกับ endpoint ถัดไป
        """
        result = self.parse_checkout_result(check_out)
        if not result["ok"]:
            return {
                "ok": False,
                "message": result["message"],
                "payload": None
            }

        data = result["data"]

        payload = {
            "shippingAddressId": data.get("shipping_address_id"),
            "shipmentOptionId": data.get("shipment_option_id"),
            "paymentName": data.get("payment_name"),
        }

        return {
            "ok": True,
            "message": "สร้าง selected checkout options สำเร็จ",
            "payload": payload
        }

    def _build_shipping_address_for_order(self, address):
        address = address or {}
        return {
            "id": address.get("id"),
            "recipient_name": address.get("recipientName"),
            "address": address.get("address"),
            "sub_district": address.get("subDistrict"),
            "district": address.get("district"),
            "province": address.get("province"),
            "postal_code": address.get("postalCode"),
            "country": address.get("country"),
            "country_id": address.get("countryId"),
            "phone_number": address.get("phoneNumber"),
            "email": address.get("email"),
            "note_to_driver": address.get("noteToDriver"),
            "pinned_location": address.get("pinnedLocation"),
            "pinned_address": address.get("pinnedAddress"),
            "is_out_of_service_area": address.get("isOutOfServiceArea", False),
        }

    def _build_order_items_from_checkout(self, order_items, preorder_shipping_option="NO_PREORDER"):
        result_items = []
        for item in order_items or []:
            result_items.append({
                "product_id": item.get("productId"),
                "product_variant_id": item.get("productVariantId"),
                "is_promotion": item.get("isPromotion", False),
                "quantity": item.get("quantity", 1),
                "preorder_shipping_option": item.get("preorderShippingOption") or preorder_shipping_option,
                "preorder_shipping_date": item.get("preorderShippingDate"),
                "preorder_shipping_period": item.get("preorderShippingPeriod"),
            })
        return result_items

    def _build_single_order_item_from_product(self, data_product, size=None, quantity=1):
        """
        fallback กรณี checkout response ไม่มี order.items
        """
        product = (data_product or {}).get("data", {})
        result = self.find_variant_by_size(data_product, size, quantity)

        if not result["ok"]:
            return None

        variant = result.get("variant") or {}
        preorder_shipping_option = product.get("preorder_option") or "NO_PREORDER"

        return {
            "product_id": product.get("id"),
            "product_variant_id": variant.get("id"),
            "is_promotion": False,
            "quantity": quantity,
            "preorder_shipping_option": preorder_shipping_option,
            "preorder_shipping_date": None,
            "preorder_shipping_period": None,
        }

    def build_create_order_payload(self, check_out, data_product=None, size=None, quantity=1,
                                   payment_app_switch_id=None,
                                   is_android=False,
                                   is_liff=False,
                                   remark_buyer="",
                                   point=None,
                                   ignore_point=None,
                                   promotion_id="",
                                   cart_id="",
                                   gift_info=None,
                                   seller_product_discount_coupon=None,
                                   seller_shipping_discount_coupon=None,
                                   subsidised_product_discount_coupon=None,
                                   bank_transfer=None):
        """
        สร้าง payload สำหรับ endpoint สร้าง order ต่อจาก response ของ api.checkout()

        ลำดับการหา items:
        1. ใช้ order.items จาก checkout ถ้ามี
        2. ถ้าไม่มี ให้ fallback จาก data_product + size + quantity
        """
        parsed = self.parse_checkout_result(check_out)
        if not parsed["ok"]:
            return {
                "ok": False,
                "message": parsed["message"],
                "payload": None
            }

        data = parsed["data"]
        order = data.get("order") or {}
        shipping_address = data.get("shipping_address") or {}

        preorder_shipping_option = "NO_PREORDER"
        if data_product:
            preorder_shipping_option = (
                ((data_product or {}).get("data") or {}).get("preorder_option")
                or preorder_shipping_option
            )

        items = self._build_order_items_from_checkout(
            order_items=order.get("items", []),
            preorder_shipping_option=preorder_shipping_option,
        )

        if not items and data_product:
            fallback_item = self._build_single_order_item_from_product(
                data_product=data_product,
                size=size,
                quantity=quantity,
            )
            if fallback_item:
                items = [fallback_item]

        if not items:
            return {
                "ok": False,
                "message": "ไม่พบ items ใน checkout result และไม่สามารถสร้าง fallback item จาก data_product ได้",
                "payload": None
            }

        shipping_address_payload = self._build_shipping_address_for_order(shipping_address)

        payload = {
            "customer_address_id": str(data.get("shipping_address_id") or ""),
            "shop_shipment_channel_id": str(data.get("shipment_option_id") or ""),
            "shipping_address": shipping_address_payload,
            "payment_app_switch_id": payment_app_switch_id,
            "is_android": is_android,
            "is_liff": is_liff,
            "remark_buyer": remark_buyer,
            "point": point,
            "ignore_point": ignore_point,
            "promotion_id": promotion_id,
            "items": items,
            "cart_id": cart_id,
            "gift_info": gift_info,
            "is_preorder": order.get("isPreorder", False),
            "seller_product_discount_coupon": seller_product_discount_coupon,
            "seller_shipping_discount_coupon": seller_shipping_discount_coupon,
            "subsidised_product_discount_coupon": subsidised_product_discount_coupon,
            "bank_transfer": bank_transfer,
        }

        return {
            "ok": True,
            "message": "สร้าง payload create order สำเร็จ",
            "payload": payload
        }