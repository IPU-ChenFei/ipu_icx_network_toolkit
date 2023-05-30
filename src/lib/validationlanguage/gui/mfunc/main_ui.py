#!/usr/bin/env python
# -*- coding: utf-8 -*-
import wx.tools.wxget

from src.lib.validationlanguage.gui.layout.main_frame import *
from src.lib.validationlanguage.gui.mfunc.vlstep import VlSteps
from src.lib.validationlanguage.gui.mfunc.monitor import VlMonitor
from src.lib.validationlanguage.gui.mfunc.vltoolmenu import VlToolMenu
from src.lib.validationlanguage.src_translator.parser_table import MappingTableParser
from src.lib.validationlanguage.src_translator.trans_h2l import get_tcdb_file_path
from src.lib.validationlanguage.src_translator.trans_utils import get_pvl_mapping_file_path
from dtaf_core.lib.tklib.auto_api import *
from dtaf_core.lib.tklib.steps_lib.valtools.tools import _cfg_file as get_tools_ini

import webbrowser

class MainFrame(mainfrm):
    CUSTOM_ID = 10000
    def __init__(self, parent, _globals, _locals):
        super().__init__(parent)
        self.itp_cmd_window = None
        self.host_cmd_window = None
        self.set_feature_window = None
        self.tcd_block_window = None
        self.wait_window = None
        self.about_windows = None
        self.tool_download_window = None
        self.tool_upload_window = None
        self._boot_to_menuitems = [self.m_pop_boot_linux, self.m_pop_boot_win, self.m_pop_boot_vm, self.m_pop_boot_uefi]
        self._reset_menuitems = [self.m_pop_reset_os, self.m_pop_reset_uefi]
        self._ac_menuitems = [self.m_pop_ac_on, self.m_pop_ac_off]
        self._dc_menuitems = [self.m_pop_dc_on, self.m_pop_dc_off]
        self._reset2_menuitems = [self.m_pop_reset_any, self.m_pop_reset_cold, self.m_pop_reset_warm]
        self._waitfor_menuitems = [self.m_pop_waitfor_os, self.m_pop_waitfor_uefishell, self.m_pop_waitfor_s0, self.m_pop_waitfor_s5]
        self._checkenvironmnt_menuitems = [self.m_pop_checkenvironment_os, self.m_pop_checkenvironment_uefishell]
        self._checkpowerstate_menuitems = [self.m_pop_checkpowerstate_s0, self.m_pop_checkpowerstate_s5, self.m_pop_checkpowerstate_g3]
        self._right_bios = [self.m_right_bios_start, self.m_right_bios_stop, self.m_right_click_copy, self.m_right_click_paste, self.m_right_click_cut,
                            self.m_right_click_clear]
        self._right_dryrun = [self.m_right_click_copy, self.m_right_click_paste, self.m_right_click_cut, self.m_right_click_clear]
        self._right_steps = [self.m_right_steps_import, self.m_right_steps_export, self.m_right_steps_execute, self.m_right_click_copy,
                             self.m_right_click_paste, self.m_right_click_cut, self.m_right_click_clear, ]
        self.steps = VlSteps(self.m_textCtrl3, self.m_textCtrl2, self.m_textCtrl1, _globals, _locals)
        self.monitor = VlMonitor()
        self.m_choice5.Select(-1)
        self.toolmenu = VlToolMenu()
        self.read_domain_tools()

    def read_domain_tools(self):
        tools = self.toolmenu.get_all_tools()
        for i in tools:
            toolitem = wx.MenuItem( self.m_menu3, self.CUSTOM_ID, f"{i}", wx.EmptyString, wx.ITEM_NORMAL )
            self.m_menu3.Append(toolitem)
            self.Bind( wx.EVT_MENU, self.click_tool_menuitem, id = toolitem.GetId() )
            self.CUSTOM_ID += 1

    def click_right_bioslog(self, event):
        mousept = event.Position + event.EventObject.Position + event.EventObject.Parent.Position + event.EventObject.Parent.Parent.Position
        for mit in self.m_popmenu.GetMenuItems():
            self.m_popmenu.Remove(mit)
        for mit in self._right_bios:
            self.m_popmenu.Append(mit)
        self.PopupMenu(self.m_popmenu, mousept)

    def on_bios_start( self, event ):
        self.steps.toggle_bios_log(True)
        return super().on_bios_start(event)

    def on_bios_stop( self, event ):
        self.steps.toggle_bios_log(False)
        return super().on_bios_stop(event)

    def on_copy(self, event):
        text = self.FindFocus()
        if text is not None:
            text.Copy()
        return super().on_copy(event)

    def on_paste(self, event):
        text = self.FindFocus()
        if text is not None:
            text.Paste()
        return super().on_paste(event)

    def on_cut(self, event):
        text = self.FindFocus()
        if text is not None:
            text.Cut()
        return super().on_cut(event)

    def on_clear( self, event ):
        text = self.FindFocus()
        if text is not None:
            text.Clear()
        return super().on_clear(event)

    def on_steps_import( self, event ):
        defaultpath = os.path.abspath(
            os.path.join(os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))),
                "lib", "toolkit", "validationlanguage", "TcdBlocks"))
        dlg = wx.FileDialog(self, "Import File:", f'{defaultpath}', "", "TCD Block (*.tcdb)|*.tcdb|ALL (*.*)|*.*", wx.FD_OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            i = dlg.GetFilterIndex()
            if i == 0:  # Text format
                try:
                    f = open(dlg.GetPath(), "r")
                    log = f.read()
                    f.close()
                    self.m_textCtrl3.SetValue(log)
                except:
                    print("Import failed")
        return super().on_steps_import(event)

    def on_steps_export( self, event ):
        defaultpath = os.path.abspath(
            os.path.join(os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))),
                "lib", "toolkit", "validationlanguage", "TcdBlocks"))
        dlg = wx.FileDialog(self, "Export File:", f"{defaultpath}", "", "TCD Block (*.tcdb)|*.tcbd|ALL (*.*)|*.*", wx.FD_SAVE)
        if dlg.ShowModal() == wx.ID_OK:
            i = dlg.GetFilterIndex()
            if i == 0:  # Text format
                try:
                    f = open(dlg.GetPath(), "w")
                    log = self.m_textCtrl3.GetValue()
                    f.write(log)
                    f.close()
                except:
                    print("Export failed")
        return super().on_steps_export(event)

    def on_steps_execute(self, event):
        for line in self.m_textCtrl3.GetValue().split('\n'):
            step = line.strip()
            if len(step) > 0 and not step.startswith('#'):
                self.steps.steps_queue.append(step)
        return super().on_steps_execute(event)

    def click_right_dryrunlog( self, event ):
        for mit in self.m_popmenu.GetMenuItems():
            self.m_popmenu.Remove(mit)
        for mit in self._right_dryrun:
            self.m_popmenu.Append(mit)
        mousept = event.Position + event.EventObject.Position + event.EventObject.Parent.Position
        self.PopupMenu(self.m_popmenu, mousept)

    def click_right_stepslog( self, event ):
        for mit in self.m_popmenu.GetMenuItems():
            self.m_popmenu.Remove(mit)
        for mit in self._right_steps:
            self.m_popmenu.Append(mit)
        mousept = event.Position + event.EventObject.Position + event.EventObject.Parent.Position + event.EventObject.Parent.Parent.Position
        self.PopupMenu(self.m_popmenu, mousept)

    def onclose(self, event):
        self.steps.stop()
        self.monitor.stop()
        return super().onclose(event)

    def on_setting_menu( self, event ):
        if event.Id == self.m_setting_sut.GetId():
            os.system(f'notepad {DEFAULT_SUT_CONFIG_FILE}')
        elif event.Id == self.m_setting_feature.GetId():
            pvl = get_pvl_mapping_file_path()
            os.system(pvl)
        elif event.Id == self.m_setting_debug.GetId():
            os.system(f'notepad {DEBUG_INI}')
        elif event.Id == self.m_setting_tool.GetId():
            path = get_tools_ini()
            os.system(f'notepad {path}')
        elif event.Id == self.m_setting_dtafconfig.GetId():
            path = get_dtaf_xml_path(DEFAULT_SUT_CONFIG_FILE)
            os.system(f'notepad {path}')

    def hls_wiki( self, event ):
        webbrowser.open('https://wiki.ith.intel.com/display/testing/Tools')

    def toolkit_wiki( self, event ):
        webbrowser.open('https://wiki.ith.intel.com/display/testing/Automation+Validation+Toolkit+Document')

    # Click Help -> about Show Window
    def about( self, event ):
        if self.about_windows is None:
            self.about_windows = AboutWindow(self)
        self.about_windows.ShowModal()
        event.Skip()

    def _prepare_popmenu(self, rootname):
        for mit in self.m_popmenu.GetMenuItems():
            self.m_popmenu.Remove(mit)
        if rootname == 'Boot To':
            for mit in self._boot_to_menuitems:
                self.m_popmenu.Append(mit)
        elif rootname == 'Reset To':
            for mit in self._reset_menuitems:
                self.m_popmenu.Append(mit)
        elif rootname == 'AC':
            for mit in self._ac_menuitems:
                self.m_popmenu.Append(mit)
        elif rootname == 'DC':
            for mit in self._dc_menuitems:
                self.m_popmenu.Append(mit)
        elif rootname == 'Reset':
            for mit in self._reset2_menuitems:
                self.m_popmenu.Append(mit)
        elif rootname == 'Wait For':
            for mit in self._waitfor_menuitems:
                self.m_popmenu.Append(mit)
        elif rootname == 'Check Environment':
            for mit in self._checkenvironmnt_menuitems:
                self.m_popmenu.Append(mit)
        elif rootname == 'Check Power State':
            for mit in self._checkpowerstate_menuitems:
                self.m_popmenu.Append(mit)

    def on_variable_select(self, event):
        self.m_textCtrl12.WriteText(' {' + event.EventObject.StringSelection + '} ')
        event.EventObject.Select(-1)
        return super().on_variable_select(event)

    def execute_add_step( self, event ):
        timeout = int(self.m_textCtrl11.GetValue()) if self.m_checkBox1.IsChecked() else None
        no_check = not self.m_checkBox2.IsChecked()
        cmd = self.m_textCtrl12.GetValue()
        self.steps.execute_commmand(cmd, timeout, no_check)

        if self.m_checkBox1.IsChecked():
            self.m_checkBox1.SetValue(0)
            self.m_textCtrl11.Clear()
        if self.m_checkBox2.IsChecked():
            self.m_checkBox2.SetValue(0)
        self.m_textCtrl12.Clear()

    def execute_itp_command(self, cmd, itplib):
        self.steps.execute_itp_command(cmd, itplib)

    def execute_host_command(self, cmd, timeout, nocheck):
        self.steps.execute_host_command(cmd, timeout, nocheck)

    def on_popmenu_clicked( self, event ):
        if event.Id == self.m_pop_boot_linux.GetId():
            self.steps.boot_to('Linux')
        elif event.Id == self.m_pop_boot_win.GetId():
            self.steps.boot_to('Windows')
        elif event.Id == self.m_pop_boot_vm.GetId():
            self.steps.boot_to('ESXi')
        elif event.Id == self.m_pop_boot_uefi.GetId():
            self.steps.boot_to('UEFI SHELL')
        elif event.Id == self.m_pop_reset_os.GetId():
            self.steps.reset_to('OS')
        elif event.Id == self.m_pop_reset_uefi.GetId():
            self.steps.reset_to('UEFI SHELL')
        elif event.Id == self.m_pop_ac_on.GetId():
            self.steps.ac("On")
        elif event.Id == self.m_pop_ac_off.GetId():
            self.steps.ac("Off")
        elif event.Id == self.m_pop_dc_on.GetId():
            self.steps.dc("On")
        elif event.Id == self.m_pop_dc_off.GetId():
            self.steps.dc("Off")
        elif event.Id == self.m_pop_reset_any.GetId():
            self.steps.reset("ANY")
        elif event.Id == self.m_pop_reset_cold.GetId():
            self.steps.reset("COLD")
        elif event.Id == self.m_pop_reset_warm.GetId():
            self.steps.reset("WARM")
        elif event.Id == self.m_pop_waitfor_os.GetId():
            self.steps.wait_for("OS")
        elif event.Id == self.m_pop_waitfor_uefishell.GetId():
            self.steps.wait_for("UEFI Shell")
        elif event.Id == self.m_pop_waitfor_s0.GetId():
            self.steps.wait_for("S0")
        elif event.Id == self.m_pop_waitfor_s5.GetId():
            self.steps.wait_for("S5")
        elif event.Id == self.m_pop_checkenvironment_os.GetId():
            self.steps.check_envirnment("OS")
        elif event.Id == self.m_pop_checkenvironment_uefishell.GetId():
            self.steps.check_envirnment("UEFI Shell")
        elif event.Id == self.m_pop_checkpowerstate_s0.GetId():
            self.steps.check_power("S0")
        elif event.Id == self.m_pop_checkpowerstate_s5.GetId():
            self.steps.check_power("S5")
        elif event.Id == self.m_pop_checkpowerstate_g3.GetId():
            self.steps.check_power("G3")

    # Click tool -> download Show Window
    def click_download(self, event):
        if self.tool_download_window is None:
            self.tool_download_window = DownloadWindow(self)
        self.tool_download_window.ShowModal()
        event.Skip()

    # Click tool -> upload Show Window
    def click_upload(self, event):
        if self.tool_upload_window is None is None:
            self.tool_upload_window = UploadWindow(self)
        self.tool_upload_window.ShowModal()
        event.Skip()

    def click_tool_menuitem(self, event):
        mitem = event.EventObject.FindItemById(event.Id)
        pkg = mitem.GetItemLabel()
        self.toolmenu.install_tool_to_sut(pkg)
        event.Skip()

    # Click Execute Host Command Button Show Window
    def on_high_level_list_host(self):
        if self.host_cmd_window is None:
            self.host_cmd_window = CommandDialogHost(self)
        self.host_cmd_window.ShowModal()

    # Click Set Feature Button Show Window
    def on_high_level_list_action(self):
        if self.set_feature_window is None:
            self.set_feature_window = CommandDialog(self)
        self.set_feature_window.ShowModal()

    # Click Execute ITP Command Button Show Window
    def on_high_level_list_ITP(self):
        if self.itp_cmd_window is None:
            self.itp_cmd_window = CommandDialogITP(self)
        self.itp_cmd_window.ShowModal()

    # Click Run TCD Block Button Show
    def on_high_level_list_TCD(self):
        if self.tcd_block_window is None:
            self.tcd_block_window = RunTCDBlock(self)
        self.tcd_block_window.ShowModal()

    # Click Wait Button Show
    def on_high_level_list_wait(self):
        if self.wait_window is None:
            self.wait_window = WaitWindow(self)
        self.wait_window.ShowModal()

    def on_high_level_clear_cmos(self):
        self.steps.hlclearcmos()

    def on_high_level_list_click(self, event):
        ctrlbox = event.EventObject
        if ctrlbox.Selection < 2:
            self._prepare_popmenu(ctrlbox.StringSelection)
            poppt = wx.Point(ctrlbox.Position.x, ctrlbox.Parent.Position.y + ctrlbox.Position.y) + wx.Point(ctrlbox.Size.x, ctrlbox.Selection * ctrlbox.Size.y / ctrlbox.CountPerPage)
            super().PopupMenu(self.m_popmenu, poppt)
        # Set Feature Button
        elif ctrlbox.Selection == 2:
            self.on_high_level_list_action()
        # Run TCD Block Button
        elif ctrlbox.Selection == 3:
            self.on_high_level_list_TCD()
        # Execute ITP Command Button
        elif ctrlbox.Selection == 4:
            self.on_high_level_list_ITP()
        # Execute Host Command Button
        elif ctrlbox.Selection == 5:
            self.on_high_level_list_host()
        # Wait Button
        elif ctrlbox.Selection == 6:
            self.on_high_level_list_wait()
        # clear CMOS
        elif ctrlbox.Selection == 7:
            self.on_high_level_clear_cmos()
        ctrlbox.Select(-1)
        super().on_high_level_list_click(event)

    def on_lower_level_list_click( self, event ):
        ctrlbox = event.EventObject
        self._prepare_popmenu(ctrlbox.StringSelection)
        poppt = wx.Point(ctrlbox.Position.x, ctrlbox.Parent.Position.y + ctrlbox.Position.y) + wx.Point(ctrlbox.Size.x, ctrlbox.Selection * ctrlbox.Size.y / ctrlbox.CountPerPage)
        super().PopupMenu(self.m_popmenu, poppt)
        ctrlbox.Select(-1)
        super().on_lower_level_list_click(event)

    def toggle_power_monitor(self, event):
        self.monitor.toggle_power_state(self.m_textCtrl23)
        return super().toggle_power_monitor(event)

    def toggle_postcode_monitor(self, event):
        self.monitor.toggle_post_code(self.m_textCtrl24)
        return super().toggle_postcode_monitor(event)


