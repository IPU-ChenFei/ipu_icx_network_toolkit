#!/usr/bin/env python
#################################################################################
# INTEL CONFIDENTIAL
# Copyright Intel Corporation All Rights Reserved.
#
# The source code contained or described herein and all documents related to
# the source code ("Material") are owned by Intel Corporation or its suppliers
# or licensors. Title to the Material remains with Intel Corporation or its
# suppliers and licensors. The Material may contain trade secrets and proprietary
# and confidential information of Intel Corporation and its suppliers and
# licensors, and is protected by worldwide copyright and trade secret laws and
# treaty provisions. No part of the Material may be used, copied, reproduced,
# modified, published, uploaded, posted, transmitted, distributed, or disclosed
# in any way without Intel's prior express written permission.
#
# No license under any patent, copyright, trade secret or other intellectual
# property right is granted to or conferred upon you by disclosure or delivery
# of the Materials, either expressly, by implication, inducement, estoppel or
# otherwise. Any license under such intellectual property rights must be express
# and approved by Intel in writing.
#################################################################################
"""Provides a GUI interface to request SDSi licenses through the SDSi API.

    Typical usage example:
        This module is currently meant to be run as a script.
        When script is executed, a GUI application will be launched and can be used to request licenses.
        API key, PPINs and feature bundles can be specified via GUI.
        API key can be saved as an environment variable sdsi_api_key to be loaded automatically.
"""
import os
import threading
import tkinter as tk

from src.sdsi.lib.license.sdsi_license_names import FeatureNames
from src.sdsi.lib.license.sdsi_license_request_tool import SDSiLicenseTool


class _SDSiLicenseGUI:
    """
    License requesting GUI tool to interface with SDSi License API.
    Glasgow_ID :    77513
    Phoenix_ID :    22014767375
    """

    def __init__(self) -> None:
        """Initialize the GUI, constructing GUI components and load API key (if provided)."""
        # Define GUI options
        self.product_id_options = [name.value for name in FeatureNames]
        self.hw_ids, self.product_ids, self.api_key = [], [], os.getenv('sdsi_api_key', '')

        # Create GUI Root
        self.root = tk.Tk()
        self.root.title('SDSi License API GUI')
        self.root.resizable(False, False)

        # Define API widgets
        self.api_key_label, self.api_key_field_string, self.api_key_field = None, None, None
        self.hw_id_label, self.hw_id_field, self.hw_id_field_string, self.add_hw_id_button = None, None, None, None
        self.product_id_label, self.product_id_field, self.add_product_id_button = None, None, None
        self.submit_button, self.clear_button = None, None
        self._update_widgets()

        # Run GUI
        self.root.mainloop()

    def _update_widgets(self) -> None:
        """Update the GUI widgets to reflect the current internal state of the class."""
        # Delete all widgets so you can recreate them
        [widget.destroy() for widget in self.root.winfo_children()]

        # Create GUI widgets
        cur_row = 0
        # API key widgets
        self.api_key_label = tk.Label(self.root, text="API Key: ")
        self.api_key_field_string = tk.StringVar(value=self.api_key)
        self.api_key_field = tk.Entry(self.root, textvariable=self.api_key_field_string)
        self.api_key_label.grid(row=cur_row, column=0, pady=(10, 10))
        self.api_key_field.grid(row=cur_row, column=1, pady=(10, 10))
        cur_row += 1
        self.hw_id_label = tk.Label(self.root, text="PPINS: ")
        self.hw_id_field_string = tk.StringVar(value='')
        self.hw_id_field = tk.Entry(self.root, textvariable=self.hw_id_field_string)
        self.add_hw_id_button = tk.Button(self.root, text="ADD", command=self._add_hw_id)
        self.hw_id_label.grid(row=cur_row, column=0, pady=(10, 10))
        self.hw_id_field.grid(row=cur_row, column=1, pady=(10, 10))
        self.add_hw_id_button.grid(row=cur_row, column=2, pady=(10, 10), padx=(10, 10))
        cur_row += 1
        # Dynamic HWID widget list
        for hw_id in self.hw_ids:
            hw_id_label = tk.Label(self.root, text=hw_id)
            hw_id_label.grid(row=cur_row, column=1)
            cur_row += 1
        self.product_id_label = tk.Label(self.root, text="Products: ")
        self.product_id_field = tk.Listbox(self.root, selectmode="multiple")
        for each_item in range(len(self.product_id_options)):
            self.product_id_field.insert(tk.END, self.product_id_options[each_item])
            self.product_id_field.itemconfig(each_item, bg="cyan")
        self.add_product_id_button = tk.Button(self.root, text="ADD", command=self._add_product_id)
        self.product_id_label.grid(row=cur_row, column=0, pady=(10, 10))
        self.product_id_field.grid(row=cur_row, column=1, pady=(10, 10))
        self.add_product_id_button.grid(row=cur_row, column=2, pady=(10, 10), padx=(10, 10))
        cur_row += 1
        # Dynamic product ID widget list
        for product_id in self.product_ids:
            product_id_label = tk.Label(self.root, text=product_id)
            product_id_label.grid(row=cur_row, column=1)
            cur_row += 1
        # Submit and clear button widgets
        self.submit_button = tk.Button(self.root, text="Request", command=self._make_request)
        self.submit_button.grid(row=cur_row, column=0, sticky='E', pady=(10, 10))
        self.clear_button = tk.Button(self.root, text="Clear", command=self._clear_widgets)
        self.clear_button.grid(row=cur_row, column=1, sticky='E', pady=(10, 10))
        # Set window Size
        longest_product = 0
        for product_list in self.product_ids:
            longest_product = max(longest_product, len(product_list))
        self.root.geometry(f"{240 + 30 * longest_product}x{300 + (cur_row * 20)}")

    def _make_request(self) -> None:
        """Make a request using the SDSi API Tool using the fields in the GUI."""
        # Check GUI values to ensure valid request
        self.api_key = self.api_key_field_string.get()
        api_key, hw_ids, product_ids = self.api_key, self.hw_ids, self.product_ids
        if not api_key or not hw_ids or not product_ids:
            print("Ignoring Request. Empty Fields.")
            return

        # Send request, use a thread for the API Tool to ensure GUI does not freeze during request.
        print("Sending request to API Tool.")
        print(f"HWIDs: {hw_ids}")
        print(f"Products: {product_ids}")
        self._clear_widgets()
        api_tool = SDSiLicenseTool(api_key)
        api_tool_thread = threading.Thread(target=api_tool.create_license_set, args=(hw_ids, product_ids))
        api_tool_thread.start()

    def _add_hw_id(self) -> None:
        """Add the given PPIN from the user to the request."""
        self.api_key = self.api_key_field_string.get()
        hw_id = self.hw_id_field.get()
        if not hw_id: return
        self.hw_ids.append(hw_id)
        self._update_widgets()
        print(f"HW ID Added: {hw_id}")

    def _add_product_id(self) -> None:
        """Add the given product from the user to the request."""
        self.api_key = self.api_key_field_string.get()
        selected_products = [self.product_id_field.get(i) for i in self.product_id_field.curselection()]
        if not selected_products: return
        self.product_ids.append(selected_products)
        self._update_widgets()
        print(f"Product Added: {selected_products}")

    def _clear_widgets(self) -> None:
        """Clear GUI and all request information except api key."""
        self.api_key = self.api_key_field_string.get()
        self.hw_ids = []
        self.product_ids = []
        self._update_widgets()

if __name__ == "__main__":
    gui = _SDSiLicenseGUI()
