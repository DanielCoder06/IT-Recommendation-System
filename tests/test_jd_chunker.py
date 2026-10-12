from src.processing.jd_chunker import chunk_jd_text

# Sử dụng JD thực tế của SAEKI để test
raw_jd_text = """
SAEKI - Manufacturing at software speed
Europe's defense industrial base cannot respond at the speed modern conflict requires. Legacy suppliers operate on month-long timelines.
The Role
As a Computational Geometry Engineer, you own the geometry core of our Manufacturing Intelligence stack - the engine that takes an arbitrary customer CAD model and reasons about how to build it.
You own the code that runs in the factory.
What We're Looking For
5+ years building geometry-heavy software in production - CAD/CAM, geometry kernels.
B-rep and Mesh Depth. You think natively in topology and NURBS. Feature recognition.
Kernel Fluency. Hands-on with a geometry kernel - Parasolid, OpenCASCADE, ACIS.
What we're not looking for
Researchers who want to publish and hand off. You ship.
CAD users. This is a role for people who build the tools, not drive them.
What we offer
Mission: Rebuild the industrial sovereignty of the West. Your work directly enables production.
Total Ownership: High-stakes autonomy in your domain.
Compensation: Competitive salary + meaningful equity.
Location: Zurich HQ, with occasional time at Factory ONE in Munich.
"""

def test_modular_chunker():
    print("Đang chạy mô hình Embedding và Chunking JD...")
    
    # Gọi hàm chunk_jd_text từ cấu trúc mới
    chunks = chunk_jd_text(raw_jd_text, max_words=120)
    
    print(f"\n=> TỔNG SỐ CHUNKS TẠO RA: {len(chunks)}")
    print("=" * 100)
    print(f"{'CATEGORY':<15} | {'CHUNK CONTENT'}")
    print("-" * 100)
    
    for i, chunk in enumerate(chunks):
        # Trích xuất dữ liệu từ format mới (dict)
        category = chunk.get("category", "UNKNOWN")
        text = chunk.get("text", "")
        
        # Rút gọn text nếu quá dài để dễ nhìn trên terminal
        display_text = text if len(text) < 80 else text[:77] + "..."
        
        print(f"[{category:<13}] | {display_text}")

if __name__ == "__main__":
    test_modular_chunker()