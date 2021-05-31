import garble
import wx
from multiprocessing import freeze_support
import sys
import os
from pathlib import Path

# pyinstaller GarbleExecutable.py  --onefile -w --add-data ./venv/Lib/site-packages/clkhash/data;clkhash/data --add-data ./venv/Lib/site-packages/clkhash/schemas;clkhash/schemas --add-data ./example-schema;example-schema


if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    os.chdir(sys._MEIPASS)


class GarbleWindow(wx.Frame):
    def __init__(self, *args, **kwargs):
        super(GarbleWindow, self).__init__(*args, **kwargs)
        self.pii_path = ""
        self.schema_dir = "example-schema"
        self.salt_path = ""
        self.pii_path_text = None
        self.pii_path_btn = None
        self.salt_path_text = None
        self.salt_path_btn = None
        self.garble_text = None
        self.garble_btn = None
        self.InitUI()

    def InitUI(self):

        panel = wx.Panel(self)

        hbox = wx.BoxSizer()
        sizer = wx.FlexGridSizer(5, 2, 2, 250)


        self.pii_path_text = wx.StaticText(panel, label="Select PII CSV file:")
        self.pii_path_btn = wx.Button(panel, label='Open CSV File')
        self.pii_path_btn.Bind(wx.EVT_BUTTON, self.on_open_pii)





        self.salt_path_text = wx.StaticText(panel, label="Select Secret File:")
        self.salt_path_btn = wx.Button(panel, label='Open Secret File')
        self.salt_path_btn.Bind(wx.EVT_BUTTON, self.on_open_salt)

        self.garble_text = wx.StaticText(panel, label="")
        self.garble_btn = wx.Button(panel, label='Garble')
        self.garble_btn.Bind(wx.EVT_BUTTON, self.on_garble)

        sizer.AddMany(
            [self.pii_path_text, self.pii_path_btn, self.salt_path_text, self.salt_path_btn, self.garble_text, self.garble_btn])

        hbox.Add(sizer, 0, wx.ALL, 15)
        panel.SetSizer(hbox)





        self.SetSize((500, 150))
        self.SetTitle('Garble Tool')
        self.Centre()

    def on_open_pii(self, event):
        with wx.FileDialog(self, "Open csv file", wildcard="CSV files (*.csv)|*.csv",
                           style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return  # the user changed their mind

            # Proceed loading the file chosen by the user
            self.pii_path = fileDialog.GetPath()
            self.pii_path_text.SetLabel(self.pii_path)

    def on_open_salt(self, event):
        with wx.FileDialog(self, "Open Secret file", style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return  # the user changed their mind

            # Proceed loading the file chosen by the user
            self.salt_path = fileDialog.GetPath()
            self.salt_path_text.SetLabel(self.salt_path)

    def on_garble(self, event):

        with wx.FileDialog(self, "Save Zip file", wildcard="Zip files (*.zip)|*.zip",
                           style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return  # the user changed their mind

            # save the current contents in the file
            pathname = fileDialog.GetPath()
            self.garble_text.SetLabel("Processing PII Data...")
            self.Update()
            output_dir, file_name = os.path.split(pathname)
            self.garble_text.SetLabel(
                garble.garble_data(Path(self.pii_path), Path(self.schema_dir), Path(self.salt_path), Path(output_dir), file_name, rm_json=True))


def main():
    app = wx.App()
    ex = GarbleWindow(None)
    ex.Show()
    app.MainLoop()


if __name__ == '__main__':
    freeze_support()
    main()
