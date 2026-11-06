
import json
import math
import sys
from src.n4_hoang_yen_du_lieu import ROOT, bounds
from src.n3_phuc_khang_danh_gia import evaluate, evaluate_benchmark, crosses_gate
from src.n8_trang_bui_thong_ke import load_runs

TOL = 0.000000001
errors = []


def complain(where, message):
    errors.append(where + ": " + message)


def same(a, b):
    return math.isclose(a, b, abs_tol=TOL, rel_tol=1e-9)


def circle_check(points, storms, safety):
    bad = []
    for i in range(len(points) - 1):
        ax, ay = points[i]
        bx, by = points[i + 1]
        dx = bx - ax
        dy = by - ay
        A = dx * dx + dy * dy
        for v, storm in enumerate(storms):
            px = ax - storm["x"]
            py = ay - storm["y"]
            radius = storm["r"] + safety - 0.00000001
            C = px * px + py * py - radius * radius
            if C < -0.000001:
                bad.append((i, v))         
                continue
            if A < 1e-18:
                continue
            B = 2 * (px * dx + py * dy)
            discriminant = B * B - 4 * A * C
            if discriminant > 0.0000001:
                left = (-B - math.sqrt(discriminant)) / (2 * A)
                right = (-B + math.sqrt(discriminant)) / (2 * A)
                if min(1, right) - max(0, left) > 0.0000001:
                    bad.append((i, v))
    return bad


def independent_totals(report):
    length = 0
    for i in range(len(report["points"]) - 1):
        a = report["points"][i]
        b = report["points"][i + 1]
        length += math.hypot(b[0] - a[0], b[1] - a[1])
    lamps = 0
    for beacon in report["beacons"]:
        lamps += beacon["energy"]
    return length, 0.45 * length + lamps


def check_item(tag, key, item, problem):
    where = tag + "." + key
    position = item["position"]
    if len(position) != 30:
        complain(where, "position dài " + str(len(position)) + ", cần 30")
        return
    for j in range(30):
        if not math.isfinite(position[j]):
            complain(where, "ô " + str(j) + " không hữu hạn")
            return
    fresh = evaluate(position, problem)
    for metric in ["score", "base_score", "utility_sat", "total", "length"]:
        if not same(fresh[metric], item["evaluation"][metric]):
            complain(where, metric + " lưu " + str(item["evaluation"][metric]) + " != chấm lại " + str(fresh[metric]))
    if fresh["valid"] != item["evaluation"]["valid"]:
        complain(where, "valid lưu khác chấm lại")
    j_value = (fresh["base_score"] + problem["collision_weight"] * fresh["collision"]
               + problem["battery_weight"] * fresh["over"] ** 2
               + problem["map_weight"] * fresh["map_violation"])
    if not same(j_value, fresh["score"]):
        complain(where, "J không khớp công thức ghép")
    length, total = independent_totals(fresh)
    if not same(length, fresh["length"]) or not same(total, fresh["total"]):
        complain(where, "độ dài/pin khác phép tính độc lập")
    if key in ["best_valid", "best_gate"]:
        if not fresh["valid"]:
            complain(where, "không hợp lệ khi chấm lại nhưng nằm trong sổ hợp lệ")
        if fresh["total"] > problem["budget"] + 0.0000001:
            complain(where, "quá pin 220")
        bad = circle_check(fresh["points"], problem["storms"], problem["safety"])
        if bad:
            complain(where, "kiểm hình học độc lập thấy đoạn lấn bão: " + str(bad[:3]))
    if key == "best_gate":
        if not fresh["through_gate"] or not crosses_gate(fresh["points"], problem):
            complain(where, "không phải đường hợp lệ qua khe")
    return fresh