#Set Feature Button
class CommandDialog(SetFeature):
    def __init__(self, parent):
        super().__init__(parent)
        self.feature_name()

    def feature_name( self ):
        mapping_table = MappingTableParser('pvl.xlsx')
        feature_table = mapping_table.feature_table
        names = set()
        for k, v in feature_table.keys():
            names.add(k)

        features = list(names)
        self.m_choice3.SetItems(features)
        self.m_choice3.Select(0)
        self.set_feature_status(features[0])

    def set_feature_status(self, feature):
        mapping_table = MappingTableParser('pvl.xlsx')
        feature_table = mapping_table.feature_table
        options = set()
        for k, v in feature_table.keys():
            if k != feature:
                continue
            options.add(v)
        self.m_choice4.SetItems(list(options))
        self.m_choice4.Select(0)

    def feature_status( self, event ):
        feature_name = self.m_choice3.GetStringSelection()
        self.set_feature_status(feature_name)
        event.Skip()

    def on_add_feature_clicked(self, event):
        feature = self.m_choice3.GetStringSelection()
        status = self.m_choice4.GetStringSelection()
        if len(self.m_textCtrl13.GetValue().strip()) == 0:
            self.m_textCtrl13.AppendText(f'{feature}={status}')
        else:
            self.m_textCtrl13.AppendText(f'\n{feature}={status}')
        old = self.m_textCtrl13.GetValue().split()
        new = []
        for x in old:
            if x not in new:
                new.append(x)
        self.m_textCtrl13.Clear()
        for i in new:
            self.m_textCtrl13.AppendText(f'{i}\n')
        return super().on_add_feature_clicked(event)

    def on_remove_selected( self, event ):
        begin, end = self.m_textCtrl13.GetSelection()
        value = self.m_textCtrl13.GetValue().replace('\n', '\n\n')

        selectlinestart = value.rfind('\n\n', 0, begin)
        selectlinestart = 0 if selectlinestart == -1 else selectlinestart + 2
        selectlinestop = value.find('\n\n', end)
        selectlinestop = len(value) if selectlinestop == -1 else selectlinestop + 2

        dvalue = value[0:selectlinestart] + value[selectlinestop:]
        self.m_textCtrl13.SetValue(dvalue.replace('\n\n', '\n'))
        self.m_textCtrl13.SetSelection(begin, begin)
        self.m_textCtrl13.SetFocus()

        return super().on_remove_selected(event)

    def on_apply_clicked(self, event):
        features = self.m_textCtrl13.GetValue()
        if len(features.strip()) > 0:
            _parent = self.GetParent()
            assert(isinstance(_parent, MainFrame))
            features = features.replace('\n', ', ')
            _parent.steps.set_feature(features)
        self.Hide()
        return super().on_apply_clicked(event)


