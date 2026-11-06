# Phúc Khang




| Bước | Nội dung làm | Đầu vào | Đầu ra |
|---|---|---|---|
| 1 | Ghép phiếu chấm `evaluate(whale, problem)` | Hình học của Tuấn (n1), pin/utility của Phong (n2), decode của Yến (n4) | `base_score`, `penalty`, `score` (J), `valid` và các thông tin để vẽ/lưu |
| 2 | Kiểm hợp lệ độc lập: map, pin từng đèn, tổng pin, toàn đường tránh bão | Mảng 30 số, S/T và dữ liệu bão | `box_ok`, `geometry_ok`, `energy_ok`, `valid`. Không tự sửa nghiệm |
| 3 | Kiểm cổng khe ca B | Các đoạn và cổng x = 40, y trong [47, 53] | `through_gate`: chỉ true khi **toàn đường hợp lệ**. Cắt cổng mà lấn bão vẫn bị loại |
| 4 | Benchmark ở miền gốc | (x−7)², Sphere, Rastrigin; đáp án, miền, ngưỡng | `evaluate_benchmark` và bảng điều kiện thành công |
| 5 | Chấm lại các position đã lưu | JSON ba sổ, `final_population`, ví dụ nhỏ | Score/valid khớp; lỗi dữ liệu ghi rõ trước khi vẽ hình |
| 6 | Bàn giao | Module, bảng benchmark, nhật ký kiểm tra | Cách phân biệt J, `best_overall`, `best_valid` |

## Cách chạy

```bash
python kiem_tra.py             # ví dụ nhỏ biết trước đáp án
python kiem_tra_ket_qua.py     # chấm lại 330 lượt + 90 benchmark đã lưu
```

Đầu ra thật:

```
Qua kiểm tra: khe có đường hợp lệ, bão, pin, 30 biến, số đèn, a, biên, seed và benchmark.

Đã kiểm 330 lượt ứng dụng; 322 lượt có best_valid; các đường qua kiểm hình học độc lập.
Điểm J khớp công thức ghép; ba sổ đúng vai trò; pin và độ dài khớp phép tính khác.
Đàn cuối là 30 mảng 30 biến trong miền; 90 benchmark đạt ngưỡng ở miền gốc; số lượt chấm đúng.
```

Ví dụ một lần gọi `evaluate` (ca B, đi qua khe, 10 đèn pin 5):

| | Đường qua khe `(10,50)…(40,50)…(95,40)` | Đường thẳng `y = 50` cắt cổng nhưng lấn bão V3 |
|---|---|---|
| `score` (J) | −0,4772 | 179,94 |
| `valid` | True | False |
| `geometry_ok` | True | False (đoạn 6, 7, 8 lấn bão) |
| `through_gate` | True | **False**, dù có cắt cổng |
| Pin tổng | 106,1 / 220 | |

## Ghi chú giải thích (dùng cho slide)

**Hàm mục tiêu**

```
f0 = −U + 0,12·L/100
J  = f0 + 100·Pc + 30·V² + 100·Pmap
```

- U là utility bão hòa (trung bình có trọng số 8 trại), L là chiều dài đường bay.
- Pc: phạt lấn bão, cộng bình phương độ lấn sâu của từng cặp (đoạn, bão), có biên an toàn 2.
- V: phần vượt pin 220, chuẩn hóa. Pmap: phần vượt biên bản đồ.
- Không còn phạt gấp khúc. Các mức 100 / 30 / 100 là cố định, không đưa vào ngách.

**J, best_overall, best_valid**

| Sổ | Chọn theo | Nội dung |
|---|---|---|
| `best_overall` | J thấp nhất | X\* dẫn đàn; có thể **chưa hợp lệ** vì phạt là hữu hạn, không phải bức tường |
| `best_valid` | f0 thấp nhất | Chỉ nghiệm đạt toàn bộ luật; dùng để báo cáo chất lượng đường bay |
| `best_gate` | f0 thấp nhất | Chỉ nghiệm vừa hợp lệ vừa qua khe |

Điểm thấp không đồng nghĩa với hợp lệ. Chưa có `best_valid` thì ghi "chưa có nghiệm hợp lệ", không ghi "vô nghiệm", và không cắt pin hay sửa đường sau tối ưu rồi gắn nhãn là kết quả nguyên bản.

**Điều kiện hợp lệ** (phải đạt đồng thời, tất cả số hữu hạn)

- `box_ok`: 0 ≤ x, y ≤ 100 và 0 ≤ pin ≤ 25 cho từng ô.
- `geometry_ok`: khoảng cách từ **cả 11 đoạn** tới tâm mỗi bão ≥ r + 2. Kiểm cả đoạn, không chỉ các chấm đèn.
- `energy_ok`: 0,45·L + tổng pin đèn ≤ 220.
- Dung sai 1e-9 (hình học) và 1e-7 (pin) chỉ là sai số làm tròn, không phải mức phạt mới.

**Cổng khe (ca B):** `through_gate` đúng khi có đoạn đi trái → phải với x_i < 40 ≤ x_{i+1} và y tại x = 40 nằm trong [47, 53], **và** toàn đường hợp lệ. Qua khe chỉ là chỉ số nghiên cứu; đường hợp lệ đi vòng ngoài vẫn là nghiệm hợp lệ.

**Cách đọc benchmark** (miền gốc, 30 seed, N = 30, T = 500, 15 000 lần chấm/lượt)

| Hàm | Miền | Ngưỡng | Đáp án | Thành công |
|---|---|---|---|---|
| (x − 7)² | [−20, 20] | 1e-8 | x = 7 | 30/30 |
| Sphere (30 chiều) | [−100, 100] | 1e-8 | gốc | 30/30 |
| Rastrigin (30 chiều) | [−5,12; 5,12] | 1e-6 | gốc | 30/30 |

- Một lượt thành công khi f(X\*) ≤ ngưỡng **và** X\* nằm trong miền gốc.
- Không dời hay thu miền quanh đáp án, không đưa đáp án vào giữa hộp 0..1 rồi báo là cùng bài.
- Đây là kiểm tra cài đặt WOA, không so sánh với thuật toán khác. 30/30 trên các bài này **không** chứng minh WOA tốt cho bài UAV.
