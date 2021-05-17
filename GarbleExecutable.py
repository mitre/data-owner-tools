import garble
import wx
from multiprocessing import freeze_support
import sys
import os
from pathlib import Path

#pyinstaller GarbleExecutable.py  --onefile -w --add-data ./venv/Lib/site-packages/clkhash/data;clkhash/data --add-data ./venv/Lib/site-packages/clkhash/schemas;clkhash/schemas --add-data ./example-schema;example-schema --add-data ./secret-file/secret-file.txt;secret-file


if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    os.chdir(sys._MEIPASS)


class GarbleWindow(wx.Frame):
    def __init__(self, *args, **kwargs):
        super(GarbleWindow, self).__init__(*args, **kwargs)
        self.pii_path = ""
        self.output_dir = ""
        self.schema_dir = "example-schema"
        self.salt_path = "secret-file/secret-file.txt"
        self.pii_path_text = None
        self.output_dir_text = None
        self.garble_text = None
        self.InitUI()

    def InitUI(self):

        panel = wx.Panel(self)

        hbox = wx.BoxSizer()
        sizer = wx.GridSizer(5, 2, 2, 300)

        open_csv_btn = wx.Button(panel, label='Open CSV File')
        open_output_btn = wx.Button(panel, label='Open Output Directory')
        garble_btn = wx.Button(panel, label='Garble')

        self.pii_path_text = wx.StaticText(panel, label="Select PII CSV file")
        self.output_dir_text = wx.StaticText(panel, label="Select output directory")
        self.garble_text = wx.StaticText(panel, label="")

        sizer.AddMany([self.pii_path_text, open_csv_btn, self.output_dir_text, open_output_btn, self.garble_text, garble_btn])

        hbox.Add(sizer, 0, wx.ALL, 15)
        panel.SetSizer(hbox)

        open_csv_btn.Bind(wx.EVT_BUTTON, self.OnOpenPII)
        open_output_btn.Bind(wx.EVT_BUTTON, self.OnOpenOutput)
        garble_btn.Bind(wx.EVT_BUTTON, self.OnGarble)

        self.SetSize((850, 200))
        self.SetTitle('Messages')
        self.Centre()

    def OnOpenPII(self, event):
        with wx.FileDialog(self, "Open csv file", wildcard="CSV files (*.csv)|*.csv",
                           style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return  # the user changed their mind

            # Proceed loading the file chosen by the user
            self.pii_path = fileDialog.GetPath()
            self.pii_path_text.SetLabel(self.pii_path)


    def OnOpenOutput(self, event):
        with wx.DirDialog(self, "Choose Output Directory", style=wx.FD_OPEN | wx.DD_DIR_MUST_EXIST) as dirDialog:
            if dirDialog.ShowModal() == wx.ID_CANCEL:
                return  # the user changed their mind

            # Proceed loading the file chosen by the user
            self.output_dir = dirDialog.GetPath()
            self.output_dir_text.SetLabel(self.output_dir)

    def OnGarble(self, event):
        self.garble_text.SetLabel("Processing PII Data...")
        self.Update()
        self.garble_text.SetLabel(garble.garble_data(Path(self.pii_path), Path(self.schema_dir), Path(self.salt_path), Path(self.output_dir)))

def main():
    app = wx.App()
    ex = GarbleWindow(None)
    ex.Show()
    app.MainLoop()


if __name__ == '__main__':
    freeze_support()
    main()

