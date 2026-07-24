
with open(r"E:\Tate\WorkSpace\AI_Model_Balance\ai_model_monitor.py", "r", encoding="utf-8") as f:
    c = f.read()

# Replace _create_tray stub
old_tray = "    def _create_tray(self):
        pass  # tray via icon file"
new_tray = "    def _create_tray(self):
        pass  # tray handled by hover loop"
c = c.replace(old_tray, new_tray)

# Ensure quit_app has os._exit
c = c.replace("        self.destroy()", "        self.destroy()
        os._exit(0)")

# Remove duplicate os._exit
c = c.replace("os._exit(0)
        os._exit(0)", "os._exit(0)")

with open(r"E:\Tate\WorkSpace\AI_Model_Balance\ai_model_monitor.py", "w", encoding="utf-8") as f:
    f.write(c)
print("done")