#Execute ITP Command Button
class CommandDialogITP(ExecuteITPCommand):
    def __init__(self, parent):
        super().__init__(parent)
        self.m_choice5.Select(-1)

    def on_variable_select(self, event):
        self.m_textCtrl15.WriteText(' {' + event.EventObject.StringSelection + '} ')
        event.EventObject.Select(-1)
        return super().on_variable_select(event)

    def on_cancel_clicked( self, event ):
        self.Hide()
        return super().on_cancel_clicked(event)

    def on_execute_clicked( self, event ):
        if len(self.m_textCtrl15.GetValue().strip()) > 0:
            itplib = 'pythonsv' if self.m_choice4.GetSelection() == 0 else 'cscripts'
            self.Parent.execute_itp_command(self.m_textCtrl15.GetValue(), itplib)
            self.m_textCtrl15.Clear()
        self.Hide()
        return super().on_execute_clicked(event)


#Execute Host Command Button
class CommandDialogHost(ExcuteHostCommand):
    def __init__(self, parent):
        super().__init__(parent)
        self.m_choice5.Select(-1)

    def on_variable_select(self, event):
        self.m_textCtrl12.WriteText(' {' + event.EventObject.StringSelection + '} ')
        event.EventObject.Select(-1)
        return super().on_variable_select(event)

    def on_cancel_clicked( self, event ):
        self.Hide()
        return super().on_cancel_clicked(event)

    def on_execute_clicked( self, event ):
        if len(self.m_textCtrl12.GetValue().strip()) > 0:
            self.Parent.execute_host_command(self.m_textCtrl12.GetValue(), int(self.m_textCtrl11.GetValue()) if self.m_checkBox1.IsChecked() else None, not self.m_checkBox2.IsChecked())
            if self.m_checkBox1.IsChecked():
                self.m_textCtrl11.Clear()
                self.m_checkBox1.SetValue(0)
            if self.m_checkBox2.IsChecked():
                self.m_checkBox2.SetValue(0)
            self.m_textCtrl12.Clear()
        self.Hide()
        return super().on_execute_clicked(event)


