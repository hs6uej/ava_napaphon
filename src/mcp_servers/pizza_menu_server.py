#!/usr/bin/env python3
import sys
import json
import os
import argparse

# --- Configuration ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")


def _load_config_file(config_path: str) -> dict:
    """Load optional YAML/JSON config file to override defaults (e.g. data_dir)."""
    if not config_path or not os.path.isfile(config_path):
        return {}
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            content = f.read()
        # Try JSON first, then YAML
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            try:
                import yaml  # type: ignore
                return yaml.safe_load(content) or {}
            except Exception:
                return {}
    except Exception as e:
        sys.stderr.write(f"DEBUG: Could not load config file {config_path}: {e}\n")
        return {}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Pizza Menu MCP Server")
    parser.add_argument(
        "--config",
        default=None,
        help="Path to optional YAML/JSON config file (e.g. /app/config/pizza-menu-python-config.yaml)",
    )
    return parser.parse_args()


# Apply optional config overrides
_args = _parse_args()
_file_cfg = _load_config_file(_args.config) if _args.config else {}
if _file_cfg.get("data_dir"):
    DATA_DIR = _file_cfg["data_dir"]

def log(msg: str):
    sys.stderr.write(f"DEBUG: {msg}\n")
    sys.stderr.flush()

def load_file(filename: str, is_json=True):
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        return {} if is_json else ""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f) if is_json else f.read()
    except Exception as e:
        return {} if is_json else ""

# --- Tools Logic ---
def get_daily_recommend():
    content = load_file("recommend.txt", is_json=False)
    if not content:
        content = "ขออภัยครับ ขณะนี้ยังไม่มีเมนูแนะนำพิเศษสำหรับวันนี้"
    return {"content": [{"type": "text", "text": content}]}

def get_upsell_strategy():
    """เส้นที่ 6: อ่านจาก upsell.txt สำหรับกลยุทธ์การขายเพิ่ม"""
    content = load_file("upsell.txt", is_json=False)
    if not content:
        content = "แนะนำให้อัปเกรดเป็นขอบชีส หรือเพิ่มเครื่องดื่มเพื่อความคุ้มค่า"
    return {"content": [{"type": "text", "text": content}]}

def get_promos_and_recommendations():
    recom = load_file("[UAT] RECOMMEND.json")
    promo = load_file("[UAT] PROMOTION.json")
    return {"content": [{"type": "text", "text": json.dumps({"recommendations": recom, "promotions": promo}, ensure_ascii=False)}]}

def search_menu(keyword: str):
    files_to_search = ["[UAT] PIZZA.json", "[UAT] APPETIZERS.json", "[UAT] COMBO.json"]
    results_dict = {}
    keyword_lower = keyword.lower()
    for f_name in files_to_search:
        data = load_file(f_name)
        for cat in data.get("categories", []):
            for item in cat.get("items", []):
                name_th = item.get("name_th", "")
                name_en = item.get("name_en", "")
                item_id = item.get("code")
                if keyword_lower in name_th.lower() or keyword_lower in name_en.lower():
                    if item_id and item_id not in results_dict:
                        results_dict[item_id] = {
                            "id": item_id, "name": name_th, 
                            "note": "ใช้ get_item_details เพื่อเช็คราคา ไซส์ และขอบ"
                        }
    results = list(results_dict.values())
    return {"content": [{"type": "text", "text": json.dumps(results, ensure_ascii=False) if results else f"ไม่พบเมนู '{keyword}'"}]}

def get_item_details(item_id: str):
    files_to_search = ["[UAT] PIZZA.json", "[UAT] APPETIZERS.json", "[UAT] COMBO.json"]
    item_detail = None
    for f_name in files_to_search:
        data = load_file(f_name)
        for cat in data.get("categories", []):
            for item in cat.get("items", []):
                if item.get("code") == item_id:
                    item_detail = item
                    break
            if item_detail: break
        if item_detail: break

    if not item_detail:
        return {"content": [{"type": "text", "text": f"ไม่พบรายละเอียดของรหัสสินค้า: {item_id}"}]}

    simplified_sizes = []
    for size in item_detail.get("subitems", []):
        crusts = [f"{c.get('crust_name_th')} (+{c.get('price')}฿)" for c in size.get("crust", [])]
        simplified_sizes.append({"size": size.get("sizename_th"), "base_price": size.get("price"), "crusts": crusts})

    simplified_toppings = []
    toppings_data = load_file("[UAT] ADDON_TOPPINGS.json")
    try:
        addon_list = toppings_data.get("AddonToppingsList", [])
        if addon_list:
            for t in addon_list[0].get("PIZZA", {}).get("M", {}).get("TOPPING", []):
                simplified_toppings.append(f"{t.get('ingr_name_th')} (+{t.get('price')}฿)")
    except Exception: pass

    response_data = {
        "name": item_detail.get("name_th"), "description": item_detail.get("description_th"),
        "sizes_and_crusts": simplified_sizes, "addons": simplified_toppings
    }
    return {"content": [{"type": "text", "text": json.dumps(response_data, ensure_ascii=False)}]}

