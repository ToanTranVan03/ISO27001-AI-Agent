import subprocess
import psutil
import time
import ollama
import json

def get_rtx3050_vram_usage() -> dict:
    """Đọc mức sử dụng VRAM thực tế từ card NVIDIA GeForce RTX 3050 qua lệnh hệ thống."""
    try:
        output = subprocess.check_output(
            [
                "nvidia-smi",
                "--query-gpu=name,memory.used,memory.total,utilization.gpu",
                "--format=csv,noheader,nounits"
            ],
            encoding="utf-8"
        ).strip()
        name, used, total, util = [x.strip() for x in output.split(",")]
        return {
            "gpu_name": name,
            "vram_used_mb": int(used),
            "vram_total_mb": int(total),
            "gpu_utilization_percent": int(util)
        }
    except Exception as e:
        return {"error": "Không đọc được NVIDIA-SMI. Hãy đảm bảo driver NVIDIA đã cài chuẩn."}

def benchmark_local_slm(model_name: str = "qwen2.5:7b"):
    print(f"--- Đang chạy thử nghiệm model: {model_name} ---")
    start_time = time.perf_counter()

    # Gọi trực tiếp model bạn vừa tải về
    response = ollama.chat(
        model=model_name,
        messages=[
            {
                "role": "system",
                "content": "Bạn là chuyên gia an toàn thông tin ISO/IEC 27001. Trả lời ngắn gọn bằng tiếng Việt."
            },
            {
                "role": "user",
                "content": "Nêu 3 bằng chứng kỹ thuật cần thu thập cho control A.8.5 (Xác thực an toàn)."
            }
        ],
        options={
            "temperature": 0.0,
            "num_ctx": 4096  # Giới hạn context để không tràn 8GB VRAM
        }
    )

    latency = time.perf_counter() - start_time
    vram_after = get_rtx3050_vram_usage()
    ram_info = psutil.virtual_memory()

    eval_count = response.get("eval_count", 0)
    eval_duration_sec = response.get("eval_duration", 1) / 1e9
    tokens_per_sec = round(eval_count / eval_duration_sec, 2) if eval_duration_sec > 0 else 0

    report = {
        "benchmark_result": {
            "model": model_name,
            "latency_seconds": round(latency, 3),
            "generation_speed_tokens_per_sec": tokens_per_sec,
            "vram_used_mb": vram_after.get("vram_used_mb"),
            "system_ram_used_gb": round(ram_info.used / (1024**3), 2)
        },
        "sample_output": response["message"]["content"]
    }
    return report

if __name__ == "__main__":
    # Chạy hàm và in kết quả ra màn hình
    result = benchmark_local_slm("qwen2.5:7b")
    print("\n=== KẾT QUẢ KHẢO SÁT TUẦN 1 CỦA TOÀN ===")
    print(json.dumps(result, ensure_ascii=False, indent=2))