#Run TCD Block Button Show Window
class RunTCDBlock(RunTCDBlock):
    def __init__(self, parent):
        super().__init__(parent)
        self.load_tcd_names()

    def load_tcd_names(self):
        testtcd = get_tcdb_file_path('test_tcdb')
        if not os.path.isfile(testtcd):
            return

        tcdfolder = os.path.dirname(testtcd)
        tcds = ['.'.join(f.split('.')[0:-1]) for f in os.listdir(tcdfolder)]
        self.m_comboBox1.SetItems(tcds)


    def on_cancel_clicked(self, event):
        self.Hide()
        return super().on_cancel_clicked(event)

    def on_execute_clicked( self, event ):
        _parent = self.GetParent()
        assert(isinstance(_parent, MainFrame))
        tcdname = self.m_comboBox1.GetValue()
        tcdfile = get_tcdb_file_path(tcdname)
        if tcdfile is not None:
            _parent.steps.run_tcd_block(tcdname, int(self.m_textCtrl13.GetValue()))
        self.Hide()
        return super().on_execute_clicked(event)


#Wait Button Show Window
class WaitWindow(Wait):
    def __init__(self, parent):
        super().__init__(parent)

    def execute_wait( self, event ):
        _parent = self.GetParent()
        assert(isinstance(_parent, MainFrame))
        sec = int(self.m_textCtrl14.GetValue())
        if sec > 0:
            _parent.steps.hlwait(sec)
        self.Hide()
        super().execute_wait(event)


