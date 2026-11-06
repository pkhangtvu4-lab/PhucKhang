
import math
import random
from src.n4_hoang_yen_du_lieu import load_problem, default_settings, decode, bounds, a_value
from src.n3_phuc_khang_danh_gia import evaluate, evaluate_benchmark, crosses_gate, edge_excess
from src.n5_quynh_ngan_buoc_woa import repair_population
from src.n6_van_lam_woa import woa


def whale_from(route, pin):
    whale = []
    for point in route:
        whale.extend([point[0], point[1], pin])
    return whale


def near(a, b, tolerance=0.000001):
    return abs(a - b) <= tolerance


def test_cong_khe():
    problem = load_problem("khe_hep")
    gate_route = [[10,50],[20,50],[30,50],[40,50],[50,50],[60,30],[70,30],[80,30],[90,30],[95,40]]
    report = evaluate(whale_from(gate_route, 5), problem)
    assert report["valid"] and report["through_gate"]
    assert report["total"] < 220
    blocked = whale_from([[10,50],[20,50],[30,50],[40,50],[50,50],[60,50],[70,50],[80,50],[90,50],[95,50]], 5)
    report = evaluate(blocked, problem)
    assert crosses_gate(report["points"], problem)
    assert not report["valid"] and not report["geometry_ok"] and not report["through_gate"]
    assert report["bad_segments"] != []
    below = whale_from([[10,10],[20,10],[30,10],[40,10],[50,10],[60,10],[70,10],[80,10],[90,10],[95,30]], 5)
    report = evaluate(below, problem)
    assert report["valid"] and not report["through_gate"]
    assert crosses_gate([[30,48],[50,52]], problem)
    assert not crosses_gate([[30,10],[50,12]], problem)
    assert not crosses_gate([[30,48],[50,52]], load_problem("co_ban"))


def test_vi_pham():
    problem = load_problem("co_ban")
    clean = whale_from([[10,10],[20,10],[30,10],[40,10],[50,10],[60,10],[70,10],[80,10],[88,12],[95,30]], 10)
    base = evaluate(clean, problem)
    assert base["valid"] and base["box_ok"] and base["geometry_ok"] and base["energy_ok"]
    assert near(base["penalty"], 0) and near(base["score"], base["base_score"])
    assert near(base["base_score"], -base["utility_sat"] + 0.12 * base["length"] / 100)
    assert near(base["total"], 0.45 * base["length"] + 100)
    through = clean.copy()
    through[0:2] = [28, 20]
    through[3:5] = [28, 80]
    report = evaluate(through, problem)
    assert not report["geometry_ok"] and not report["valid"] and report["collision"] > 0
    assert report["penalty"] > 0
    soft = clean.copy()
    soft[0:2] = [28, 59]
    soft[3:5] = [28, 59]
    report = evaluate(soft, problem)
    assert report["collision"] > 0 and not report["valid"]
    heavy = clean.copy()
    for k in range(10):
        heavy[3 * k + 2] = 25
    report = evaluate(heavy, problem)
    assert not report["energy_ok"] and report["geometry_ok"] and not report["valid"]
    assert near(report["penalty"], 30 * report["over"] ** 2)
    outside = clean.copy()
    outside[0] = 108
    report = evaluate(outside, problem)
    assert not report["box_ok"] and not report["valid"]
    assert near(report["map_violation"], 0.08 * 0.08)
    assert outside[0] == 108
    assert near(edge_excess(-5, 0, 100), 0.05) and edge_excess(40, 0, 100) == 0
    big = clean.copy()
    big[2] = 30
    assert not evaluate(big, problem)["box_ok"]
    bad = clean.copy()
    bad[4] = float("nan")
    assert not evaluate(bad, problem)["valid"]
    try:
        evaluate(clean[:29], problem)
        assert False
    except ValueError:
        pass
    report = evaluate(through, problem)
    total = report["base_score"] + 100 * report["collision"] + 30 * report["over"] ** 2 + 100 * report["map_violation"]
    assert near(report["score"], total)


def test_so_den_va_a():
    problem = load_problem("khe_hep")
    route = [[10,50],[20,50],[30,50],[40,50],[50,50],[60,30],[70,30],[80,30],[90,30],[95,40]]
    whale = whale_from(route, 5)
    for K in [6, 8, 10]:
        problem["active_lights"] = K
        count = 0
        for beacon in decode(whale, problem):
            if beacon["active"]:
                count += 1
        assert count == K and len(whale) == 30
    assert a_value(0, 800, "linear") == 2
    assert abs(a_value(799, 800, "linear") - 0.0025) < 0.0000001


def test_benchmark():
    cases = [("quadratic", 1, -20, 20, 0.00000001, [7]),
             ("sphere", 30, -100, 100, 0.00000001, [0] * 30),
             ("rastrigin", 30, -5.12, 5.12, 0.000001, [0] * 30)]
    for name, dimensions, lower, upper, target, optimum in cases:
        problem = {"function": name, "dimensions": dimensions, "lower": lower,
                   "upper": upper, "target": target}
        report = evaluate_benchmark(optimum, problem)
        assert report["score"] == 0 and report["success"]
        # Đáp án nằm ngoài miền gốc thì không tính là thành công.
        outside = optimum.copy()
        outside[0] = upper + 1
        assert not evaluate_benchmark(outside, problem)["in_domain"]
    quad = {"function": "quadratic", "lower": -20, "upper": 20, "target": 0.00000001}
    assert not evaluate_benchmark([7.001], quad)["success"]     # (0.001)^2 = 1e-6 > 1e-8
    assert evaluate_benchmark([-3], quad)["score"] == 100        # miền gốc có số âm
    sphere = {"function": "sphere", "dimensions": 30, "lower": -100, "upper": 100, "target": 1e-8}
    assert evaluate_benchmark([1, 2, 3] + [0] * 27, sphere)["score"] == 14


def test_woa_tai_lap():
    s = default_settings()
    s["iterations"] = 120
    bench = {"function": "sphere", "dimensions": 30, "lower": -100, "upper": 100}
    result = woa(evaluate_benchmark, bench, s)
    assert result["evaluations"] == 30 * 120
    assert result["best_overall"]["evaluation"]["score"] < 0.000001
    repeat = woa(evaluate_benchmark, bench, s)
    assert result["best_overall"] == repeat["best_overall"]
    assert result["history"] == repeat["history"]
    pop = [[-5, 0.5, 6]]
    repair_population(pop, [0, 0, 0], [1, 1, 1], "clip", random.Random(7))
    assert pop == [[0, 0.5, 1]]


def main():
    test_cong_khe()
    test_vi_pham()
    test_so_den_va_a()
    test_benchmark()
    test_woa_tai_lap()
    print("Qua kiểm tra: khe có đường hợp lệ, bão, pin, 30 biến, số đèn, a, biên, seed và benchmark.")


if __name__ == "__main__":
    main()
