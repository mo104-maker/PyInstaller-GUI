import wx
import subprocess
import os
import threading
import re

try:
    from win10toast import ToastNotifier
    HAS_TOAST = True
except ImportError:
    HAS_TOAST = False

class MainWindow(wx.Frame):
    def __init__(self):
        super().__init__(None, title="PyInstaller GUI", size=(700, 600))
        
        self.panel = wx.Panel(self)
        self.current_directory = os.getcwd()
        self.progress_pattern = re.compile(r'(\d+)%')
        self.dark_mode = False
        self.current_process = None

        # Initialize UI
        self.create_widgets()
        self.apply_theme()
        self.Layout()
        self.Centre()

    def create_widgets(self):
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Theme Toggle
        self.theme_btn = wx.Button(self.panel, label="🌙 Dark Mode")
        self.theme_btn.Bind(wx.EVT_BUTTON, self.toggle_theme)
        main_sizer.Add(self.theme_btn, 0, wx.ALIGN_RIGHT|wx.RIGHT|wx.TOP, 10)

        # File Selection
        file_sizer = self.create_file_picker()
        main_sizer.Add(wx.StaticText(self.panel, label="Script File:"), 0, wx.TOP|wx.LEFT, 10)
        main_sizer.Add(file_sizer, 0, wx.EXPAND|wx.ALL, 5)

        # Icon Selection
        icon_sizer = self.create_icon_picker()
        main_sizer.Add(wx.StaticText(self.panel, label="Icon File:"), 0, wx.TOP|wx.LEFT, 10)
        main_sizer.Add(icon_sizer, 0, wx.EXPAND|wx.ALL, 5)

        # Output Directory
        output_sizer = self.create_output_picker()
        main_sizer.Add(wx.StaticText(self.panel, label="Output Directory:"), 0, wx.TOP|wx.LEFT, 10)
        main_sizer.Add(output_sizer, 0, wx.EXPAND|wx.ALL, 5)

        # Advanced Options
        advanced_sizer = self.create_advanced_options()
        main_sizer.Add(advanced_sizer, 0, wx.EXPAND|wx.ALL, 5)

        # Progress and Logs
        progress_logs_sizer = self.create_progress_logs()
        main_sizer.Add(progress_logs_sizer, 1, wx.EXPAND|wx.ALL, 5)

        # Action Buttons
        button_sizer = self.create_action_buttons()
        main_sizer.Add(button_sizer, 0, wx.ALIGN_CENTER|wx.ALL, 10)

        self.panel.SetSizer(main_sizer)

    def create_file_picker(self):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.file_txt = wx.TextCtrl(self.panel, style=wx.TE_READONLY)
        btn = wx.Button(self.panel, label="Select Script")
        btn.Bind(wx.EVT_BUTTON, self.on_browse_file)
        sizer.Add(self.file_txt, 1, wx.EXPAND|wx.RIGHT, 5)
        sizer.Add(btn, 0, wx.EXPAND)
        return sizer

    def create_icon_picker(self):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.icon_txt = wx.TextCtrl(self.panel, style=wx.TE_READONLY)
        btn = wx.Button(self.panel, label="Select Icon")
        btn.Bind(wx.EVT_BUTTON, self.on_browse_icon)
        sizer.Add(self.icon_txt, 1, wx.EXPAND|wx.RIGHT, 5)
        sizer.Add(btn, 0, wx.EXPAND)
        return sizer

    def create_output_picker(self):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.output_txt = wx.TextCtrl(self.panel, style=wx.TE_READONLY)
        btn = wx.Button(self.panel, label="Output Folder")
        btn.Bind(wx.EVT_BUTTON, self.on_browse_output)
        sizer.Add(self.output_txt, 1, wx.EXPAND|wx.RIGHT, 5)
        sizer.Add(btn, 0, wx.EXPAND)
        return sizer

    def create_advanced_options(self):
        sizer = wx.StaticBoxSizer(wx.VERTICAL, self.panel, "Advanced Options")
        self.console_cb = wx.CheckBox(self.panel, label="Show Console")
        self.console_cb.SetValue(True)
        self.onefile = wx.CheckBox(self.panel, label="Single File")
        self.clean_cb = wx.CheckBox(self.panel, label="Clean Build")
        self.add_data_txt = wx.TextCtrl(self.panel)
        self.add_data_txt.SetHint("Add data: format=source;destination")
        
        sizer.Add(self.console_cb, 0, wx.ALL, 2)
        sizer.Add(self.onefile, 0, wx.ALL, 2)
        sizer.Add(self.clean_cb, 0, wx.ALL, 2)
        sizer.Add(self.add_data_txt, 0, wx.EXPAND|wx.ALL, 2)
        return sizer

    def create_progress_logs(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.progress = wx.Gauge(self.panel, range=100)
        
        log_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.log_txt = wx.TextCtrl(self.panel, style=wx.TE_MULTILINE|wx.TE_READONLY)
        copy_btn = wx.Button(self.panel, label="📋 Copy Logs")
        copy_btn.Bind(wx.EVT_BUTTON, self.copy_logs)
        
        log_sizer.Add(self.log_txt, 1, wx.EXPAND)
        log_sizer.Add(copy_btn, 0, wx.LEFT, 5)
        
        sizer.Add(self.progress, 0, wx.EXPAND|wx.ALL, 5)
        sizer.Add(log_sizer, 1, wx.EXPAND)
        return sizer

    def create_action_buttons(self):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        build_btn = wx.Button(self.panel, label="🚀 Build Executable")
        build_btn.Bind(wx.EVT_BUTTON, self.build_exe)
        cancel_btn = wx.Button(self.panel, label="⛔ Cancel Build")
        cancel_btn.Bind(wx.EVT_BUTTON, self.cancel_build)
        
        sizer.Add(build_btn, 0, wx.RIGHT, 10)
        sizer.Add(cancel_btn, 0, wx.LEFT, 10)
        return sizer

    # Event Handlers
    def on_browse_file(self, event):
        with wx.FileDialog(self, "Select Python script", wildcard="Python files (*.py)|*.py") as fd:
            if fd.ShowModal() == wx.ID_CANCEL: return
            self.file_txt.SetValue(fd.GetPath())

    def on_browse_icon(self, event):
        with wx.FileDialog(self, "Select Icon file", wildcard="Icon files (*.ico)|*.ico") as fd:
            if fd.ShowModal() == wx.ID_CANCEL: return
            self.icon_txt.SetValue(fd.GetPath())

    def on_browse_output(self, event):
        with wx.DirDialog(self, "Select output directory") as dd:
            if dd.ShowModal() == wx.ID_CANCEL: return
            self.output_txt.SetValue(dd.GetPath())

    def build_exe(self, event):
        try:
            subprocess.check_output(['pyinstaller', '--version'])
        except (FileNotFoundError, subprocess.CalledProcessError):
            wx.MessageBox("PyInstaller not found! Please install it first.", "Error", wx.OK|wx.ICON_ERROR)
            return

        script_path = self.file_txt.GetValue()
        if not script_path or not os.path.exists(script_path):
            wx.MessageBox("Invalid script path!", "Error", wx.OK|wx.ICON_ERROR)
            return

        cmd = ['pyinstaller']
        if self.onefile.IsChecked(): cmd.append('--onefile')
        if not self.console_cb.IsChecked(): cmd.append('--noconsole')
        if self.icon_txt.GetValue(): cmd.extend(['--icon', self.icon_txt.GetValue()])
        if self.output_txt.GetValue(): cmd.extend(['--distpath', self.output_txt.GetValue()])
        if self.clean_cb.IsChecked(): cmd.append('--clean')
        if self.add_data_txt.GetValue(): cmd.extend(['--add-data', self.add_data_txt.GetValue()])
        cmd.append(script_path)

        preview_dlg = wx.MessageDialog(self, ' '.join(cmd), 'Command Preview', wx.OK|wx.CANCEL)
        if preview_dlg.ShowModal() == wx.ID_CANCEL: return

        self.log_txt.Clear()
        self.progress.SetValue(0)
        self.log_txt.AppendText(f"Starting build...\nCommand: {' '.join(cmd)}\n")
        
        threading.Thread(target=self.run_pyinstaller, args=(cmd,), daemon=True).start()

    def run_pyinstaller(self, cmd):
        try:
            self.current_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )

            while True:
                output = self.current_process.stdout.readline()
                if output == '' and self.current_process.poll() is not None:
                    break
                if output:
                    self.update_progress(output.strip())
                    
            return_code = self.current_process.poll()
            if return_code == 0:
                self.update_progress("\n✅ Build completed successfully!")
                self.show_notification("Build Success", "Executable created successfully!")
            else:
                self.update_progress(f"\n❌ Build failed with code {return_code}")
                self.show_notification("Build Failed", f"Error code: {return_code}")

        except Exception as e:
            self.update_progress(f"⛔ Critical Error: {str(e)}")
            self.show_notification("Build Error", str(e))
        finally:
            self.current_process = None

    def cancel_build(self, event):
        if self.current_process:
            self.current_process.terminate()
            self.log_txt.AppendText("\n⚠️ Process cancelled by user!")
            self.current_process = None

    def copy_logs(self, event):
        data = wx.TextDataObject()
        data.SetText(self.log_txt.GetValue())
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(data)
            wx.TheClipboard.Close()
            self.log_txt.AppendText("\n📋 Logs copied to clipboard!")

    def toggle_theme(self, event):
        self.dark_mode = not self.dark_mode
        self.apply_theme()
        self.theme_btn.SetLabel("🌞 Light Mode" if self.dark_mode else "🌙 Dark Mode")

    def apply_theme(self):
        bg_color = wx.Colour(30, 30, 30) if self.dark_mode else wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW)
        text_color = wx.WHITE if self.dark_mode else wx.BLACK
        
        self.panel.SetBackgroundColour(bg_color)
        for child in self.panel.GetChildren():
            if isinstance(child, (wx.TextCtrl, wx.StaticText, wx.CheckBox)):
                child.SetForegroundColour(text_color)
                child.SetBackgroundColour(bg_color)
        self.Refresh()

    def show_notification(self, title, message):
        if HAS_TOAST:
            ToastNotifier().show_toast(title, message, duration=5)
        else:
            wx.MessageBox(message, title, wx.OK|wx.ICON_INFORMATION)

    def update_progress(self, message):
        wx.CallAfter(self._update_ui, message)

    def _update_ui(self, message):
        self.log_txt.AppendText(message + "\n")
        if match := self.progress_pattern.search(message):
            self.progress.SetValue(int(match.group(1)))
        self.log_txt.ShowPosition(self.log_txt.GetLastPosition())

if __name__ == "__main__":
    app = wx.App()
    frame = MainWindow()
    frame.Show()
    app.MainLoop()