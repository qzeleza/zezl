# coding=utf-8

from telegram import Update, error
from telegram.ext import CallbackContext

from keenetic import device
from libraries.main import dialog
from setup.menu import Menu
from setup.autosets import ROUTER_MENU, ROUTER_LIST_MENU


class RouterMenu:

    @staticmethod
    def show_router_menu(update: Update, context: CallbackContext) -> int:
        result, message_id = dialog.show_list_core(message_id=-1,
                                                   reply_text=Menu.RouterMenu.Title,
                                                   list_content=[],
                                                   cmd_buttons=Menu.RouterMenu.Items,
                                                   menu_level=ROUTER_MENU,
                                                   back_buttons=[],
                                                   update=update, context=context)
        return result

    @staticmethod
    def show_list_devices(update: Update, context: CallbackContext) -> int:
        # devices = list(device.list_devices_online().keys())
        devices = device.list_devices_online()
        result, message_id = dialog.show_list_core(message_id=-1,
                                                   reply_text=Menu.RouterMenu.DevicesMenu.Title,
                                                   list_content=devices,
                                                   cmd_buttons=[],
                                                   back_buttons=[],
                                                   menu_level=ROUTER_LIST_MENU,
                                                   update=update, context=context)
        return result

    def show_model_info(self, update: Update, context: CallbackContext) -> int:

        text = device.about_model()
        dialog.alert(text=text, update=update, context=context, popup=True)
        try:
            result = self.show_router_menu(update, context)
        except error.BadRequest:
            result = ROUTER_MENU
        return result


router = RouterMenu()
