import wx
import linkid_to_patid
from multiprocessing import freeze_support
import sys
import os
from types import SimpleNamespace
#pyinstaller Link-IDs-Executable.py --onefile -w

if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    os.chdir(sys._MEIPASS)


class LinkIDsWindow(wx.Frame):
    def __init__(self, *args, **kwargs):
        super(LinkIDsWindow, self).__init__(*args, **kwargs)
        self.pii_path = ""
        self.link_file_path = ""
        self.output_dir = ""
        self.pii_path_text = None
        self.link_ids_path_text = None
        self.output_dir_text = None
        self.match_text = None
        self.InitUI()

    def InitUI(self):

        panel = wx.Panel(self)

        hbox = wx.BoxSizer()
        sizer = wx.GridSizer(4, 2, 2, 300)

        open_csv_btn = wx.Button(panel, label='Open CSV File')
        open_link_id_btn = wx.Button(panel, label='Open Link-Id file')
        open_output_btn = wx.Button(panel, label='Select Output')
        match_btn = wx.Button(panel, label='Match')

        self.pii_path_text = wx.StaticText(panel, label="Select PII CSV file (used to generate gabled data)")
        self.link_ids_path_text = wx.StaticText(panel, label="Select Link-ids file (provided by Data Integrator)")
        self.output_dir_text = wx.StaticText(panel, label="Select output directory")
        self.match_text = wx.StaticText(panel, label="Match Link-ids to Patient IDs")

        sizer.AddMany([self.pii_path_text, open_csv_btn, self.link_ids_path_text, open_link_id_btn, self.output_dir_text, open_output_btn, self.match_text, match_btn])

        hbox.Add(sizer, 0, wx.ALL, 15)
        panel.SetSizer(hbox)

        open_csv_btn.Bind(wx.EVT_BUTTON, self.OnOpenPII)
        open_link_id_btn.Bind(wx.EVT_BUTTON, self.OnOpenLinkIds)
        open_output_btn.Bind(wx.EVT_BUTTON, self.OnOpenOutput)
        match_btn.Bind(wx.EVT_BUTTON, self.OnMatch)

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

    def OnOpenLinkIds(self, event):
        with wx.FileDialog(self, "Open csv file", wildcard="CSV files (*.csv)|*.csv",
                           style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return  # the user changed their mind

            # Proceed loading the file chosen by the user
            self.link_file_path = fileDialog.GetPath()
            self.link_ids_path_text.SetLabel(self.link_file_path)


    def OnOpenOutput(self, event):
        with wx.DirDialog(self, "Choose Output Directory", style=wx.FD_OPEN | wx.DD_DIR_MUST_EXIST) as dirDialog:
            if dirDialog.ShowModal() == wx.ID_CANCEL:
                return  # the user changed their mind

            # Proceed loading the file chosen by the user
            self.output_dir = dirDialog.GetPath()
            self.output_dir_text.SetLabel(self.output_dir)

    def OnMatch(self, event):
        self.match_text.SetLabel("Processing PII Data...")
        self.Update()
        args = {"sourcefile": self.pii_path, "linksfile": self.link_file_path, "outputdir": self.output_dir,"hhsource": "", "hhlinks": ""}
        args = SimpleNamespace(**args)
        linkid_to_patid.translate_linkids(args)
        self.match_text.SetLabel("Wrote File to " + self.output_dir)

def main():
    app = wx.App()
    ex = LinkIDsWindow(None)
    ex.Show()
    app.MainLoop()


if __name__ == '__main__':
    freeze_support()
    main()