def get_business_rules(topic: str):
    topic = topic.lower()
    if topic == "selling_time": data = load_file("[UAT] SELLING_TIME.json")
    elif topic == "pricing": data = {"pricing_rules_text": load_file("Calculate Price & Concept Price.txt", is_json=False)}
    elif topic == "half_half": data = {"half_half_available_items": load_file("[UAT] HALF.json"), "half_half_order_structure": load_file("Half-Half Pizza - Create order.json")}
    else: return {"content": [{"type": "text", "text": "Topic ต้องเป็น selling_time, pricing, หรือ half_half"}]}
    return {"content": [{"type": "text", "text": json.dumps(data, ensure_ascii=False)}]}

# --- MCP Protocol Helpers ---
def send_rpc(req_id, result):
    resp = {"jsonrpc": "2.0", "id": req_id, "result": result}
    body = json.dumps(resp, ensure_ascii=False).encode('utf-8')
    header = f"Content-Length: {len(body)}\r\n\r\n".encode('utf-8')
    sys.stdout.buffer.write(header + body)
    sys.stdout.buffer.flush()

def main():
    while True:
        header_line = sys.stdin.buffer.readline()
        if not header_line: break
        header = header_line.decode('utf-8', errors='replace').strip()
        if header.startswith("Content-Length:"):
            try:
                content_length = int(header.split(":")[1].strip())
                sys.stdin.buffer.readline() 
                body_bytes = sys.stdin.buffer.read(content_length)
                body_str = body_bytes.decode('utf-8', errors='replace')
                req = json.loads(body_str)
                mid = req.get("id")
                method = req.get("method")
                params = req.get("params", {})

                if method == "initialize":
                    send_rpc(mid, {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}}, "serverInfo": {"name": "pizza_menu", "version": "4.3.0"}})
                elif method == "tools/list":
                    send_rpc(mid, {"tools": [
                        {"name": "get_promos", "description": "ดึงเมนูแนะนำ", "inputSchema": {"type": "object", "properties": {}}},
                        {"name": "search_menu", "description": "ค้นหาเมนู", "inputSchema": {"type": "object", "properties": {"keyword": {"type": "string"}}, "required": ["keyword"]}},
                        {"name": "get_item_details", "description": "ดูรายละเอียด", "inputSchema": {"type": "object", "properties": {"item_id": {"type": "string"}}, "required": ["item_id"]}},
                        {"name": "get_business_rules", "description": "ดูกฎ", "inputSchema": {"type": "object", "properties": {"topic": {"type": "string"}}, "required": ["topic"]}},
                        {"name": "get_daily_recommend", "description": "ดึงเมนูแนะนำพิเศษจาก recommend.txt"},
                        {"name": "get_upsell_strategy", "description": "ดึงสคริปต์เสนอขายเพิ่ม (Upsell) จาก upsell.txt"}
                    ]})
                elif method == "tools/call":
                    t_name = params.get("name")
                    t_args = params.get("arguments", {})
                    if t_name == "get_daily_recommend": send_rpc(mid, get_daily_recommend())
                    elif t_name == "get_upsell_strategy": send_rpc(mid, get_upsell_strategy())
                    elif t_name == "get_promos": send_rpc(mid, get_promos_and_recommendations())
                    elif t_name == "search_menu": send_rpc(mid, search_menu(t_args.get("keyword", "")))
                    elif t_name == "get_item_details": send_rpc(mid, get_item_details(t_args.get("item_id", "")))
                    elif t_name == "get_business_rules": send_rpc(mid, get_business_rules(t_args.get("topic", "")))
            except Exception as e: log(f"Error: {e}")

if __name__ == "__main__":
    main()