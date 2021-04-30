import wx
import linkidtopatid
from multiprocessing import freeze_support
import sys
import os

#pyinstaller Link-IDs-Executable.py --onefile -w

if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    os.chdir(sys._MEIPASS)


class CSVManager(wx.Frame):
    def __init__(self, *args, **kwargs):
        super(CSVManager, self).__init__(*args, **kwargs)
        self.PII_path = ""
        self.link_ids_path = ""
        self.output_dir = ""
        self.txt1 = None
        self.txt2 = None
        self.txt3 = None
        self.txt4 = None
        self.InitUI()

    def InitUI(self):

        panel = wx.Panel(self)

        hbox = wx.BoxSizer()
        sizer = wx.GridSizer(4, 2, 2, 300)

        btn1 = wx.Button(panel, label='Open CSV File')
        btn2 = wx.Button(panel, label='Open Link-Id file')
        btn3 = wx.Button(panel, label='Select Output')
        btn4 = wx.Button(panel, label='Match')

        self.txt1 = wx.StaticText(panel, label="Select PII CSV file (used to generate gabled data)")
        self.txt2 = wx.StaticText(panel, label="Select Link-ids file (provided by Data Integrator)")
        self.txt3 = wx.StaticText(panel, label="Select output directory")
        self.txt4 = wx.StaticText(panel, label="Match Link-ids to Patient IDs")

        sizer.AddMany([self.txt1, btn1, self.txt2, btn2, self.txt3, btn3, self.txt4, btn4])

        hbox.Add(sizer, 0, wx.ALL, 15)
        panel.SetSizer(hbox)

        btn1.Bind(wx.EVT_BUTTON, self.OnOpenPII)
        btn2.Bind(wx.EVT_BUTTON, self.OnOpenLinkIds)
        btn3.Bind(wx.EVT_BUTTON, self.OnOpenOutput)
        btn4.Bind(wx.EVT_BUTTON, self.OnMatch)

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

    def OnOpenLinkIds(self, event):
        with wx.FileDialog(self, "Open csv file", wildcard="CSV files (*.csv)|*.csv",
                           style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return  # the user changed their mind

            # Proceed loading the file chosen by the user
            self.link_ids_path = fileDialog.GetPath()
            self.txt2.SetLabel(self.link_ids_path)


    def OnOpenOutput(self, event):
        with wx.DirDialog(self, "Choose Output Directory", style=wx.FD_OPEN | wx.DD_DIR_MUST_EXIST) as dirDialog:
            if dirDialog.ShowModal() == wx.ID_CANCEL:
                return  # the user changed their mind

            # Proceed loading the file chosen by the user
            self.output_dir = dirDialog.GetPath()
            self.txt3.SetLabel(self.output_dir)

    def OnMatch(self, event):
        self.txt4.SetLabel("Processing PII Data...")
        self.Update()
        self.txt4.SetLabel(linkidtopatid.linkids_to_patids(self.PII_path, self.link_ids_path, self.output_dir))

def main():
    app = wx.App()
    ex = CSVManager(None)
    ex.Show()
    app.MainLoop()


if __name__ == '__main__':
    freeze_support()
    main()