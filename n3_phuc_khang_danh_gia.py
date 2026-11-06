
import math
from src.n1_hoang_tuan_hinh_hoc import path_metrics
from src.n2_quoc_phong_nang_luong import energy_metrics, signal_metrics
from src.n4_hoang_yen_du_lieu import decode

SLOTS = 10
TOL_GEOMETRY = 0.000000001 
TOL_ENERGY = 0.0000001


def edge_excess(value, low, high):
    return max(0, low - value, value - high) / (high - low)


def check_box(whale, problem):
    for k in range(SLOTS):
        limits = [100, 100, problem["beacon_max"]]
        for j in range(3):
            value = whale[3 * k + j]
            if not math.isfinite(value) or value < 0 or value > limits[j]:
                return False
    return True


def map_violation(beacons):
    total = 0
    for beacon in beacons:
        for value in [beacon["x"], beacon["y"]]:
            excess = edge_excess(value, 0, 100)
            total += excess * excess
    return total


def crosses_gate(points, problem):
    if "gate" not in problem:
        return False
    gate = problem["gate"]
    for i in range(len(points) - 1):
        a = points[i]
        b = points[i + 1]
        if a[0] < gate["x"] <= b[0]:          # b[0] > a[0], không chia cho 0
            fraction = (gate["x"] - a[0]) / (b[0] - a[0])
            y = a[1] + fraction * (b[1] - a[1])
            if gate["y_min"] <= y <= gate["y_max"]:
                return True
    return False


def evaluate(whale, problem):
    if len(whale) != 30:
        raise ValueError("Bài nhóm giữ 30 biến: 10 bộ x, y, pin.")
    beacons = decode(whale, problem)
    points = [problem["start"]]
    for beacon in beacons:
        points.append([beacon["x"], beacon["y"]])
    points.append(problem["target"])
    path = path_metrics(points, problem["storms"], problem["safety"])
    energy = energy_metrics(path["length"], beacons, problem)
    signal = signal_metrics(beacons, problem)
    pmap = map_violation(beacons)
    base_score = -signal["utility_sat"] + problem["length_weight"] * path["length"] / 100
    penalty = (problem["collision_weight"] * path["collision"]
               + problem["battery_weight"] * energy["over"] * energy["over"]
               + problem["map_weight"] * pmap)
    box_ok = check_box(whale, problem)
    geometry_ok = path["clearance"] is None or path["clearance"] >= -TOL_GEOMETRY
    energy_ok = energy["total"] <= problem["budget"] + TOL_ENERGY
    valid = box_ok and geometry_ok and energy_ok
    result = {"score": base_score + penalty, "base_score": base_score,
              "penalty": penalty, "valid": valid, "box_ok": box_ok,
              "geometry_ok": geometry_ok, "energy_ok": energy_ok,
              "map_violation": pmap, "beacons": beacons, "points": points,
              "through_gate": valid and crosses_gate(points, problem)}
    result.update(path)
    result.update(energy)
    result.update(signal)
    return result


def evaluate_benchmark(whale, problem):
    score = 0
    if problem["function"] == "quadratic":
        score = (whale[0] - 7) * (whale[0] - 7)
    elif problem["function"] == "sphere":
        for value in whale:
            score += value * value
    elif problem["function"] == "rastrigin":
        for value in whale:
            score += value * value - 10 * math.cos(2 * math.pi * value) + 10
    else:
        raise ValueError("Benchmark chưa biết: " + str(problem["function"]))
    in_domain = True
    if "lower" in problem:
        for value in whale:
            if value < problem["lower"] or value > problem["upper"]:
                in_domain = False
    result = {"score": score, "base_score": score, "valid": True,
              "values": whale.copy(), "in_domain": in_domain}
    if "target" in problem:
        # Thành công = đủ nhỏ VÀ nằm trong miền gốc.
        result["success"] = in_domain and score <= problem["target"]
    return result