def main():
    runs = load_runs(ROOT / "results")
    if len(runs) != 330:
        complain("tổng", "có " + str(len(runs)) + " lượt ứng dụng, cần 330")
    groups = {}
    valid_count = 0
    for result in runs:
        name = result["experiment"]["id"]
        seed = result["settings"]["seed"]
        tag = name + "/seed" + str(seed)
        groups.setdefault(name, []).append(seed)
        if result["evaluations"] != 24000:
            complain(tag, "số lượt chấm " + str(result["evaluations"]) + " != 24000")
        if result["problem"]["budget"] != 220:
            complain(tag, "pin chuẩn không phải 220")
        lower, upper = bounds(result["problem"])
        best_score = result["best_overall"]["evaluation"]["score"]
        for index, whale in enumerate(result["final_population"]):
            if len(whale) != 30:
                complain(tag, "final_population[" + str(index) + "] không đủ 30 biến")
                continue
            for j in range(30):
                if not lower[j] <= whale[j] <= upper[j]:
                    complain(tag, "final_population[" + str(index) + "][" + str(j) + "] ngoài miền")
            if best_score > evaluate(whale, result["problem"])["score"] + TOL:
                complain(tag, "best_overall có J cao hơn một cá voi đã chấm")
        fresh = {}
        for key in ["best_overall", "best_valid", "best_gate"]:
            if result[key] is not None:
                fresh[key] = check_item(tag, key, result[key], result["problem"])
        if "best_valid" in fresh and fresh["best_valid"] and fresh["best_overall"]:
            if fresh["best_overall"]["score"] > fresh["best_valid"]["score"] + TOL:
                complain(tag, "best_overall (J) cao hơn J của best_valid")
        if "best_gate" in fresh and fresh["best_gate"] and "best_valid" in fresh and fresh["best_valid"]:
            if fresh["best_valid"]["base_score"] > fresh["best_gate"]["base_score"] + TOL:
                complain(tag, "best_valid có f0 cao hơn best_gate, vậy best_gate không thể là nhóm con")
        if result["best_gate"] is not None and result["best_valid"] is None:
            complain(tag, "có best_gate mà không có best_valid")
        if result["best_valid"] is not None:
            valid_count += 1
    if len(groups) != 11:
        complain("tổng", "có " + str(len(groups)) + " cấu hình, cần 11")
    for name in groups:
        if sorted(groups[name]) != list(range(1, 31)):
            complain(name, "seed không đủ 1..30")

    benchmark_count = 0
    for path in sorted((ROOT / "results" / "benchmarks").glob("*/seed_*.json")):
        result = json.loads(path.read_text())
        tag = path.parent.name + "/" + path.stem
        fresh_b = evaluate_benchmark(result["best_overall"]["position"], result["problem"])
        if not same(fresh_b["score"], result["best_overall"]["evaluation"]["score"]):
            complain(tag, "điểm benchmark lưu khác chấm lại")
        if not fresh_b["in_domain"]:
            complain(tag, "đáp án nằm ngoài miền gốc")
        if fresh_b["score"] > result["problem"]["target"]:
            complain(tag, "chưa đạt ngưỡng " + str(result["problem"]["target"]))
        if result["evaluations"] != 15000:
            complain(tag, "số lượt chấm != 15000")
        benchmark_count += 1
    if benchmark_count != 90:
        complain("benchmark", "có " + str(benchmark_count) + " lượt, cần 90")

    if errors:
        print("CÓ", len(errors), "LỖI DỮ LIỆU (xử lý trước khi đưa lên hình):")
        for line in errors[:40]:
            print(" -", line)
        sys.exit(1)
    print("Đã kiểm 330 lượt ứng dụng;", valid_count, "lượt có best_valid; các đường qua kiểm hình học độc lập.")
    print("Điểm J khớp công thức ghép; ba sổ đúng vai trò; pin và độ dài khớp phép tính khác.")
    print("Đàn cuối là 30 mảng 30 biến trong miền; 90 benchmark đạt ngưỡng ở miền gốc; số lượt chấm đúng.")


if __name__ == "__main__":
    main()
