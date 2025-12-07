import os
import sys


def toggle_extension():
    current_dir = os.getcwd()

    print(f"📂 현재 위치: {current_dir}")
    print("-" * 30)
    print("1. [.ms]  -> [.txt] 로 변환")
    print("2. [.txt] -> [.ms]  로 변환")
    print("-" * 30)

    choice = input("선택할 번호를 입력하세요 (1 또는 2): ").strip()

    if choice == "1":
        src_ext = ".ms"
        dst_ext = ".txt"
    elif choice == "2":
        src_ext = ".txt"
        dst_ext = ".ms"
    else:
        print("❌ 잘못된 입력입니다. 프로그램을 종료합니다.")
        return

    count = 0
    for filename in os.listdir(current_dir):
        # 파일이 맞는지, 그리고 해당 확장자로 끝나는지 확인
        if os.path.isfile(filename) and filename.lower().endswith(src_ext):
            base_name = os.path.splitext(filename)[0]
            new_filename = base_name + dst_ext

            # 이미 변환된 파일 이름이 있는지 확인 (덮어쓰기 방지)
            if os.path.exists(new_filename):
                print(f"⚠️ 건너뜀 (이미 존재함): {new_filename}")
                continue

            try:
                os.rename(filename, new_filename)
                print(f"✅ 변환: {filename} -> {new_filename}")
                count += 1
            except Exception as e:
                print(f"❌ 오류 발생 ({filename}): {e}")

    if count == 0:
        print(f"\n⚠️ 변환할 '{src_ext}' 파일이 없습니다.")
    else:
        print(f"\n🎉 총 {count}개의 파일이 '{dst_ext}'로 변환되었습니다.")

    input("엔터키를 누르면 종료합니다...")


if __name__ == "__main__":
    toggle_extension()