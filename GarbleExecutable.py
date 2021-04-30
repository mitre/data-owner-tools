import garble
import wx
from multiprocessing import freeze_support
import sys
import os
from pathlib import Path

#pyinstaller GarbleExecutable.py  --onefile -w --add-data ./venv/Lib/site-packages/clkhash/data;clkhash/data --add-data ./venv/Lib/site-packages/clkhash/schemas;clkhash/schemas --add-data ./example-schema;example-schema --add-data ./secret-file/secret-file.txt;secret-file


if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    os.chdir(sys._MEIPASS)


class CSVManager(wx.Frame):
    def __init__(self, *args, **kwargs):
        super(CSVManager, self).__init__(*args, **kwargs)
        self.PII_path = ""
        self.output_dir = ""
        self.schema_dir = "example-schema"
        self.salt_path = "secret-file/secret-file.txt"
        self.txt1 = None
        self.txt2 = None
        self.txt3 = None
        self.txt2 = None
        self.InitUI()

    def InitUI(self):

        panel = wx.Panel(self)

        hbox = wx.BoxSizer()
        sizer = wx.GridSizer(5, 2, 2, 300)

        btn1 = wx.Button(panel, label='Open CSV File')
        btn2 = wx.Button(panel, label='Open Output Directory')
        btn3 = wx.Button(panel, label='Garble')

        self.txt1 = wx.StaticText(panel, label="Select PII CSV file")
        self.txt2 = wx.StaticText(panel, label="Select output directory")
        self.txt3 = wx.StaticText(panel, label="")

        sizer.AddMany([self.txt1, btn1, self.txt2, btn2, self.txt3, btn3])

        hbox.Add(sizer, 0, wx.ALL, 15)
        panel.SetSizer(hbox)

        btn1.Bind(wx.EVT_BUTTON, self.OnOpenPII)
        btn2.Bind(wx.EVT_BUTTON, self.OnOpenOutput)
        btn3.Bind(wx.EVT_BUTTON, self.OnGarble)

        self.SetSize((850, 200))
        self.SetTitle('Messages')
        self.Centre()

    def OnOpenPII(self, event):
        with wx.FileDialog(self, "Open csv file", wildcard="CSV files (*.csv)|*.csv",
                           style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return  # the user changed their mind

            # Proceed loading the file chosen by the user
            self.PII_path = fileDialog.GetPath()
            self.txt1.SetLabel(self.PII_path)


    def OnOpenOutput(self, event):
        with wx.DirDialog(self, "Choose Output Directory", style=wx.FD_OPEN | wx.DD_DIR_MUST_EXIST) as dirDialog:
            if dirDialog.ShowModal() == wx.ID_CANCEL:
                return  # the user changed their mind

            # Proceed loading the file chosen by the user
            self.output_dir = dirDialog.GetPath()
            self.txt2.SetLabel(self.output_dir)

    def OnGarble(self, event):
        self.txt3.SetLabel("Processing PII Data...")
        self.Update()
        self.txt3.SetLabel(garble.garble_data(Path(self.PII_path), Path(self.schema_dir), Path(self.salt_path), Path(self.output_dir)))

def main():
    app = wx.App()
    ex = CSVManager(None)
    ex.Show()
    app.MainLoop()


if __name__ == '__main__':
    freeze_support()
    main()

