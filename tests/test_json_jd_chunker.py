import json
import os
import random
from src.processing.jd_chunker import chunk_jd_text

def print_chunks(job: dict, index: int):
    """Hàm in kết quả chunking của một Job cụ thể."""
    title = job.get('title', 'Unknown Title')
    company = job.get('company', 'Unknown Company')
    description = job.get('description', '')
    
    print(f"\n" + "=" * 100)
    print(f"🏢 JOB [{index}]: {title} | {company}")
    print("-" * 100)
    
    if not description.strip():
        print("[ LỖI ] -> Job này không có nội dung description.\n")
        return
        
    chunks = chunk_jd_text(description, max_words=120)
    
    for chunk in chunks:
        category = chunk.get("category", "UNKNOWN")
        text = chunk.get("text", "")
        # Cắt bớt text dài để hiển thị gọn trên terminal
        display_text = text #if len(text) < 80 else text[:77] + "..."
        print(f"[{category:<14}] | {display_text}")
        
    print("=" * 100)

def run_interactive_tester(file_path: str):
    """Menu tương tác để chọn và test JD."""
    if not os.path.exists(file_path):
        print(f"❌ Không tìm thấy file: {file_path}")
        return
        
    with open(file_path, 'r', encoding='utf-8') as f:
        jobs = json.load(f)
        
    total_jobs = len(jobs)
    print(f"✅ Đã load {total_jobs} jobs từ {file_path}.")
    
    while True:
        print("\n" + "▪" * 50)
        print("🛠️ CÔNG CỤ TEST JD CHUNKER TƯƠNG TÁC")
        print(f"Phạm vi ID hợp lệ: từ 0 đến {total_jobs - 1}")
        print("  • Nhập một SỐ (VD: 5) để test Job ở vị trí đó.")
        print("  • Nhập 'r' để lấy NGẪU NHIÊN 1 Job.")
        print("  • Nhập 's <từ khóa>' để TÌM KIẾM theo tiêu đề (VD: s python).")
        print("  • Nhập 'q' để THOÁT.")
        print("▪" * 50)
        
        choice = input("👉 Lựa chọn của bạn: ").strip().lower()
        
        if choice in ['q', 'quit', 'exit']:
            print("👋 Đã thoát công cụ test. Chúc bạn code vui vẻ!")
            break
            
        elif choice == 'r':
            idx = random.randint(0, total_jobs - 1)
            print_chunks(jobs[idx], idx)
            
        elif choice.startswith('s '):
            keyword = choice[2:].strip()
            results = []
            for i, j in enumerate(jobs):
                t = j.get('title', '').lower()
                c = j.get('company', '').lower()
                if keyword in t or keyword in c:
                    results.append((i, j.get('title', ''), j.get('company', '')))
            
            if not results:
                print(f"❌ Không tìm thấy Job nào chứa từ khóa '{keyword}'.")
            else:
                print(f"\n🔍 Tìm thấy {len(results)} kết quả. Gõ số ID để xem chi tiết:")
                # Chỉ in tối đa 15 kết quả để khỏi trôi màn hình
                for idx, t, c in results[:15]: 
                    print(f"  ID [{idx:>3}] : {t} | {c}")
                if len(results) > 15:
                    print(f"  ... (và {len(results) - 15} kết quả khác)")
                    
        elif choice.isdigit():
            idx = int(choice)
            if 0 <= idx < total_jobs:
                print_chunks(jobs[idx], idx)
            else:
                print(f"❌ ID vượt quá giới hạn! Vui lòng nhập từ 0 đến {total_jobs - 1}.")
                
        else:
            print("❌ Lựa chọn không hợp lệ, vui lòng thử lại.")

if __name__ == "__main__":
    # Đường dẫn trỏ đến file dữ liệu thực tế của bạn
    json_path = "data/filtered_it_jobs.json" 
    run_interactive_tester(json_path)