from os import name
import dearpygui.dearpygui as dpg
import datetime
from netmiko import ConnectHandler

class config():
    def __init__(self):
        self.device = {
            'device_type': 'cisco_ios',
            'ip': lambda: dpg.get_value("ip_input"),
            'username': lambda: dpg.get_value("username_input"),
            'password': lambda: dpg.get_value("password_input"),
            'secret': lambda: dpg.get_value("secret_input"),
        }
        
        self.selected_file = None

    def ssh(self):
        global net_connect

        evaluated_device = {
            key: value() if callable(value) else value
            for key, value in self.device.items()
        }

        print(evaluated_device)
        net_connect = ConnectHandler(**evaluated_device)
        net_connect.enable()

    def get_running_config(self, sender, app_data):
        self.ssh()

        ip_func = lambda: dpg.get_value("ip_input")
        time = datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S")

        ip = ip_func()
        name = f"{ip} running {time}"
        print(name)

        running_config = net_connect.send_command("show running-config")
        save_config = open(f"{name}.txt", "w")
        save_config.write(str(running_config))
        save_config.close()

        current_output = dpg.get_value("command output")
        updated_output = f"{current_output}\n\n{running_config}"
        dpg.set_value("command output", updated_output)

        dpg.set_value("config_download", f"Config file {ip}-running.txt downloaded to desktop")

        net_connect.disconnect()

    def send_config(self, sender, app_data):
        if not self.selected_file:
            dpg.set_value("output_current", "No file selected!")
            return

        self.ssh()

        with open(self.selected_file, "r") as config_file:
            command_output = net_connect.send_config_from_file(config_file.name)

        current_output = dpg.get_value("command output")
        updated_output = f"{current_output}\n\n{command_output}"
        dpg.set_value("command output", updated_output)

        dpg.set_value("output_current", f"Configuration from {self.selected_file} sent successfully!")

        net_connect.disconnect()

    def set_selected_file(self, sender, app_data):
        self.selected_file = app_data['file_path_name']
        dpg.set_value("output_current", f"Selected file: {self.selected_file}")


def router_settings():
    router_config = config()

    with dpg.file_dialog(label="Open File", directory_selector=False, show=False, tag="file_dialog_id", height=600, width=600, callback=router_config.set_selected_file):
        dpg.add_file_extension(".txt")

    with dpg.window(label="Config", height=760, width=785, no_collapse=True, no_move=True, no_scrollbar=True, no_scroll_with_mouse=True, no_resize=True):
        dpg.add_text("Router Config GUI", color=(255, 255, 255), tag="title")
        dpg.add_separator()
        with dpg.group(horizontal=True):
            dpg.add_input_text(label="IP", default_value='192.168.10.1', tag="ip_input", width=100)
            dpg.add_input_text(label="Username", default_value='admin', tag="username_input", width=100)
        with dpg.group(horizontal=True):
            dpg.add_input_text(label="Password", default_value='abcd1234', tag="password_input", width=100)
            dpg.add_input_text(label="Secret", default_value='abcd1234', tag="secret_input", width=100)

        dpg.add_separator()
        with dpg.group(horizontal=True, ):
            dpg.add_button(label="Get running config file", callback=router_config.get_running_config)
            dpg.add_text(tag="config_download", default_value="Not downloaded")
        with dpg.group(horizontal=True):
            dpg.add_button(label="file selector", callback=lambda: dpg.show_item("file_dialog_id"))
            dpg.add_text(tag=("output_current"), default_value="select file")
        with dpg.group(horizontal=True):
            dpg.add_button(label="Send config file", callback=router_config.send_config)

        output_child_window = dpg.generate_uuid()
        with dpg.group(horizontal=True, pos=(0, 260)):
            with dpg.child_window(tag=output_child_window, height=500, width=785):
                dpg.add_text(tag="command output", default_value="Command output", user_data=output_child_window)
                    

if __name__ == '__main__':
    dpg.create_context()
    dpg.create_viewport(title='router GUI', width=800, height=800)

    router_settings()

    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()
