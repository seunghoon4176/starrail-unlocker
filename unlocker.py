
import customtkinter as ctk
from tkinter import messagebox
import os
import sys
import requests
import tempfile
import subprocess
import webbrowser

CURRENT_VERSION = "1.0.0"
GITHUB_API = "https://api.github.com/repos/seunghoon4176/starrail-gacha-tracker/releases/latest"

# PyInstaller 리소스 경로 처리
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class StarRailUnlockerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("120fps 언락커")
        self.root.geometry("250x100")
        self.root.resizable(False, False)  # 창 크기 고정
        ctk.set_appearance_mode("system")
        ctk.set_default_color_theme("blue")

        # 아이콘 적용 (여러 경로 시도)
        try:
            icon_paths = [
                resource_path("images/anaxa.ico"),
                resource_path("anaxa.ico"),
                "images/anaxa.ico",
                "anaxa.ico"
            ]
            for icon_path in icon_paths:
                if os.path.exists(icon_path):
                    self.root.iconbitmap(icon_path)
                    break
        except Exception:
            pass

        self.unlock_btn = ctk.CTkButton(self.root, text="120FPS 언락", command=self.unlock_120fps)
        self.unlock_btn.pack(pady=40)

        # 앱 시작 시 업데이트 체크
        self.check_update_on_startup()

    def unlock_120fps(self):
        """Star Rail FPS 제한을 120으로 언락 (레지스트리 수정)"""
        try:
            import winreg
            reg_path = r"Software\Cognosphere\Star Rail"
            value_name_prefix = "GraphicsSettings_Model_"
            # 하위 키에서 GraphicsSettings_Model_* 찾기
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path, 0, winreg.KEY_READ) as key:
                i = 0
                found_name = None
                while True:
                    try:
                        name, val, typ = winreg.EnumValue(key, i)
                        if name.startswith(value_name_prefix):
                            found_name = name
                            break
                        i += 1
                    except OSError:
                        break
            if not found_name:
                messagebox.showerror("120 FPS 언락 실패", "GraphicsSettings_Model_* 값을 찾을 수 없습니다.\n게임 내 그래픽 설정을 '커스텀'으로 변경 후 다시 시도하세요.")
                return
            # 값 읽기
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path, 0, winreg.KEY_READ | winreg.KEY_WRITE) as key:
                val, typ = winreg.QueryValueEx(key, found_name)
                if typ != winreg.REG_BINARY:
                    messagebox.showerror("120 FPS 언락 실패", "알 수 없는 레지스트리 값 형식입니다.")
                    return
                # 바이너리 → bytearray
                b = bytearray(val)
                # ASCII로 변환해서 "FPS":60 찾기
                s = b.decode("latin1")
                import re
                m = re.search(r'"FPS":(\d+)', s)
                if not m:
                    messagebox.showerror("120 FPS 언락 실패", '"FPS":60 값을 찾을 수 없습니다.')
                    return
                fps_val = m.group(1)
                if fps_val == "120":
                    messagebox.showinfo("120 FPS 언락", "이미 120 FPS로 설정되어 있습니다!")
                    return
                # 60 → 120 치환
                s_new = s.replace(f'"FPS":{fps_val}', '"FPS":120', 1)
                # 다시 바이너리로 변환
                b_new = s_new.encode("latin1")
                # 길이 맞추기 (PyInstaller 환경 호환)
                if len(b_new) < len(b):
                    b_new += b[len(b_new):]
                elif len(b_new) > len(b):
                    b_new = b_new[:len(b)]
                # 레지스트리 값 쓰기
                winreg.SetValueEx(key, found_name, 0, winreg.REG_BINARY, bytes(b_new))
            messagebox.showinfo("120 FPS 언락 완료", "성공적으로 120 FPS로 설정했습니다!\n게임을 재시작하세요.\n(설정 메뉴에는 30으로 보일 수 있으나 실제로는 120 FPS로 동작합니다.)")
        except Exception as e:
            messagebox.showerror("120 FPS 언락 실패", f"오류 발생: {e}")


    def check_update_on_startup(self):
        """GitHub 릴리즈에서 최신 버전 확인 및 자동 다운로드/실행 안내"""
        try:
            resp = requests.get(GITHUB_API, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                latest_ver = data.get("tag_name", "")
                body = data.get("body", "")
                if latest_ver and latest_ver != CURRENT_VERSION:
                    assets = data.get("assets", [])
                    exe_asset = None
                    for asset in assets:
                        if asset["name"].endswith(".exe"):
                            exe_asset = asset
                            break
                    if exe_asset:
                        url = exe_asset["browser_download_url"]
                        msg = f"새 버전이 있습니다: {latest_ver}\n\n지금 자동으로 다운로드할까요?"
                        if messagebox.askyesno("업데이트 알림", msg):
                            local_path = os.path.join(tempfile.gettempdir(), exe_asset["name"])
                            try:
                                with requests.get(url, stream=True, timeout=30) as r:
                                    r.raise_for_status()
                                    with open(local_path, "wb") as f:
                                        for chunk in r.iter_content(chunk_size=8192):
                                            f.write(chunk)
                                messagebox.showinfo("다운로드 완료", f"새 버전이 다운로드되었습니다.\n프로그램을 종료하고 새 버전을 실행합니다.")
                                self.show_update_notice_after_update(body, latest_ver)
                                subprocess.Popen([local_path])
                                self.root.destroy()
                            except Exception as e:
                                messagebox.showerror("업데이트 실패", f"다운로드 또는 실행 중 오류 발생:\n{e}")
                    else:
                        url = data.get("html_url", "https://github.com/seunghoon4176/starrail-gacha-tracker/releases")
                        msg = f"새 버전이 있습니다: {latest_ver}\n\n업데이트 페이지로 이동할까요?"
                        if messagebox.askyesno("업데이트 알림", msg):
                            webbrowser.open(url)
        except Exception as e:
            print(f"업데이트 확인 실패: {e}")

    def show_update_notice_after_update(self, body, latest_ver):
        """업데이트 후에만 공지(릴리즈 노트) 표시"""
        msg = f"업데이트 공지 (v{latest_ver})\n\n{body or '공지 없음'}"
        notice_win = ctk.CTkToplevel(self.root)
        notice_win.title("업데이트 공지")
        notice_win.geometry("520x420")
        try:
            icon_paths = [
                resource_path("images/anaxa.ico"),
                resource_path("anaxa.ico"),
                "images/anaxa.ico",
                "anaxa.ico"
            ]
            for icon_path in icon_paths:
                if os.path.exists(icon_path):
                    notice_win.iconbitmap(icon_path)
                    break
        except Exception:
            pass
        notice_text = ctk.CTkTextbox(notice_win)
        notice_text.pack(fill="both", expand=True, padx=20, pady=20)
        notice_text.insert("0.0", msg)
        notice_text.configure(state="disabled")




if __name__ == "__main__":
    root = ctk.CTk()
    app = StarRailUnlockerApp(root)
    root.mainloop()