#Help -> about  Show Window
class AboutWindow(About):
    def __init__(self, parent):
        super().__init__(parent)

    def click_about_ok( self, event ):
        self.Hide()
        return super().click_about_ok(event)


#Click tool download show window
class DownloadWindow(ToolDownload):
    def __init__(self, parent):
        super().__init__(parent)

    def tool_download( self, event ):
        rfilepath = self.m_textCtrl15.GetValue().strip()
        target = self.m_textCtrl17.GetValue().strip()
        if len(rfilepath) and len(target) > 0:
             VlToolMenu().download(rfilepath, target)
        else:
            c_dialog = wx.MessageDialog(None, "Path cannot be empty", 'Error message',
                                        wx.YES_DEFAULT | wx.ICON_QUESTION)
            if c_dialog.ShowModal() == wx.ID_YES:
                c_dialog.Destroy()
        return super().tool_download(event)

    def tool_download_import( self, event ):
        dlg = wx.DirDialog(self, "Download File:", r'C:\Users\Administrator\Downloads', wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST)
        if dlg.ShowModal() == wx.ID_OK:
            try:
                self.m_textCtrl17.SetValue(dlg.GetPath())
            except:
                c_dialog = wx.MessageDialog(None, "Please enter a correct folder address", 'Error message', wx.YES_DEFAULT | wx.ICON_QUESTION)
                if c_dialog.ShowModal() == wx.ID_YES:
                    c_dialog.Destroy()
        return super().tool_download_import(event)

