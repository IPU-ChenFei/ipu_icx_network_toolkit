# -*- coding: utf-8 -*-

###########################################################################
## Python code generated with wxFormBuilder (version 3.10.1-0-g8feb16b3)
## http://www.wxformbuilder.org/
##
## PLEASE DO *NOT* EDIT THIS FILE!
###########################################################################

import wx
import wx.xrc

setting_sut = 1000
setting_feature = 1001
setting_debug = 1002
setting_tool = 1003
setting_dtafconfig = 1004
bootto_linux = 1005
bootto_win = 1006
bootto_vm = 1007
bootto_uefi = 1008
reset_os = 1009
reset_uefo = 1010
ac_on = 1011
ac_off = 1012
dc_on = 1013
dc_off = 1014
reset_any = 1015
reset_cold = 1016
reset_warm = 1017
waitfor_os = 1018
waitfor_uefi = 1019
waitfor_s0 = 1020
waitfor_s5 = 1021
checkenvironment_os = 1022
checkenvironment_uefi = 1023
checkpowerstate_s0 = 1024
checkpowerstate_s5 = 1025
checkpowerstate_g3 = 1026
bios_log = 1027
dryrun_log = 1028
steps_log = 1029

###########################################################################
## Class mainfrm
###########################################################################

class mainfrm ( wx.Frame ):

    def __init__( self, parent ):
        wx.Frame.__init__ ( self, parent, id = wx.ID_ANY, title = u"Platform Level Validation Language", pos = wx.DefaultPosition, size = wx.Size( 1174,715 ), style = wx.DEFAULT_FRAME_STYLE|wx.TAB_TRAVERSAL )

        self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )
        self.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_WINDOW ) )

        self.m_menubar1 = wx.MenuBar( 0 )
        self.m_setting = wx.Menu()
        self.m_setting_sut = wx.MenuItem( self.m_setting, setting_sut, u"SUT", wx.EmptyString, wx.ITEM_NORMAL )
        self.m_setting.Append( self.m_setting_sut )

        self.m_setting_feature = wx.MenuItem( self.m_setting, setting_feature, u"Feature", wx.EmptyString, wx.ITEM_NORMAL )
        self.m_setting.Append( self.m_setting_feature )

        self.m_setting_debug = wx.MenuItem( self.m_setting, setting_debug, u"Debug", wx.EmptyString, wx.ITEM_NORMAL )
        self.m_setting.Append( self.m_setting_debug )

        self.m_setting_tool = wx.MenuItem( self.m_setting, setting_tool, u"Tool", wx.EmptyString, wx.ITEM_NORMAL )
        self.m_setting.Append( self.m_setting_tool )

        self.m_setting_dtafconfig = wx.MenuItem( self.m_setting, setting_dtafconfig, u"Dtaf Config", wx.EmptyString, wx.ITEM_NORMAL )
        self.m_setting.Append( self.m_setting_dtafconfig )

        self.m_menubar1.Append( self.m_setting, u"Setting     " )

        self.m_tool = wx.Menu()
        self.m_menu1 = wx.Menu()
        self.m_menuItem31 = wx.MenuItem( self.m_menu1, wx.ID_ANY, u"Download", wx.EmptyString, wx.ITEM_NORMAL )
        self.m_menu1.Append( self.m_menuItem31 )

        self.m_menuItem33 = wx.MenuItem( self.m_menu1, wx.ID_ANY, u"Upload", wx.EmptyString, wx.ITEM_NORMAL )
        self.m_menu1.Append( self.m_menuItem33 )

        self.m_tool.AppendSubMenu( self.m_menu1, u"File transfer" )

        self.m_menu3 = wx.Menu()
        self.m_tool.AppendSubMenu( self.m_menu3, u"Domain tools" )

        self.m_menubar1.Append( self.m_tool, u"Tool     " )

        self.m_help = wx.Menu()
        self.m_help_hlswiki = wx.MenuItem( self.m_help, wx.ID_ANY, u"HLS Wiki", wx.EmptyString, wx.ITEM_NORMAL )
        self.m_help.Append( self.m_help_hlswiki )

        self.m_help_toolkitwiki = wx.MenuItem( self.m_help, wx.ID_ANY, u"Toolkit Wiki", wx.EmptyString, wx.ITEM_NORMAL )
        self.m_help.Append( self.m_help_toolkitwiki )

        self.m_help_about = wx.MenuItem( self.m_help, wx.ID_ANY, u"About", wx.EmptyString, wx.ITEM_NORMAL )
        self.m_help.Append( self.m_help_about )

        self.m_menubar1.Append( self.m_help, u"Help     " )

        self.SetMenuBar( self.m_menubar1 )

        self.m_popmenu = wx.Menu()
        self.m_pop_boot_linux = wx.MenuItem( self.m_popmenu, bootto_linux, u"Linux", wx.EmptyString, wx.ITEM_NORMAL )
        self.m_popmenu.Append( self.m_pop_boot_linux )

        self.m_pop_boot_win = wx.MenuItem( self.m_popmenu, bootto_win, u"Windows", wx.EmptyString, wx.ITEM_NORMAL )
        self.m_popmenu.Append( self.m_pop_boot_win )

        self.m_pop_boot_vm = wx.MenuItem( self.m_popmenu, bootto_vm, u"VMWare", wx.EmptyString, wx.ITEM_NORMAL )
        self.m_popmenu.Append( self.m_pop_boot_vm )

        self.m_pop_boot_uefi = wx.MenuItem( self.m_popmenu, bootto_uefi, u"UEFI SHELL", wx.EmptyString, wx.ITEM_NORMAL )
        self.m_popmenu.Append( self.m_pop_boot_uefi )

        self.m_pop_reset_os = wx.MenuItem( self.m_popmenu, reset_os, u"OS", wx.EmptyString, wx.ITEM_NORMAL )
        self.m_popmenu.Append( self.m_pop_reset_os )

        self.m_pop_reset_uefi = wx.MenuItem( self.m_popmenu, reset_uefo, u"UEFI SHELL", wx.EmptyString, wx.ITEM_NORMAL )
        self.m_popmenu.Append( self.m_pop_reset_uefi )

        self.m_pop_ac_on = wx.MenuItem( self.m_popmenu, ac_on, u"ON", wx.EmptyString, wx.ITEM_NORMAL )
        self.m_popmenu.Append( self.m_pop_ac_on )

        self.m_pop_ac_off = wx.MenuItem( self.m_popmenu, ac_off, u"OFF", wx.EmptyString, wx.ITEM_NORMAL )
        self.m_popmenu.Append( self.m_pop_ac_off )

        self.m_pop_dc_on = wx.MenuItem( self.m_popmenu, dc_on, u"ON", wx.EmptyString, wx.ITEM_NORMAL )
        self.m_popmenu.Append( self.m_pop_dc_on )

        self.m_pop_dc_off = wx.MenuItem( self.m_popmenu, dc_off, u"OFF", wx.EmptyString, wx.ITEM_NORMAL )
        self.m_popmenu.Append( self.m_pop_dc_off )

        self.m_pop_reset_any = wx.MenuItem( self.m_popmenu, reset_any, u"ANY", wx.EmptyString, wx.ITEM_NORMAL )
        self.m_popmenu.Append( self.m_pop_reset_any )

        self.m_pop_reset_cold = wx.MenuItem( self.m_popmenu, reset_cold, u"COLD", wx.EmptyString, wx.ITEM_NORMAL )
        self.m_popmenu.Append( self.m_pop_reset_cold )

        self.m_pop_reset_warm = wx.MenuItem( self.m_popmenu, reset_warm, u"WARM", wx.EmptyString, wx.ITEM_NORMAL )
        self.m_popmenu.Append( self.m_pop_reset_warm )

        self.m_pop_waitfor_os = wx.MenuItem( self.m_popmenu, waitfor_os, u"OS", wx.EmptyString, wx.ITEM_NORMAL )
        self.m_popmenu.Append( self.m_pop_waitfor_os )

        self.m_pop_waitfor_uefishell = wx.MenuItem( self.m_popmenu, waitfor_uefi, u"UEFI SHELL", wx.EmptyString, wx.ITEM_NORMAL )
        self.m_popmenu.Append( self.m_pop_waitfor_uefishell )

        self.m_pop_waitfor_s0 = wx.MenuItem( self.m_popmenu, waitfor_s0, u"S0", wx.EmptyString, wx.ITEM_NORMAL )
        self.m_popmenu.Append( self.m_pop_waitfor_s0 )

        self.m_pop_waitfor_s5 = wx.MenuItem( self.m_popmenu, waitfor_s5, u"S5", wx.EmptyString, wx.ITEM_NORMAL )
        self.m_popmenu.Append( self.m_pop_waitfor_s5 )

        self.m_pop_checkenvironment_os = wx.MenuItem( self.m_popmenu, checkenvironment_os, u"OS", wx.EmptyString, wx.ITEM_NORMAL )
        self.m_popmenu.Append( self.m_pop_checkenvironment_os )

        self.m_pop_checkenvironment_uefishell = wx.MenuItem( self.m_popmenu, checkenvironment_uefi, u"UEFI SHELL", wx.EmptyString, wx.ITEM_NORMAL )
        self.m_popmenu.Append( self.m_pop_checkenvironment_uefishell )

        self.m_pop_checkpowerstate_s0 = wx.MenuItem( self.m_popmenu, checkpowerstate_s0, u"S0", wx.EmptyString, wx.ITEM_NORMAL )
        self.m_popmenu.Append( self.m_pop_checkpowerstate_s0 )

        self.m_pop_checkpowerstate_s5 = wx.MenuItem( self.m_popmenu, checkpowerstate_s5, u"S5", wx.EmptyString, wx.ITEM_NORMAL )
        self.m_popmenu.Append( self.m_pop_checkpowerstate_s5 )

        self.m_pop_checkpowerstate_g3 = wx.MenuItem( self.m_popmenu, checkpowerstate_g3, u"G3", wx.EmptyString, wx.ITEM_NORMAL )
        self.m_popmenu.Append( self.m_pop_checkpowerstate_g3 )

        self.m_right_bios_start = wx.MenuItem( self.m_popmenu, wx.ID_ANY, u"Start BIOS Log", wx.EmptyString, wx.ITEM_NORMAL )
        self.m_popmenu.Append( self.m_right_bios_start )

        self.m_right_bios_stop = wx.MenuItem( self.m_popmenu, wx.ID_ANY, u"Stop BIOS Log", wx.EmptyString, wx.ITEM_NORMAL )
        self.m_popmenu.Append( self.m_right_bios_stop )

        self.m_right_click_cut = wx.MenuItem( self.m_popmenu, wx.ID_ANY, u"Cut", wx.EmptyString, wx.ITEM_NORMAL )
        self.m_popmenu.Append( self.m_right_click_cut )

        self.m_right_click_copy = wx.MenuItem( self.m_popmenu, wx.ID_ANY, u"Copy", wx.EmptyString, wx.ITEM_NORMAL )
        self.m_popmenu.Append( self.m_right_click_copy )

        self.m_right_click_paste = wx.MenuItem( self.m_popmenu, wx.ID_ANY, u"Paste", wx.EmptyString, wx.ITEM_NORMAL )
        self.m_popmenu.Append( self.m_right_click_paste )

        self.m_right_click_clear = wx.MenuItem( self.m_popmenu, wx.ID_ANY, u"Clear", wx.EmptyString, wx.ITEM_NORMAL )
        self.m_popmenu.Append( self.m_right_click_clear )

        self.m_right_steps_export = wx.MenuItem( self.m_popmenu, wx.ID_ANY, u"Export ...", wx.EmptyString, wx.ITEM_NORMAL )
        self.m_popmenu.Append( self.m_right_steps_export )

        self.m_right_steps_execute = wx.MenuItem( self.m_popmenu, wx.ID_ANY, u"Execute", wx.EmptyString, wx.ITEM_NORMAL )
        self.m_popmenu.Append( self.m_right_steps_execute )

        self.m_right_steps_import = wx.MenuItem( self.m_popmenu, wx.ID_ANY, u"Import ...", wx.EmptyString, wx.ITEM_NORMAL )
        self.m_popmenu.Append( self.m_right_steps_import )


        bSizer5 = wx.BoxSizer( wx.HORIZONTAL )

        bSizer53 = wx.BoxSizer( wx.VERTICAL )

        sbSizer10 = wx.StaticBoxSizer( wx.StaticBox( self, wx.ID_ANY, wx.EmptyString ), wx.VERTICAL )

        sbSizer6 = wx.StaticBoxSizer( wx.StaticBox( sbSizer10.GetStaticBox(), wx.ID_ANY, u"High Level Steps" ), wx.VERTICAL )

        m_listBox3Choices = [ u"Boot To", u"Reset To", u"Set Feature", u"Run TCD Block", u"Execute ITP Command", u"Execute Host Command", u"Wait", u"Clear CMOS" ]
        self.m_listBox3 = wx.ListBox( sbSizer6.GetStaticBox(), wx.ID_ANY, wx.Point( -1,-1 ), wx.Size( 200,-1 ), m_listBox3Choices, 0 )
        self.m_listBox3.SetFont( wx.Font( 10, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, "Calibri" ) )
        self.m_listBox3.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_INACTIVECAPTION ) )

        sbSizer6.Add( self.m_listBox3, 1, wx.ALL|wx.EXPAND, 5 )


        sbSizer10.Add( sbSizer6, 1, wx.EXPAND, 5 )


        bSizer53.Add( sbSizer10, 1, wx.EXPAND, 5 )

        sbSizer3 = wx.StaticBoxSizer( wx.StaticBox( self, wx.ID_ANY, u"Low Level Steps" ), wx.VERTICAL )

        m_listBox2Choices = [ u"AC", u"DC", u"Reset", u"Wait For", u"Check Environment", u"Check Power State" ]
        self.m_listBox2 = wx.ListBox( sbSizer3.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.Size( 200,-1 ), m_listBox2Choices, 0 )
        self.m_listBox2.SetFont( wx.Font( 10, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, "Calibri" ) )
        self.m_listBox2.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_INFOBK ) )

        sbSizer3.Add( self.m_listBox2, 1, wx.ALL|wx.EXPAND, 5 )


        bSizer53.Add( sbSizer3, 1, wx.EXPAND, 5 )


        bSizer5.Add( bSizer53, 0, wx.EXPAND, 5 )

        bSizer64 = wx.BoxSizer( wx.VERTICAL )

        sbSizer16 = wx.StaticBoxSizer( wx.StaticBox( self, wx.ID_ANY, wx.EmptyString ), wx.VERTICAL )

        sbSizer19 = wx.StaticBoxSizer( wx.StaticBox( sbSizer16.GetStaticBox(), wx.ID_ANY, u"Execute Command" ), wx.VERTICAL )

        bSizer66 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_checkBox1 = wx.CheckBox( sbSizer19.GetStaticBox(), wx.ID_ANY, u"Timeout (/s)", wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer66.Add( self.m_checkBox1, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )

        self.m_textCtrl11 = wx.TextCtrl( sbSizer19.GetStaticBox(), wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( 70,-1 ), 0 )
        bSizer66.Add( self.m_textCtrl11, 0, wx.ALL, 5 )

        self.m_checkBox2 = wx.CheckBox( sbSizer19.GetStaticBox(), wx.ID_ANY, u"Assert Retval=0", wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer66.Add( self.m_checkBox2, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )


        bSizer66.Add( ( 0, 0), 1, wx.EXPAND, 5 )

        self.m_staticText36 = wx.StaticText( sbSizer19.GetStaticBox(), wx.ID_ANY, u"Insert Variable", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText36.Wrap( -1 )

        bSizer66.Add( self.m_staticText36, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )

        m_choice5Choices = [ u"sutos.bkc_root_path", u"hostos.bkc_root_path", u"bmc.ipaddr", u"bmc.username", u"bmc.password" ]
        self.m_choice5 = wx.Choice( sbSizer19.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, m_choice5Choices, 0 )
        self.m_choice5.SetSelection( 0 )
        bSizer66.Add( self.m_choice5, 0, wx.ALL, 5 )


        sbSizer19.Add( bSizer66, 0, wx.EXPAND, 5 )

        bSizer65 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticText57 = wx.StaticText( sbSizer19.GetStaticBox(), wx.ID_ANY, u"Command Line  ", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText57.Wrap( -1 )

        self.m_staticText57.SetFont( wx.Font( 10, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, "Calibri" ) )
        self.m_staticText57.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_WINDOW ) )

        bSizer65.Add( self.m_staticText57, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )

        self.m_textCtrl12 = wx.TextCtrl( sbSizer19.GetStaticBox(), wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_textCtrl12.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_WINDOW ) )

        bSizer65.Add( self.m_textCtrl12, 1, wx.ALL, 5 )

        self.m_button19 = wx.Button( sbSizer19.GetStaticBox(), wx.ID_ANY, u"Execute", wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer65.Add( self.m_button19, 0, wx.ALL, 5 )


        sbSizer19.Add( bSizer65, 0, wx.EXPAND, 5 )


        sbSizer16.Add( sbSizer19, 0, wx.EXPAND, 5 )

        sbSizer20 = wx.StaticBoxSizer( wx.StaticBox( sbSizer16.GetStaticBox(), wx.ID_ANY, u"Bios Log" ), wx.VERTICAL )

        self.m_textCtrl1 = wx.TextCtrl( sbSizer20.GetStaticBox(), bios_log, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.TE_MULTILINE )
        self.m_textCtrl1.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_WINDOW ) )

        sbSizer20.Add( self.m_textCtrl1, 1, wx.ALL|wx.EXPAND, 5 )


        sbSizer16.Add( sbSizer20, 1, wx.EXPAND, 5 )


        bSizer64.Add( sbSizer16, 1, wx.EXPAND, 5 )

        sbSizer18 = wx.StaticBoxSizer( wx.StaticBox( self, wx.ID_ANY, u"DryRun Log" ), wx.VERTICAL )

        self.m_textCtrl2 = wx.TextCtrl( sbSizer18.GetStaticBox(), dryrun_log, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.TE_MULTILINE )
        self.m_textCtrl2.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_HIGHLIGHTTEXT ) )

        sbSizer18.Add( self.m_textCtrl2, 1, wx.ALL|wx.EXPAND, 5 )


        bSizer64.Add( sbSizer18, 1, wx.EXPAND, 5 )


        bSizer5.Add( bSizer64, 1, wx.EXPAND, 5 )

        bSizer55 = wx.BoxSizer( wx.VERTICAL )

        sbSizer11 = wx.StaticBoxSizer( wx.StaticBox( self, wx.ID_ANY, wx.EmptyString ), wx.VERTICAL )

        sbSizer4 = wx.StaticBoxSizer( wx.StaticBox( sbSizer11.GetStaticBox(), wx.ID_ANY, u"Steps" ), wx.VERTICAL )

        self.m_textCtrl3 = wx.TextCtrl( sbSizer4.GetStaticBox(), steps_log, wx.EmptyString, wx.DefaultPosition, wx.Size( 250,-1 ), wx.TE_MULTILINE )
        self.m_textCtrl3.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_HIGHLIGHTTEXT ) )

        sbSizer4.Add( self.m_textCtrl3, 1, wx.ALL|wx.EXPAND, 5 )


        sbSizer11.Add( sbSizer4, 1, wx.EXPAND, 5 )


        bSizer55.Add( sbSizer11, 1, wx.EXPAND, 5 )

        sbSizer1 = wx.StaticBoxSizer( wx.StaticBox( self, wx.ID_ANY, u"System Monitor" ), wx.VERTICAL )

        bSizer39 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticText52 = wx.StaticText( sbSizer1.GetStaticBox(), wx.ID_ANY, u"Power State", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText52.Wrap( -1 )

        bSizer39.Add( self.m_staticText52, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )

        self.m_textCtrl23 = wx.TextCtrl( sbSizer1.GetStaticBox(), wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( 100,-1 ), wx.TE_READONLY )
        bSizer39.Add( self.m_textCtrl23, 0, wx.ALL, 5 )

        self.m_button46 = wx.Button( sbSizer1.GetStaticBox(), wx.ID_ANY, u"Start/Stop", wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer39.Add( self.m_button46, 0, wx.ALL, 5 )


        sbSizer1.Add( bSizer39, 0, wx.EXPAND, 5 )

        bSizer40 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticText53 = wx.StaticText( sbSizer1.GetStaticBox(), wx.ID_ANY, u"Post Code   ", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText53.Wrap( -1 )

        bSizer40.Add( self.m_staticText53, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )

        self.m_textCtrl24 = wx.TextCtrl( sbSizer1.GetStaticBox(), wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( 100,-1 ), wx.TE_READONLY )
        bSizer40.Add( self.m_textCtrl24, 0, wx.ALL, 5 )

        self.m_button47 = wx.Button( sbSizer1.GetStaticBox(), wx.ID_ANY, u"Start/Stop", wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer40.Add( self.m_button47, 0, wx.ALL, 5 )


        sbSizer1.Add( bSizer40, 0, 0, 5 )


        bSizer55.Add( sbSizer1, 1, wx.EXPAND, 5 )


        bSizer5.Add( bSizer55, 0, wx.EXPAND, 5 )


        self.SetSizer( bSizer5 )
        self.Layout()

        self.Centre( wx.BOTH )

        # Connect Events
        self.Bind( wx.EVT_CLOSE, self.onclose )
        self.Bind( wx.EVT_MENU, self.on_setting_menu, id = self.m_setting_sut.GetId() )
        self.Bind( wx.EVT_MENU, self.on_setting_menu, id = self.m_setting_feature.GetId() )
        self.Bind( wx.EVT_MENU, self.on_setting_menu, id = self.m_setting_debug.GetId() )
        self.Bind( wx.EVT_MENU, self.on_setting_menu, id = self.m_setting_tool.GetId() )
        self.Bind( wx.EVT_MENU, self.on_setting_menu, id = self.m_setting_dtafconfig.GetId() )
        self.Bind( wx.EVT_MENU, self.click_download, id = self.m_menuItem31.GetId() )
        self.Bind( wx.EVT_MENU, self.click_upload, id = self.m_menuItem33.GetId() )
        self.Bind( wx.EVT_MENU, self.hls_wiki, id = self.m_help_hlswiki.GetId() )
        self.Bind( wx.EVT_MENU, self.toolkit_wiki, id = self.m_help_toolkitwiki.GetId() )
        self.Bind( wx.EVT_MENU, self.about, id = self.m_help_about.GetId() )
        self.Bind( wx.EVT_MENU, self.on_popmenu_clicked, id = self.m_pop_boot_linux.GetId() )
        self.Bind( wx.EVT_MENU, self.on_popmenu_clicked, id = self.m_pop_boot_win.GetId() )
        self.Bind( wx.EVT_MENU, self.on_popmenu_clicked, id = self.m_pop_boot_vm.GetId() )
        self.Bind( wx.EVT_MENU, self.on_popmenu_clicked, id = self.m_pop_boot_uefi.GetId() )
        self.Bind( wx.EVT_MENU, self.on_popmenu_clicked, id = self.m_pop_reset_os.GetId() )
        self.Bind( wx.EVT_MENU, self.on_popmenu_clicked, id = self.m_pop_reset_uefi.GetId() )
        self.Bind( wx.EVT_MENU, self.on_popmenu_clicked, id = self.m_pop_ac_on.GetId() )
        self.Bind( wx.EVT_MENU, self.on_popmenu_clicked, id = self.m_pop_ac_off.GetId() )
        self.Bind( wx.EVT_MENU, self.on_popmenu_clicked, id = self.m_pop_dc_on.GetId() )
        self.Bind( wx.EVT_MENU, self.on_popmenu_clicked, id = self.m_pop_dc_off.GetId() )
        self.Bind( wx.EVT_MENU, self.on_popmenu_clicked, id = self.m_pop_reset_any.GetId() )
        self.Bind( wx.EVT_MENU, self.on_popmenu_clicked, id = self.m_pop_reset_cold.GetId() )
        self.Bind( wx.EVT_MENU, self.on_popmenu_clicked, id = self.m_pop_reset_warm.GetId() )
        self.Bind( wx.EVT_MENU, self.on_popmenu_clicked, id = self.m_pop_waitfor_os.GetId() )
        self.Bind( wx.EVT_MENU, self.on_popmenu_clicked, id = self.m_pop_waitfor_uefishell.GetId() )
        self.Bind( wx.EVT_MENU, self.on_popmenu_clicked, id = self.m_pop_waitfor_s0.GetId() )
        self.Bind( wx.EVT_MENU, self.on_popmenu_clicked, id = self.m_pop_waitfor_s5.GetId() )
        self.Bind( wx.EVT_MENU, self.on_popmenu_clicked, id = self.m_pop_checkenvironment_os.GetId() )
        self.Bind( wx.EVT_MENU, self.on_popmenu_clicked, id = self.m_pop_checkenvironment_uefishell.GetId() )
        self.Bind( wx.EVT_MENU, self.on_popmenu_clicked, id = self.m_pop_checkpowerstate_s0.GetId() )
        self.Bind( wx.EVT_MENU, self.on_popmenu_clicked, id = self.m_pop_checkpowerstate_s5.GetId() )
        self.Bind( wx.EVT_MENU, self.on_popmenu_clicked, id = self.m_pop_checkpowerstate_g3.GetId() )
        self.Bind( wx.EVT_MENU, self.on_bios_start, id = self.m_right_bios_start.GetId() )
        self.Bind( wx.EVT_MENU, self.on_bios_stop, id = self.m_right_bios_stop.GetId() )
        self.Bind( wx.EVT_MENU, self.on_cut, id = self.m_right_click_cut.GetId() )
        self.Bind( wx.EVT_MENU, self.on_copy, id = self.m_right_click_copy.GetId() )
        self.Bind( wx.EVT_MENU, self.on_paste, id = self.m_right_click_paste.GetId() )
        self.Bind( wx.EVT_MENU, self.on_clear, id = self.m_right_click_clear.GetId() )
        self.Bind( wx.EVT_MENU, self.on_steps_export, id = self.m_right_steps_export.GetId() )
        self.Bind( wx.EVT_MENU, self.on_steps_execute, id = self.m_right_steps_execute.GetId() )
        self.Bind( wx.EVT_MENU, self.on_steps_import, id = self.m_right_steps_import.GetId() )
        self.m_listBox3.Bind( wx.EVT_LISTBOX, self.on_high_level_list_click )
        self.m_listBox2.Bind( wx.EVT_LISTBOX, self.on_lower_level_list_click )
        self.m_choice5.Bind( wx.EVT_CHOICE, self.on_variable_select )
        self.m_button19.Bind( wx.EVT_BUTTON, self.execute_add_step )
        self.m_textCtrl1.Bind( wx.EVT_RIGHT_UP, self.click_right_bioslog )
        self.m_textCtrl2.Bind( wx.EVT_RIGHT_UP, self.click_right_dryrunlog )
        self.m_textCtrl3.Bind( wx.EVT_RIGHT_UP, self.click_right_stepslog )
        self.m_button46.Bind( wx.EVT_BUTTON, self.toggle_power_monitor )
        self.m_button47.Bind( wx.EVT_BUTTON, self.toggle_postcode_monitor )

    def __del__( self ):
        pass


    # Virtual event handlers, override them in your derived class
    def onclose( self, event ):
        event.Skip()

    def on_setting_menu( self, event ):
        event.Skip()





    def click_download( self, event ):
        event.Skip()

    def click_upload( self, event ):
        event.Skip()

    def hls_wiki( self, event ):
        event.Skip()

    def toolkit_wiki( self, event ):
        event.Skip()

    def about( self, event ):
        event.Skip()

    def on_popmenu_clicked( self, event ):
        event.Skip()






















    def on_bios_start( self, event ):
        event.Skip()

    def on_bios_stop( self, event ):
        event.Skip()

    def on_cut( self, event ):
        event.Skip()

    def on_copy( self, event ):
        event.Skip()

    def on_paste( self, event ):
        event.Skip()

    def on_clear( self, event ):
        event.Skip()

    def on_steps_export( self, event ):
        event.Skip()

    def on_steps_execute( self, event ):
        event.Skip()

    def on_steps_import( self, event ):
        event.Skip()

    def on_high_level_list_click( self, event ):
        event.Skip()

    def on_lower_level_list_click( self, event ):
        event.Skip()

    def on_variable_select( self, event ):
        event.Skip()

    def execute_add_step( self, event ):
        event.Skip()

    def click_right_bioslog( self, event ):
        event.Skip()

    def click_right_dryrunlog( self, event ):
        event.Skip()

    def click_right_stepslog( self, event ):
        event.Skip()

    def toggle_power_monitor( self, event ):
        event.Skip()

    def toggle_postcode_monitor( self, event ):
        event.Skip()


###########################################################################
## Class SetFeature
###########################################################################

class SetFeature ( wx.Dialog ):

    def __init__( self, parent ):
        wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = u"Set Feature", pos = wx.DefaultPosition, size = wx.Size( 600,364 ), style = wx.DEFAULT_DIALOG_STYLE )

        self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )

        bSizer14 = wx.BoxSizer( wx.VERTICAL )

        bSizer14.SetMinSize( wx.Size( 600,-1 ) )
        bSizer17 = wx.BoxSizer( wx.HORIZONTAL )

        gSizer4 = wx.GridSizer( 2, 3, 0, 0 )

        self.m_staticText24 = wx.StaticText( self, wx.ID_ANY, u"Feature Name", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText24.Wrap( -1 )

        gSizer4.Add( self.m_staticText24, 0, wx.ALL|wx.ALIGN_BOTTOM, 5 )

        self.m_staticText25 = wx.StaticText( self, wx.ID_ANY, u"Feature Value", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText25.Wrap( -1 )

        gSizer4.Add( self.m_staticText25, 0, wx.ALL|wx.ALIGN_BOTTOM, 5 )

        self.m_staticText35 = wx.StaticText( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText35.Wrap( -1 )

        gSizer4.Add( self.m_staticText35, 0, wx.ALL, 5 )

        m_choice3Choices = []
        self.m_choice3 = wx.Choice( self, wx.ID_ANY, wx.DefaultPosition, wx.Size( 150,-1 ), m_choice3Choices, 0 )
        self.m_choice3.SetSelection( 0 )
        gSizer4.Add( self.m_choice3, 0, wx.ALL, 5 )

        m_choice4Choices = []
        self.m_choice4 = wx.Choice( self, wx.ID_ANY, wx.DefaultPosition, wx.Size( 150,-1 ), m_choice4Choices, 0 )
        self.m_choice4.SetSelection( 0 )
        gSizer4.Add( self.m_choice4, 0, wx.ALL, 5 )

        self.m_button8 = wx.Button( self, wx.ID_ANY, u"+", wx.DefaultPosition, wx.Size( 50,-1 ), 0 )
        gSizer4.Add( self.m_button8, 0, wx.ALL, 5 )


        bSizer17.Add( gSizer4, 1, wx.EXPAND, 5 )


        bSizer14.Add( bSizer17, 0, wx.EXPAND, 5 )

        bSizer15 = wx.BoxSizer( wx.HORIZONTAL )

        gSizer5 = wx.GridSizer( 1, 1, 0, 0 )

        self.m_textCtrl13 = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( 550,200 ), wx.TE_MULTILINE )
        gSizer5.Add( self.m_textCtrl13, 1, wx.ALL|wx.EXPAND, 5 )


        bSizer15.Add( gSizer5, 1, wx.EXPAND, 5 )


        bSizer14.Add( bSizer15, 1, wx.EXPAND, 5 )

        bSizer37 = wx.BoxSizer( wx.HORIZONTAL )


        bSizer37.Add( ( 0, 0), 1, wx.EXPAND, 5 )

        self.m_button11 = wx.Button( self, wx.ID_ANY, u"Remove Selected", wx.DefaultPosition, wx.Size( 100,30 ), 0 )
        bSizer37.Add( self.m_button11, 0, wx.ALL, 5 )

        self.m_button12 = wx.Button( self, wx.ID_ANY, u"Apply", wx.DefaultPosition, wx.Size( 100,30 ), 0 )
        bSizer37.Add( self.m_button12, 0, wx.ALL, 5 )


        bSizer14.Add( bSizer37, 1, wx.EXPAND, 5 )


        self.SetSizer( bSizer14 )
        self.Layout()

        self.Centre( wx.BOTH )

        # Connect Events
        self.m_choice3.Bind( wx.EVT_CHOICE, self.feature_status )
        self.m_button8.Bind( wx.EVT_BUTTON, self.on_add_feature_clicked )
        self.m_button11.Bind( wx.EVT_BUTTON, self.on_remove_selected )
        self.m_button12.Bind( wx.EVT_BUTTON, self.on_apply_clicked )

    def __del__( self ):
        pass


    # Virtual event handlers, override them in your derived class
    def feature_status( self, event ):
        event.Skip()

    def on_add_feature_clicked( self, event ):
        event.Skip()

    def on_remove_selected( self, event ):
        event.Skip()

    def on_apply_clicked( self, event ):
        event.Skip()


###########################################################################
## Class ExecuteITPCommand
###########################################################################

class ExecuteITPCommand ( wx.Dialog ):

    def __init__( self, parent ):
        wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = u"Execute ITP Command", pos = wx.DefaultPosition, size = wx.Size( 462,180 ), style = wx.DEFAULT_DIALOG_STYLE )

        self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )

        bSizer32 = wx.BoxSizer( wx.VERTICAL )

        bSizer33 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticText25 = wx.StaticText( self, wx.ID_ANY, u"ITP Lib             ", wx.DefaultPosition, wx.Size( -1,-1 ), 0 )
        self.m_staticText25.Wrap( -1 )

        bSizer33.Add( self.m_staticText25, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )

        m_choice4Choices = [ u"PythonSV", u"CScript" ]
        self.m_choice4 = wx.Choice( self, wx.ID_ANY, wx.DefaultPosition, wx.Size( -1,-1 ), m_choice4Choices, 0 )
        self.m_choice4.SetSelection( 0 )
        bSizer33.Add( self.m_choice4, 1, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )


        bSizer32.Add( bSizer33, 0, wx.EXPAND, 5 )

        bSizer36 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticText36 = wx.StaticText( self, wx.ID_ANY, u"Insert Variable", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText36.Wrap( -1 )

        bSizer36.Add( self.m_staticText36, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )

        m_choice5Choices = [ u"sutos.bkc_root_path", u"hostos.bkc_root_path", u"bmc.ipaddr", u"bmc.username", u"bmc.password" ]
        self.m_choice5 = wx.Choice( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, m_choice5Choices, 0 )
        self.m_choice5.SetSelection( 0 )
        bSizer36.Add( self.m_choice5, 1, wx.ALL, 5 )


        bSizer32.Add( bSizer36, 0, wx.EXPAND, 5 )

        bSizer35 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticText46 = wx.StaticText( self, wx.ID_ANY, u"Command      ", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText46.Wrap( -1 )

        bSizer35.Add( self.m_staticText46, 0, wx.TOP|wx.RIGHT|wx.LEFT|wx.ALIGN_CENTER_VERTICAL, 5 )

        self.m_textCtrl15 = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( -1,-1 ), 0 )
        bSizer35.Add( self.m_textCtrl15, 1, wx.ALL|wx.EXPAND, 5 )


        bSizer32.Add( bSizer35, 0, wx.EXPAND, 5 )

        bSizer37 = wx.BoxSizer( wx.HORIZONTAL )


        bSizer37.Add( ( 0, 0), 1, wx.EXPAND, 5 )

        self.m_button28 = wx.Button( self, wx.ID_ANY, u"Cancel", wx.DefaultPosition, wx.Size( -1,-1 ), 0 )
        bSizer37.Add( self.m_button28, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )

        self.m_button29 = wx.Button( self, wx.ID_ANY, u"Execute", wx.DefaultPosition, wx.Size( -1,-1 ), 0 )
        bSizer37.Add( self.m_button29, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )


        bSizer32.Add( bSizer37, 0, wx.EXPAND, 5 )


        self.SetSizer( bSizer32 )
        self.Layout()

        self.Centre( wx.BOTH )

        # Connect Events
        self.m_choice5.Bind( wx.EVT_CHOICE, self.on_variable_select )
        self.m_button28.Bind( wx.EVT_BUTTON, self.on_cancel_clicked )
        self.m_button29.Bind( wx.EVT_BUTTON, self.on_execute_clicked )

    def __del__( self ):
        pass


    # Virtual event handlers, override them in your derived class
    def on_variable_select( self, event ):
        event.Skip()

    def on_cancel_clicked( self, event ):
        event.Skip()

    def on_execute_clicked( self, event ):
        event.Skip()


###########################################################################
## Class ExcuteHostCommand
###########################################################################

class ExcuteHostCommand ( wx.Dialog ):

    def __init__( self, parent ):
        wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = u"Excute Host Command", pos = wx.DefaultPosition, size = wx.Size( 520,144 ), style = wx.DEFAULT_DIALOG_STYLE )

        self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )

        bSizer19 = wx.BoxSizer( wx.VERTICAL )

        bSizer66 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_checkBox1 = wx.CheckBox( self, wx.ID_ANY, u"Timeout (/s)", wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer66.Add( self.m_checkBox1, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )

        self.m_textCtrl11 = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( 70,-1 ), 0 )
        bSizer66.Add( self.m_textCtrl11, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )

        self.m_checkBox2 = wx.CheckBox( self, wx.ID_ANY, u"Assert Retval=0", wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer66.Add( self.m_checkBox2, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )


        bSizer66.Add( ( 0, 0), 1, wx.EXPAND, 5 )

        self.m_staticText36 = wx.StaticText( self, wx.ID_ANY, u"Insert Variable", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText36.Wrap( -1 )

        bSizer66.Add( self.m_staticText36, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )

        m_choice5Choices = [ u"sutos.bkc_root_path", u"hostos.bkc_root_path", u"bmc.ipaddr", u"bmc.username", u"bmc.password" ]
        self.m_choice5 = wx.Choice( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, m_choice5Choices, 0 )
        self.m_choice5.SetSelection( 0 )
        bSizer66.Add( self.m_choice5, 0, wx.ALL, 5 )


        bSizer19.Add( bSizer66, 0, wx.EXPAND, 5 )

        bSizer65 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticText44 = wx.StaticText( self, wx.ID_ANY, u"Command Line ", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText44.Wrap( -1 )

        bSizer65.Add( self.m_staticText44, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )

        self.m_textCtrl12 = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_textCtrl12.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_WINDOW ) )

        bSizer65.Add( self.m_textCtrl12, 1, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )


        bSizer19.Add( bSizer65, 0, wx.EXPAND, 5 )

        bSizer40 = wx.BoxSizer( wx.HORIZONTAL )


        bSizer40.Add( ( 0, 0), 1, wx.EXPAND, 5 )

        self.m_button28 = wx.Button( self, wx.ID_ANY, u"Cancel", wx.DefaultPosition, wx.Size( -1,-1 ), 0 )
        bSizer40.Add( self.m_button28, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL, 5 )

        self.m_button17 = wx.Button( self, wx.ID_ANY, u"Execute", wx.DefaultPosition, wx.Size( -1,-1 ), 0 )
        bSizer40.Add( self.m_button17, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL, 5 )


        bSizer19.Add( bSizer40, 0, wx.EXPAND, 5 )


        self.SetSizer( bSizer19 )
        self.Layout()

        self.Centre( wx.BOTH )

        # Connect Events
        self.m_choice5.Bind( wx.EVT_CHOICE, self.on_variable_select )
        self.m_button28.Bind( wx.EVT_BUTTON, self.on_cancel_clicked )
        self.m_button17.Bind( wx.EVT_BUTTON, self.on_execute_clicked )

    def __del__( self ):
        pass


    # Virtual event handlers, override them in your derived class
    def on_variable_select( self, event ):
        event.Skip()

    def on_cancel_clicked( self, event ):
        event.Skip()

    def on_execute_clicked( self, event ):
        event.Skip()


###########################################################################
## Class RunTCDBlock
###########################################################################

class RunTCDBlock ( wx.Dialog ):

    def __init__( self, parent ):
        wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = u"Run TCD Block", pos = wx.DefaultPosition, size = wx.Size( 273,142 ), style = wx.DEFAULT_DIALOG_STYLE )

        self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )

        bSizer28 = wx.BoxSizer( wx.VERTICAL )

        bSizer40 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticText43 = wx.StaticText( self, wx.ID_ANY, u"Block File         ", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText43.Wrap( -1 )

        bSizer40.Add( self.m_staticText43, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 5 )

        m_comboBox1Choices = [ u" " ]
        self.m_comboBox1 = wx.ComboBox( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( -1,-1 ), m_comboBox1Choices, 0 )
        bSizer40.Add( self.m_comboBox1, 1, wx.ALL|wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL, 5 )


        bSizer28.Add( bSizer40, 0, wx.EXPAND, 5 )

        bSizer42 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticText44 = wx.StaticText( self, wx.ID_ANY, u"Repeat              ", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText44.Wrap( -1 )

        bSizer42.Add( self.m_staticText44, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 5 )

        self.m_textCtrl13 = wx.TextCtrl( self, wx.ID_ANY, u"1", wx.DefaultPosition, wx.Size( -1,-1 ), 0 )
        bSizer42.Add( self.m_textCtrl13, 1, wx.ALL|wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL, 5 )


        bSizer28.Add( bSizer42, 0, wx.EXPAND, 5 )

        bSizer39 = wx.BoxSizer( wx.HORIZONTAL )


        bSizer39.Add( ( 0, 0), 1, wx.EXPAND, 5 )

        self.m_button27 = wx.Button( self, wx.ID_ANY, u"Cancel", wx.DefaultPosition, wx.Size( -1,-1 ), 0 )
        bSizer39.Add( self.m_button27, 0, wx.ALL, 5 )

        self.m_button20 = wx.Button( self, wx.ID_ANY, u"Execute", wx.DefaultPosition, wx.Size( -1,-1 ), 0 )
        bSizer39.Add( self.m_button20, 0, wx.ALL, 5 )


        bSizer28.Add( bSizer39, 0, wx.EXPAND, 5 )


        self.SetSizer( bSizer28 )
        self.Layout()

        self.Centre( wx.BOTH )

        # Connect Events
        self.m_button27.Bind( wx.EVT_BUTTON, self.on_cancel_clicked )
        self.m_button20.Bind( wx.EVT_BUTTON, self.on_execute_clicked )

    def __del__( self ):
        pass


    # Virtual event handlers, override them in your derived class
    def on_cancel_clicked( self, event ):
        event.Skip()

    def on_execute_clicked( self, event ):
        event.Skip()


###########################################################################
## Class Wait
###########################################################################

class Wait ( wx.Dialog ):

    def __init__( self, parent ):
        wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = u"Wait", pos = wx.DefaultPosition, size = wx.Size( 194,112 ), style = wx.DEFAULT_DIALOG_STYLE )

        self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )

        bSizer29 = wx.BoxSizer( wx.VERTICAL )

        bSizer45 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticText45 = wx.StaticText( self, wx.ID_ANY, u"Second", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText45.Wrap( -1 )

        bSizer45.Add( self.m_staticText45, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )

        self.m_textCtrl14 = wx.TextCtrl( self, wx.ID_ANY, u"30", wx.DefaultPosition, wx.Size( -1,-1 ), 0 )
        self.m_textCtrl14.SetFont( wx.Font( 11, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, "Arial" ) )

        bSizer45.Add( self.m_textCtrl14, 1, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )


        bSizer29.Add( bSizer45, 0, 0, 5 )

        bSizer47 = wx.BoxSizer( wx.HORIZONTAL )


        bSizer47.Add( ( 0, 0), 1, wx.EXPAND, 5 )

        self.m_button22 = wx.Button( self, wx.ID_ANY, u"Execute", wx.DefaultPosition, wx.Size( -1,-1 ), 0 )
        bSizer47.Add( self.m_button22, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )


        bSizer29.Add( bSizer47, 0, wx.EXPAND, 5 )


        self.SetSizer( bSizer29 )
        self.Layout()

        self.Centre( wx.BOTH )

        # Connect Events
        self.m_button22.Bind( wx.EVT_BUTTON, self.execute_wait )

    def __del__( self ):
        pass


    # Virtual event handlers, override them in your derived class
    def execute_wait( self, event ):
        event.Skip()


###########################################################################
## Class About
###########################################################################

class About ( wx.Dialog ):

    def __init__( self, parent ):
        wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = u"About Me", pos = wx.DefaultPosition, size = wx.Size( 263,147 ), style = wx.DEFAULT_DIALOG_STYLE )

        self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )

        bSizer31 = wx.BoxSizer( wx.VERTICAL )

        sbSizer10 = wx.StaticBoxSizer( wx.StaticBox( self, wx.ID_ANY, u"PLVL" ), wx.VERTICAL )

        bSizer48 = wx.BoxSizer( wx.VERTICAL )

        self.m_staticText46 = wx.StaticText( sbSizer10.GetStaticBox(), wx.ID_ANY, u"Developed by PAIV SH PV Team", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText46.Wrap( -1 )

        bSizer48.Add( self.m_staticText46, 0, wx.ALL, 5 )


        sbSizer10.Add( bSizer48, 0, wx.EXPAND, 5 )

        bSizer49 = wx.BoxSizer( wx.VERTICAL )

        self.m_staticText47 = wx.StaticText( sbSizer10.GetStaticBox(), wx.ID_ANY, u"Used for HLS Steps Dryrun", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText47.Wrap( -1 )

        bSizer49.Add( self.m_staticText47, 0, wx.ALL, 5 )


        sbSizer10.Add( bSizer49, 0, wx.EXPAND, 5 )

        bSizer50 = wx.BoxSizer( wx.VERTICAL )

        self.m_button22 = wx.Button( sbSizer10.GetStaticBox(), wx.ID_ANY, u"OK", wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer50.Add( self.m_button22, 0, wx.ALL|wx.ALIGN_RIGHT, 5 )


        sbSizer10.Add( bSizer50, 0, wx.EXPAND, 5 )


        bSizer31.Add( sbSizer10, 1, wx.EXPAND, 5 )


        self.SetSizer( bSizer31 )
        self.Layout()

        self.Centre( wx.BOTH )

        # Connect Events
        self.m_button22.Bind( wx.EVT_LEFT_UP, self.click_about_ok )

    def __del__( self ):
        pass


    # Virtual event handlers, override them in your derived class
    def click_about_ok( self, event ):
        event.Skip()


###########################################################################
## Class ToolDownload
###########################################################################

class ToolDownload ( wx.Dialog ):

    def __init__( self, parent ):
        wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = u"Download: from sutos to host", pos = wx.DefaultPosition, size = wx.Size( 381,147 ), style = wx.DEFAULT_DIALOG_STYLE )

        self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )

        bSizer32 = wx.BoxSizer( wx.VERTICAL )

        bSizer36 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticText29 = wx.StaticText( self, wx.ID_ANY, u"Sut Path   ", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText29.Wrap( -1 )

        bSizer36.Add( self.m_staticText29, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )

        self.m_textCtrl15 = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( -1,-1 ), 0 )
        bSizer36.Add( self.m_textCtrl15, 1, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )


        bSizer32.Add( bSizer36, 0, wx.EXPAND, 5 )

        bSizer41 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticText37 = wx.StaticText( self, wx.ID_ANY, u"Host Path", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText37.Wrap( -1 )

        bSizer41.Add( self.m_staticText37, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )

        self.m_textCtrl17 = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( -1,-1 ), 0 )
        bSizer41.Add( self.m_textCtrl17, 1, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )

        self.m_button26 = wx.Button( self, wx.ID_ANY, u" ... ", wx.DefaultPosition, wx.Size( 30,-1 ), 0 )
        bSizer41.Add( self.m_button26, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )


        bSizer32.Add( bSizer41, 0, wx.EXPAND, 5 )

        bSizer51 = wx.BoxSizer( wx.VERTICAL )

        self.m_button22 = wx.Button( self, wx.ID_ANY, u"Download", wx.DefaultPosition, wx.Size( -1,-1 ), 0 )
        bSizer51.Add( self.m_button22, 0, wx.ALIGN_RIGHT|wx.ALL, 5 )


        bSizer32.Add( bSizer51, 0, wx.EXPAND, 5 )


        self.SetSizer( bSizer32 )
        self.Layout()

        self.Centre( wx.BOTH )

        # Connect Events
        self.m_button26.Bind( wx.EVT_BUTTON, self.tool_download_import )
        self.m_button22.Bind( wx.EVT_BUTTON, self.tool_download )

    def __del__( self ):
        pass


    # Virtual event handlers, override them in your derived class
    def tool_download_import( self, event ):
        event.Skip()

    def tool_download( self, event ):
        event.Skip()


###########################################################################
## Class ToolUpload
###########################################################################

class ToolUpload ( wx.Dialog ):

    def __init__( self, parent ):
        wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = u"Upload: from host to sutos", pos = wx.DefaultPosition, size = wx.Size( 382,147 ), style = wx.DEFAULT_DIALOG_STYLE )

        self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )

        bSizer39 = wx.BoxSizer( wx.VERTICAL )

        bSizer42 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticText38 = wx.StaticText( self, wx.ID_ANY, u"Host Path   ", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText38.Wrap( -1 )

        bSizer42.Add( self.m_staticText38, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )

        self.m_textCtrl18 = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( -1,-1 ), 0 )
        bSizer42.Add( self.m_textCtrl18, 1, wx.ALIGN_CENTER_VERTICAL|wx.TOP|wx.BOTTOM|wx.RIGHT, 5 )

        self.m_button27 = wx.Button( self, wx.ID_ANY, u" ... ", wx.DefaultPosition, wx.Size( 30,-1 ), 0 )
        bSizer42.Add( self.m_button27, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )


        bSizer39.Add( bSizer42, 0, wx.EXPAND, 5 )

        bSizer40 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticText32 = wx.StaticText( self, wx.ID_ANY, u"Sut Path    ", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText32.Wrap( -1 )

        bSizer40.Add( self.m_staticText32, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )

        self.m_textCtrl16 = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( -1,-1 ), 0 )
        bSizer40.Add( self.m_textCtrl16, 1, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )


        bSizer39.Add( bSizer40, 0, wx.EXPAND, 5 )

        bSizer52 = wx.BoxSizer( wx.VERTICAL )

        self.m_button23 = wx.Button( self, wx.ID_ANY, u"Upload", wx.DefaultPosition, wx.Size( -1,-1 ), 0 )
        bSizer52.Add( self.m_button23, 0, wx.ALL|wx.ALIGN_RIGHT, 5 )


        bSizer39.Add( bSizer52, 0, wx.EXPAND, 5 )


        self.SetSizer( bSizer39 )
        self.Layout()

        self.Centre( wx.BOTH )

        # Connect Events
        self.m_button27.Bind( wx.EVT_BUTTON, self.tool_upload_import )
        self.m_button23.Bind( wx.EVT_BUTTON, self.tool_upload )

    def __del__( self ):
        pass


    # Virtual event handlers, override them in your derived class
    def tool_upload_import( self, event ):
        event.Skip()

    def tool_upload( self, event ):
        event.Skip()