#Click tool upload show window
class UploadWindow(ToolUpload):
    def __init__(self, parent):
        super().__init__(parent)

    def tool_upload(self, event):
        rfilepath = self.m_textCtrl18.GetValue().strip()
        target = self.m_textCtrl16.GetValue().strip()
        if len(rfilepath) and len(target) > 0:
             VlToolMenu().upload(rfilepath, target)
        else:
            c_dialog = wx.MessageDialog(None, "Path cannot be empty", 'Error message',
                                        wx.YES_DEFAULT | wx.ICON_QUESTION)
            if c_dialog.ShowModal() == wx.ID_YES:
                c_dialog.Destroy()
        return super().tool_upload(event)

    def tool_upload_import( self, event ):
        dlg = wx.FileDialog(self, "Upload File:", '', "", "ALL (*.*)|*.*", style=wx.FD_OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            i = dlg.GetFilterIndex()
            if i == 0:
                try:
                    self.m_textCtrl18.SetValue(dlg.GetPath())
                except:
                    c_dialog = wx.MessageDialog(None, "Please enter a correct file address", 'Error message',
                                                wx.YES_DEFAULT | wx.ICON_QUESTION)
                    if c_dialog.ShowModal() == wx.ID_YES:
                        c_dialog.Destroy()
        return super().tool_upload_import(event)